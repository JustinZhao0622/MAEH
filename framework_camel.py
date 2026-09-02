#!/usr/bin/env python3
"""Benchmark a CAMEL role-based repair team on the MAEH test set."""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import framework_common as common
from MAEH import (
    build_function_catalog,
    load_source_functions,
    parse_function_name,
)
from framework_mini_swe_agent import execute_module, semantic_review


FRAMEWORK = "camel"
DEFAULT_PORT = 18104
ANALYST_MAX_TOKENS = 512
CODE_MAX_TOKENS = 4096

ANALYST_PROMPT = """你是CAMEL协作团队中的特情分析专家。
根据特情和函数目录识别唯一一个直接负责该实体初始化的函数，并向代码工程师
传递精确修复方案。不要编写代码，不得扩大事件影响范围。

回复格式：
FUNCTION: 函数名
PLAN: 需要改变的行为，以及必须保持不变的行为

注意：特情中的资源、跑道、站位、路径或舰载机编号指向单个目标实体。计划必须
明确只处理该完整编号，不能删除整个区域、整个资源类型或修改其他实体。
""".strip()

DEVELOPER_PROMPT = """你是CAMEL协作团队中的Python代码工程师。
你会收到特情、分析专家的通信消息和一个原始函数。只修改该函数的函数体，
完成最小必要修复。保持函数名、参数、返回类型和无关实体行为不变。
只输出修改后的完整函数，不要输出imports、Markdown、解释或其他函数。

领域约束：
- 对“当前可用资源列表”，故障资源应按完整resource_id精确排除；不得跳过整个
  zone，也不得给无关资源增加字段。
- 跑道或保障站位故障时，只能精确移除目标编号，或只给目标实体标记非可用。
- 路径故障只改变目标segment_id；舰载机延迟只改变目标飞机的实际到达时间。
""".strip()

REVIEWER_PROMPT = """你是CAMEL协作团队中的代码审查专家。
你会收到特情、原始函数、分析消息和候选代码。检查目标实体是否被正确处置、
无关实体是否保持原状、函数签名和返回契约是否保持不变。你只负责给工程师
结论和反馈，不要重写代码。

候选代码完全正确时只输出：
VERDICT: PASS

候选代码有问题时输出：
VERDICT: REVISE
FEEDBACK: 一段精确、可执行的修复意见

必须逐项检查：
1. 代码是否匹配特情中的完整实体编号，而不是只匹配区域或类型。
2. 对可用资源列表，是否只排除故障resource_id，其他资源是否原样保留。
3. 是否只修改目标跑道、站位、路径或舰载机，未给无关实体增加字段。
4. 不得因为原始函数没有处置特情，就要求候选代码恢复原始错误行为。
""".strip()


def response_text(response: Any) -> str:
    """Read text from CAMEL's single-agent response."""

    messages = getattr(response, "msgs", None)
    if messages:
        content = messages[0].content
    else:
        message = getattr(response, "msg", None)
        content = getattr(message, "content", "")
    if not isinstance(content, str):
        return str(content)
    return content.strip()


def extract_function_source(text: str, function_name: str) -> str:
    """Extract the selected top-level function from a CAMEL response."""

    cleaned = common.clean_code(text)
    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return cleaned
    lines = cleaned.splitlines()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                end_lineno = node.end_lineno or node.lineno
                return "\n".join(lines[node.lineno - 1:end_lineno]).strip()
    return cleaned


def make_backend(
    *,
    model_name: str,
    base_url: str,
    max_tokens: int,
) -> Any:
    """Create CAMEL's OpenAI-compatible backend for local vLLM."""

    from camel.models import ModelFactory
    from camel.types import ModelPlatformType

    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type=model_name,
        url=base_url,
        api_key="EMPTY",
        timeout=common.REQUEST_TIMEOUT,
        max_retries=1,
        model_config_dict={
            "temperature": common.TEMPERATURE,
            "top_p": common.TOP_P,
            "max_tokens": max_tokens,
            "seed": common.SEED,
        },
    )


def repair_case(
    *,
    emergency: str,
    functions: dict[str, str],
    function_catalog: str,
    import_source: str,
    analyst_backend: Any,
    developer_backend: Any,
    reviewer_backend: Any,
) -> common.RepairResult:
    """Run analyst, developer, and reviewer CAMEL agents in sequence."""

    from camel.agents import ChatAgent

    analyst = ChatAgent(
        system_message=ANALYST_PROMPT,
        model=analyst_backend,
        agent_id="maeh-analyst",
    )
    analysis_response = analyst.step(
        f"特情：\n{emergency}\n\n函数目录：\n{function_catalog}"
    )
    analysis = response_text(analysis_response)
    function_name = parse_function_name(analysis, set(functions))
    if function_name is None:
        return common.RepairResult(
            code=import_source,
            model_calls=1,
            trace={
                "emergency": emergency,
                "predicted_function": None,
                "analysis": analysis,
                "candidate": None,
                "final": None,
            },
        )

    original_function = functions[function_name]
    developer = ChatAgent(
        system_message=DEVELOPER_PROMPT,
        model=developer_backend,
        agent_id="maeh-developer",
    )
    developer_response = developer.step(
        f"特情：\n{emergency}\n\n"
        f"分析专家通信消息：\n{analysis}\n\n"
        f"原始函数：\n{original_function}"
    )
    candidate = response_text(developer_response)

    reviewer = ChatAgent(
        system_message=REVIEWER_PROMPT,
        model=reviewer_backend,
        agent_id="maeh-reviewer",
    )
    reviewer_response = reviewer.step(
        f"特情：\n{emergency}\n\n"
        f"原始函数：\n{original_function}\n\n"
        f"分析专家通信消息：\n{analysis}\n\n"
        f"工程师候选代码：\n{candidate}"
    )
    review_feedback = response_text(reviewer_response)
    if re.search(r"(?im)^\s*VERDICT\s*:\s*PASS\s*$", review_feedback):
        final_text = candidate
        calls = 3
    else:
        revision_response = developer.step(
            "审查专家对上一版候选代码的反馈如下。请依据反馈修正，并再次只输出"
            "修改后的完整函数，不要解释。\n\n"
            f"{review_feedback}"
        )
        final_text = response_text(revision_response)
        calls = 4
    function_code = extract_function_source(final_text, function_name)
    module_code = "\n\n".join(
        part for part in (import_source, function_code) if part
    ).strip()

    return common.RepairResult(
        code=module_code,
        model_calls=calls,
        trace={
            "emergency": emergency,
            "predicted_function": function_name,
            "analysis": analysis,
            "candidate": candidate,
            "reviewer_feedback": review_feedback,
            "final": final_text,
        },
    )


