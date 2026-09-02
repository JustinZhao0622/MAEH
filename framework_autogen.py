"""Benchmark AutoGen's round-robin repair team on the MAEH test set."""

from __future__ import annotations

import argparse
import asyncio
import time
from typing import Any

import framework_common as common


FRAMEWORK = "autogen"

ANALYST_PROMPT = """
你是代码故障分析智能体。阅读特情和原始代码，确定受影响函数、当前返回契约、
需要改变的具体行为以及必须保持不变的行为。不要输出完整代码，给后续工程师
一份简洁、可执行的修复方案。注意区分“完整实体字典”和“当前可用资源列表”。
""".strip()

CODER_PROMPT = """
你是代码修复工程师。根据用户任务和分析智能体的方案修改代码。必须遵守用户
给出的全部约束，只做最小必要修改。仅输出修改后的完整Python代码，不要输出
Markdown、分析或说明。
""".strip()

REVIEWER_PROMPT = """
你是最终代码审查与修复智能体。检查工程师代码是否准确处置特情、保留全部
imports和函数、符合原函数返回契约并且语法正确。直接修正发现的问题。无论
工程师代码是否有问题，最终都只输出一份可直接运行的完整Python代码，不要
输出Markdown、审查意见或其他文本。
""".strip()


def dependency_error() -> RuntimeError:
    return RuntimeError(
        "缺少AutoGen依赖。请安装："
        'pip install "autogen-agentchat" "autogen-ext[openai]"'
    )


async def repair_case(
    model_client: Any,
    emergency: str,
) -> common.RepairResult:
    """Run analyst, coder, and reviewer in a three-turn AutoGen team."""

    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.teams import RoundRobinGroupChat
    except ImportError as error:
        raise dependency_error() from error

    analyst = AssistantAgent(
        "analyst",
        model_client=model_client,
        description="分析特情、定位受影响代码并制定修复方案。",
        system_message=ANALYST_PROMPT,
    )
    coder = AssistantAgent(
        "coder",
        model_client=model_client,
        description="根据分析方案生成完整修复代码。",
        system_message=CODER_PROMPT,
    )
    reviewer = AssistantAgent(
        "reviewer",
        model_client=model_client,
        description="审查并输出最终完整修复代码。",
        system_message=REVIEWER_PROMPT,
    )
    team = RoundRobinGroupChat(
        [analyst, coder, reviewer],
        max_turns=3,
    )
    result = await team.run(task=common.build_repair_task(emergency))

    messages: list[dict[str, Any]] = []
    final_text = ""
    model_calls = 0
    for message in result.messages:
        source = getattr(message, "source", "")
        content = getattr(message, "content", "")
        if source in {"analyst", "coder", "reviewer"}:
            model_calls += 1
        if source == "reviewer" and isinstance(content, str):
            final_text = content
        messages.append(
            {
                "source": source,
                "type": type(message).__name__,
                "content": (
                    content
                    if isinstance(content, (str, int, float, bool, list, dict))
                    or content is None
                    else str(content)
                ),
            }
        )
    if not final_text and result.messages:
        content = getattr(result.messages[-1], "content", "")
        final_text = content if isinstance(content, str) else str(content)

    return common.RepairResult(
        code=common.clean_code(final_text),
        model_calls=model_calls,
        trace={
            "emergency": emergency,
            "stop_reason": result.stop_reason,
            "messages": messages,
        },
    )


async def run_model(
    args: argparse.Namespace,
    model: dict[str, str],
    dataset: list[dict[str, str]],
) -> None:
    """Run one common base model through the AutoGen workflow."""

    try:
        from autogen_ext.models.openai import (
            OpenAIChatCompletionClient,
        )
    except ImportError as error:
        raise dependency_error() from error

    out_dir = common.prepare_output_dir(FRAMEWORK, model["slug"])
    traces: list[dict[str, Any]] = []
    case_times: list[float] = []
    model_calls = 0
    failures = 0

    server = common.make_server(args, model)
    with server:
        model_client = OpenAIChatCompletionClient(
            model=model["slug"],
            base_url=server.base_url,
            api_key="EMPTY",
            temperature=common.TEMPERATURE,
            top_p=common.TOP_P,
            max_tokens=common.MAX_TOKENS,
            seed=common.SEED,
            model_info={
                "vision": False,
                "function_calling": False,
                "json_output": False,
                "family": "unknown",
                "structured_output": False,
            },
        )
        try:
            for index, item in enumerate(dataset, start=1):
                started_at = time.perf_counter()
                try:
                    repaired = await repair_case(
                        model_client,
                        item["emergency"],
                    )
                except Exception as error:
                    failures += 1
                    repaired = common.RepairResult(
                        code="",
                        model_calls=0,
                        trace={
                            "emergency": item["emergency"],
                            "error": common.safe_error(error),
                        },
                    )
                elapsed = time.perf_counter() - started_at
                case_times.append(elapsed)
                model_calls += repaired.model_calls
                traces.append(
                    {
                        "case": index,
                        "time": elapsed,
                        **repaired.trace,
                    }
                )
                common.write_result(out_dir, index, repaired.code)
                common.write_trace(out_dir, traces)
        finally:
            await model_client.close()

    common.finish_benchmark(
        framework=FRAMEWORK,
        model=model,
        out_dir=out_dir,
        case_times=case_times,
        model_calls=model_calls,
        failed=failures,
        startup_time=server.startup_time,
    )


async def async_main() -> None:
    parser = argparse.ArgumentParser(
        description="使用AutoGen对MAEH特情修复进行统一框架评测。",
    )
    common.add_common_arguments(parser, default_port=18101)
    args = parser.parse_args()
    common.validate_common_arguments(args)

    dataset = common.load_dataset(args.limit)
    for model in common.selected_models(args.model):
        await run_model(args, model, dataset)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