def run_model(
    args: argparse.Namespace,
    model: dict[str, str],
    dataset: list[dict[str, str]],
) -> dict[str, Any]:
    """Run one CAMEL experiment and persist outputs and metrics."""

    out_dir = common.prepare_output_dir(FRAMEWORK, model["slug"])
    functions, import_source = load_source_functions(common.SOURCE_FILE)
    function_catalog = build_function_catalog(functions)
    baseline_code = common.SOURCE_FILE.read_text(encoding="utf-8")
    baseline_module = execute_module(
        baseline_code,
        "camel_baseline",
    )
    traces: list[dict[str, Any]] = []
    case_times: list[float] = []
    model_calls = 0

    server = common.make_server(args, model)
    with server:
        analyst_backend = make_backend(
            model_name=model["slug"],
            base_url=server.base_url,
            max_tokens=ANALYST_MAX_TOKENS,
        )
        developer_backend = make_backend(
            model_name=model["slug"],
            base_url=server.base_url,
            max_tokens=CODE_MAX_TOKENS,
        )
        reviewer_backend = make_backend(
            model_name=model["slug"],
            base_url=server.base_url,
            max_tokens=CODE_MAX_TOKENS,
        )

        def run_case(
            index: int,
            item: dict[str, str],
        ) -> tuple[int, float, common.RepairResult, dict[str, Any]]:
            started_at = time.perf_counter()
            try:
                repaired = repair_case(
                    emergency=item["emergency"],
                    functions=functions,
                    function_catalog=function_catalog,
                    import_source=import_source,
                    analyst_backend=analyst_backend,
                    developer_backend=developer_backend,
                    reviewer_backend=reviewer_backend,
                )
            except Exception as error:
                repaired = common.RepairResult(
                    code=import_source,
                    model_calls=0,
                    trace={
                        "emergency": item["emergency"],
                        "error": common.safe_error(error),
                    },
                )
            elapsed = time.perf_counter() - started_at
            review = semantic_review(
                repaired.code,
                item["emergency"],
                baseline_module,
            )
            return index, elapsed, repaired, review

        completed: list[
            tuple[int, float, common.RepairResult, dict[str, Any]]
        ] = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers
        ) as executor:
            futures = [
                executor.submit(run_case, index, item)
                for index, item in enumerate(dataset, start=1)
            ]
            for future in concurrent.futures.as_completed(futures):
                index, elapsed, repaired, review = future.result()
                completed.append((index, elapsed, repaired, review))
                print(
                    f"[CAMEL] {len(completed)}/{len(dataset)} "
                    f"case={index} "
                    f"success={review.get('status') == 'pass'}"
                )

        for index, elapsed, repaired, review in sorted(completed):
            model_calls += repaired.model_calls
            case_times.append(elapsed)
            traces.append(
                {
                    "case": index,
                    "time": elapsed,
                    "success": review.get("status") == "pass",
                    "review": review,
                    **repaired.trace,
                }
            )
            common.write_result(out_dir, index, repaired.code)
        common.write_trace(out_dir, traces)

    passed = sum(trace["success"] for trace in traces)
    cases = len(traces)
    experiment_time = sum(case_times)
    metrics = {
        "framework": "CAMEL",
        "camel_version": __import__("camel").__version__,
        "model": model["name"],
        "model_path": model["path"],
        "run": 1,
        "cases": cases,
        "passed": passed,
        "failed": cases - passed,
        "accuracy": passed / cases if cases else 0.0,
        "model_calls": model_calls,
        "startup_time": server.startup_time,
        "time": experiment_time,
        "average_response_time": (
            experiment_time / cases if cases else 0.0
        ),
        "startup_time_included": False,
        "out_dir": os.fspath(out_dir),
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="使用CAMEL角色协作机制运行MAEH对比实验。"
    )
    common.add_common_arguments(parser, default_port=DEFAULT_PORT)
    parser.add_argument(
        "--workers",
        type=int,
        default=20,
        help="并发运行的CAMEL协作任务数。",
    )
    args = parser.parse_args()
    common.validate_common_arguments(args)
    if args.workers <= 0:
        raise ValueError("--workers必须大于0")
    dataset = common.load_dataset(args.limit)

    for model in common.selected_models(args.model):
        metrics = run_model(args, model, dataset)
        print(
            f"accuracy={metrics['accuracy']:.6f}, "
            f"average_response_time="
            f"{metrics['average_response_time']:.4f}s"
        )


if __name__ == "__main__":
    main()
