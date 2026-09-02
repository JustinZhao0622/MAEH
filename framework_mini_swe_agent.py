#!/usr/bin/env python3
"""Run three-round MAEH repairs with direct local-vLLM generation."""

from __future__ import annotations

import argparse
import ast
import gc
import inspect
import json
import os
import re
import shutil
import time
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence


SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_emergency_test_set.json"
)
SOURCE_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_resource_initialization.py"
)
OUTPUT_DIR = (
    PROJECT_ROOT
    / "framework-results"
    / "mini-swe-agent"
    / "qwen2.5-coder-7b-instruct"
    / "run_1"
)

MODEL_NAME = "Qwen2.5-Coder-7B-Instruct"
MODEL_PATH = "/data/huggingface/Qwen2.5-Coder-7B-Instruct"
MAX_REPAIR_ROUNDS = 3
TEMPERATURE = 0.0
TOP_P = 0.95
MAX_MODEL_TOKENS = 8000
GPU_MEMORY_UTILIZATION = 0.9

SYSTEM_PROMPT = """你是一名代码修复器，专门根据突发事件修改给定的Python资源初始化文件。

硬性规则：
1. 只能输出修改后的完整Python文件内容。
2. 不允许输出Markdown代码块、解释、bash命令或省略号。
3. 必须原样保留全部import语句，不能新增、删除或修改import。
4. 只能修改已有函数的函数体；不能新增或删除函数，不能修改函数名、参数列表或返回值形式。
5. 只处理当前突发事件，不得修改无关实体或引入额外事件。
6. 不允许使用return或pass跳过核心逻辑，不允许硬编码评测输出。
""".strip()

USER_PROMPT_TEMPLATE = """场景：
MAEH舰载机甲板保障资源初始化。

突发事件：
{emergency}

验证语义：
- 验证会执行代码，检查当前突发事件是否被正确处理。
- feedback中的function表示最可能仍需修改的函数。
- 如果feedback包含未解决项，只修复该项，不要影响其他实体。
- 资源、保障站位或跑道不可用时，可以从返回集合移除，也可以保留并明确标记为非可用。
- 路径不可通行时，只应阻断指定路径，不能影响其他路径。
- 舰载机延迟时，目标舰载机的actual_arrival_time必须等于特情给出的预计到达时刻。

当前Python文件：
{code}

{feedback}

请输出修改后的完整Python文件。只输出Python代码本身。
"""

RESOURCE_FUNCTIONS = {
    ("FIX", "POWER"): "initialize_fixed_power_resources",
    ("FIX", "HYDRAULIC"): "initialize_fixed_hydraulic_resources",
    ("FIX", "FUEL"): "initialize_fixed_fuel_resources",
    ("FIX", "OXYGEN"): "initialize_fixed_oxygen_resources",
    ("MOB", "POWER"): "initialize_mobile_power_resources",
    ("MOB", "HYDRAULIC"): "initialize_mobile_hydraulic_resources",
    ("MOB", "FUEL"): "initialize_mobile_fuel_resources",
    ("MOB", "OXYGEN"): "initialize_mobile_oxygen_resources",
}
AVAILABLE_VALUES = {
    "可用",
    "可通行",
    "正常",
    "available",
    "enabled",
    "online",
    "open",
    "normal",
}


@dataclass
class TaskState:
    index: int
    emergency: str
    original_code: str
    current_code: str
    active: bool = True
    feedback: str = ""
    error: str | None = None
    final_review: dict[str, Any] = field(default_factory=dict)
    attempts: list[dict[str, Any]] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0


def load_dataset(limit: int = 0) -> list[dict[str, str]]:
    raw_dataset = json.loads(DATASET_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw_dataset, list):
        raise ValueError("测试集顶层结构必须是列表")

    dataset: list[dict[str, str]] = []
    for index, item in enumerate(raw_dataset, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第{index}条测试数据不是字典")
        emergency = item.get("emergency")
        if not isinstance(emergency, str) or not emergency.strip():
            raise ValueError(f"第{index}条测试数据缺少特情")
        dataset.append({"emergency": emergency.strip()})
    return dataset[:limit] if limit > 0 else dataset


def split_batches(
    items: Sequence[TaskState],
    batch_size: int,
) -> Iterable[Sequence[TaskState]]:
    if batch_size <= 0:
        if items:
            yield items
        return
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def expected_function_for_emergency(emergency: str) -> str:
    fixed_match = re.search(
        r"(FIX)-[A-C]-(POWER|HYDRAULIC|FUEL|OXYGEN)-[0-9]+",
        emergency,
    )
    if fixed_match:
        return RESOURCE_FUNCTIONS[fixed_match.groups()]

    mobile_match = re.search(
        r"(MOB)-(POWER|HYDRAULIC|FUEL|OXYGEN)-[0-9]+",
        emergency,
    )
    if mobile_match:
        return RESOURCE_FUNCTIONS[mobile_match.groups()]
    if re.search(r"MOB-TOW-[0-9]+", emergency):
        return "initialize_tow_tractors"
    if "SEG-" in emergency:
        return "create_route_segment"
    if re.search(r"舰载机AC[0-9]+", emergency):
        return "initialize_aircraft"
    if "起飞跑道" in emergency:
        return "initialize_runways"
    if "保障站位" in emergency:
        return "initialize_support_stands"
    raise ValueError(f"无法确定特情对应函数：{emergency}")


def extract_code(text: str) -> str:
    text = text.strip()
    matches = re.findall(
        r"```(?:python|py)?\s*\n?(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if matches:
        text = max((match.strip() for match in matches), key=len)
    lines = text.splitlines()
    prefixes = ('"""', "'''", "from ", "import ", "def ")
    for index, line in enumerate(lines):
        if line.lstrip().startswith(prefixes):
            text = "\n".join(lines[index:]).strip()
            break
    return text.rstrip() + "\n"


def import_structure(tree: ast.Module) -> list[str]:
    return [
        ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]


def function_structure(tree: ast.Module) -> list[tuple[str, str, str]]:
    functions: list[tuple[str, str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                (
                    type(node).__name__,
                    node.name,
                    ast.dump(node.args, include_attributes=False),
                )
            )
    return functions


def validate_code(candidate: str, original: str) -> str | None:
    try:
        candidate_tree = ast.parse(candidate)
    except SyntaxError as error:
        return f"生成代码存在语法错误：{error}"
    original_tree = ast.parse(original)
    if import_structure(candidate_tree) != import_structure(original_tree):
        return "生成代码修改了import区域，必须原样保留全部import。"
    if function_structure(candidate_tree) != function_structure(original_tree):
        return "生成代码新增、删除了函数，或者修改了函数签名。"
    return None


def is_unavailable(entity: dict[str, Any]) -> bool:
    if entity.get("available") is False:
        return True
    if entity.get("is_available") is False:
        return True
    if entity.get("usable") is False:
        return True
    status = str(entity.get("status", "")).strip().lower()
    return bool(status) and status not in AVAILABLE_VALUES


def collection_by_id(
    value: Any,
    id_field: str,
) -> dict[str, dict[str, Any]]:
    if isinstance(value, dict):
        if not all(isinstance(item, dict) for item in value.values()):
            raise AssertionError("返回字典中的实体格式不正确")
        return value
    if isinstance(value, list):
        if not all(
            isinstance(item, dict) and id_field in item
            for item in value
        ):
            raise AssertionError("返回列表中的实体格式不正确")
        entities = {item[id_field]: item for item in value}
        if len(entities) != len(value):
            raise AssertionError("返回列表中存在重复实体编号")
        return entities
    raise AssertionError("函数返回类型发生变化")


def check_unavailable_collection(
    actual: Any,
    baseline: Any,
    target_id: str,
    id_field: str,
) -> None:
    actual_entities = collection_by_id(actual, id_field)
    baseline_entities = collection_by_id(baseline, id_field)
    extra_ids = set(actual_entities) - set(baseline_entities)
    if extra_ids:
        raise AssertionError(f"新增了无关实体：{sorted(extra_ids)}")
    missing_unrelated = (
        set(baseline_entities) - set(actual_entities) - {target_id}
    )
    if missing_unrelated:
        raise AssertionError(
            f"删除了无关实体：{sorted(missing_unrelated)}"
        )
    if target_id in actual_entities and not is_unavailable(
        actual_entities[target_id]
    ):
        raise AssertionError(f"{target_id}仍然处于可用状态")


def execute_module(code: str, name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    exec(compile(code, name, "exec"), module.__dict__)
    return module


def semantic_review(
    code: str,
    emergency: str,
    baseline_module: types.ModuleType,
) -> dict[str, Any]:
    function_name = expected_function_for_emergency(emergency)
    try:
        candidate_module = execute_module(code, "candidate")
        function = getattr(candidate_module, function_name)
        baseline_function = getattr(baseline_module, function_name)
        if inspect.signature(function) != inspect.signature(
            baseline_function
        ):
            raise AssertionError("目标函数签名发生变化")

        if function_name.startswith("initialize_fixed_"):
            target_id = re.search(
                r"FIX-[A-C]-(?:POWER|HYDRAULIC|FUEL|OXYGEN)-[0-9]+",
                emergency,
            ).group(0)
            check_unavailable_collection(
                function(2),
                baseline_function(2),
                target_id,
                "resource_id",
            )
        elif function_name.startswith("initialize_mobile_"):
            target_id = re.search(
                r"MOB-(?:POWER|HYDRAULIC|FUEL|OXYGEN)-[0-9]+",
                emergency,
            ).group(0)
            check_unavailable_collection(
                function(4, "L1"),
                baseline_function(4, "L1"),
                target_id,
                "resource_id",
            )
        elif function_name == "initialize_tow_tractors":
            target_id = re.search(
                r"MOB-TOW-[0-9]+",
                emergency,
            ).group(0)
            check_unavailable_collection(
                function(2, "L1"),
                baseline_function(2, "L1"),
                target_id,
                "resource_id",
            )
        elif function_name == "initialize_runways":
            target_id = re.search(
                r"起飞跑道(R[0-9]+)",
                emergency,
            ).group(1)
            check_unavailable_collection(
                function(),
                baseline_function(),
                target_id,
                "location_id",
            )
        elif function_name == "initialize_support_stands":
            target_id = re.search(
                r"保障站位([A-C][0-9]+)",
                emergency,
            ).group(1)
            check_unavailable_collection(
                function(),
                baseline_function(),
                target_id,
                "location_id",
            )
        elif function_name == "create_route_segment":
            segment_match = re.search(
                r"SEG-([A-Z][0-9]+)-([A-Z][0-9]+)",
                emergency,
            )
            start_id, end_id = segment_match.groups()
            target = function(start_id, end_id)
            if not isinstance(target, dict):
                raise AssertionError("路径函数未返回字典")
            if target.get("segment_id") != f"SEG-{start_id}-{end_id}":
                raise AssertionError("目标路径编号错误")
            if not is_unavailable(target):
                raise AssertionError("目标路径仍然可通行")
            unaffected = function("X1", "Y1")
            baseline_unaffected = baseline_function("X1", "Y1")
            if unaffected != baseline_unaffected:
                raise AssertionError("修改影响了无关路径")
        elif function_name == "initialize_aircraft":
            aircraft_id = re.search(
                r"舰载机(AC[0-9]+)",
                emergency,
            ).group(1)
            arrival_match = re.search(
                r"预计于([0-9]{2}):([0-9]{2})到达",
                emergency,
            )
            expected_minutes = (
                int(arrival_match.group(1)) * 60
                + int(arrival_match.group(2))
            )
            stands = [f"S{index}" for index in range(1, 15)]
            actual = function(14, stands)
            baseline = baseline_function(14, stands)
            if not isinstance(actual, dict) or set(actual) != set(baseline):
                raise AssertionError("舰载机集合发生变化")
            if actual[aircraft_id].get("actual_arrival_time") != float(
                expected_minutes
            ):
                raise AssertionError(
                    f"{aircraft_id}的actual_arrival_time不正确"
                )
            for other_id, baseline_record in baseline.items():
                if other_id == aircraft_id:
                    continue
                if actual[other_id] != baseline_record:
                    raise AssertionError(f"修改影响了{other_id}")
    except Exception as error:
        reason = f"{type(error).__name__}: {error}"
        return {
            "status": "fail",
            "total": 1,
            "solved": 0,
            "unsolved": [
                {
                    "event": emergency,
                    "function": function_name,
                    "reason": reason,
                }
            ],
        }
    return {
        "status": "pass",
        "total": 1,
        "solved": 1,
        "unsolved": [],
    }


def compact_feedback(
    review: dict[str, Any],
    validation_error: str | None = None,
) -> str:
    if validation_error:
        return f"上一轮代码无效：{validation_error}"
    if review.get("status") == "pass":
        return "上一轮验证已经通过。"

    lines = ["上一轮验证未通过，精确反馈如下："]
    for item in review.get("unsolved", []):
        lines.append(
            f"- event: {item.get('event', '')}\n"
            f"  function: {item.get('function', 'unknown')}\n"
            f"  reason: {item.get('reason', '验证未通过')}"
        )
    return "\n".join(lines)


def build_prompt(
    state: TaskState,
    tokenizer: Any,
    round_index: int,
) -> str:
    feedback = state.feedback or "这是第一轮，暂无上一轮反馈。"
    user_prompt = USER_PROMPT_TEMPLATE.format(
        emergency=state.emergency,
        code=state.current_code,
        feedback=feedback,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"这是第{round_index}/{MAX_REPAIR_ROUNDS}轮修复。\n\n"
                f"{user_prompt}"
            ),
        },
    ]
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except (AttributeError, TypeError, ValueError):
        return f"{SYSTEM_PROMPT}\n\n{messages[1]['content']}"


def generate_batch(
    llm: Any,
    prompts_to_run: list[str],
    sampling_params: Any,
) -> list[Any]:
    try:
        return llm.generate(
            prompts_to_run,
            sampling_params,
            use_tqdm=False,
        )
    except TypeError:
        return llm.generate(prompts_to_run, sampling_params)


def apply_generation(
    state: TaskState,
    request_output: Any,
    prompt: str,
    round_index: int,
    baseline_module: types.ModuleType,
) -> None:
    if not request_output.outputs:
        raise RuntimeError("模型没有返回候选代码")
    completion = request_output.outputs[0]
    raw_response = completion.text
    prompt_token_ids = getattr(request_output, "prompt_token_ids", None) or []
    completion_token_ids = getattr(completion, "token_ids", None) or []
    state.prompt_tokens += len(prompt_token_ids)
    state.completion_tokens += len(completion_token_ids)

    candidate = extract_code(raw_response)
    validation_error = validate_code(candidate, state.original_code)
    if validation_error:
        review = {
            "status": "invalid_code",
            "total": 1,
            "solved": 0,
            "unsolved": [],
        }
    else:
        state.current_code = candidate
        review = semantic_review(
            candidate,
            state.emergency,
            baseline_module,
        )

    state.final_review = review
    state.feedback = compact_feedback(review, validation_error)
    if review.get("status") == "pass":
        state.active = False
    elif round_index >= MAX_REPAIR_ROUNDS:
        state.active = False
        state.error = f"达到最大修复轮数：{MAX_REPAIR_ROUNDS}"

    state.attempts.append(
        {
            "round": round_index,
            "prompt": prompt,
            "raw_response": raw_response,
            "validation_error": validation_error,
            "review": review,
            "feedback_for_next_round": state.feedback,
            "prompt_tokens": len(prompt_token_ids),
            "completion_tokens": len(completion_token_ids),
        }
    )


def run_rounds(
    states: list[TaskState],
    tokenizer: Any,
    llm: Any,
    sampling_params: Any,
    baseline_module: types.ModuleType,
    batch_size: int,
) -> None:
    for round_index in range(1, MAX_REPAIR_ROUNDS + 1):
        active = [state for state in states if state.active]
        if not active:
            break
        print(
            f"round {round_index}/{MAX_REPAIR_ROUNDS}: "
            f"generating {len(active)} active tasks"
        )
        for group in split_batches(active, batch_size):
            prompts_to_run = [
                build_prompt(state, tokenizer, round_index)
                for state in group
            ]
            outputs = generate_batch(
                llm,
                prompts_to_run,
                sampling_params,
            )
            if len(outputs) != len(group):
                raise RuntimeError("模型输出数量与输入数量不一致")
            for state, prompt, output in zip(
                group,
                prompts_to_run,
                outputs,
            ):
                try:
                    apply_generation(
                        state,
                        output,
                        prompt,
                        round_index,
                        baseline_module,
                    )
                except Exception as error:
                    state.error = f"{type(error).__name__}: {error}"
                    state.final_review = {
                        "status": "error",
                        "total": 1,
                        "solved": 0,
                        "unsolved": [],
                    }
                    state.active = False


def prepare_output_dir() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_results(
    states: list[TaskState],
    startup_time: float,
    experiment_time: float,
) -> dict[str, Any]:
    prepare_output_dir()
    for state in states:
        (OUTPUT_DIR / f"result_{state.index}.py").write_text(
            state.current_code,
            encoding="utf-8",
        )

    traces = [
        {
            "case": state.index,
            "emergency": state.emergency,
            "success": state.final_review.get("status") == "pass",
            "error": state.error,
            "attempts": state.attempts,
            "prompt_tokens": state.prompt_tokens,
            "completion_tokens": state.completion_tokens,
        }
        for state in states
    ]
    (OUTPUT_DIR / "traces.json").write_text(
        json.dumps(traces, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    passed = sum(
        state.final_review.get("status") == "pass"
        for state in states
    )
    cases = len(states)
    metrics = {
        "framework": "mini-swe-agent-direct-vllm",
        "model": MODEL_NAME,
        "model_path": MODEL_PATH,
        "run": 1,
        "max_repair_rounds": MAX_REPAIR_ROUNDS,
        "cases": cases,
        "passed": passed,
        "failed": cases - passed,
        "accuracy": passed / cases if cases else 0.0,
        "model_calls": sum(len(state.attempts) for state in states),
        "startup_time": startup_time,
        "time": experiment_time,
        "average_response_time": (
            experiment_time / cases if cases else 0.0
        ),
    }
    (OUTPUT_DIR / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="直接使用本地vLLM执行最多三轮MAEH代码修复。"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="只运行前N条，0表示完整测试集。",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="每批任务数，0表示将本轮全部活动任务交给vLLM调度。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 0 or args.batch_size < 0:
        raise ValueError("limit和batch-size不能小于0")

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    original_code = SOURCE_FILE.read_text(encoding="utf-8")
    dataset = load_dataset(args.limit)
    baseline_module = execute_module(original_code, "baseline")
    states = [
        TaskState(
            index=index,
            emergency=item["emergency"],
            original_code=original_code,
            current_code=original_code,
        )
        for index, item in enumerate(dataset, start=1)
    ]

    startup_started_at = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
    )
    llm = LLM(
        model=MODEL_PATH,
        dtype="auto",
        trust_remote_code=True,
        gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
        seed=SEED,
    )
    sampling_params = SamplingParams(
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_tokens=MAX_MODEL_TOKENS,
        seed=SEED,
    )
    startup_time = time.perf_counter() - startup_started_at

    try:
        experiment_started_at = time.perf_counter()
        run_rounds(
            states,
            tokenizer,
            llm,
            sampling_params,
            baseline_module,
            args.batch_size,
        )
        experiment_time = time.perf_counter() - experiment_started_at
        metrics = save_results(states, startup_time, experiment_time)
        print(
            f"accuracy={metrics['accuracy']:.6f}, "
            f"average_response_time="
            f"{metrics['average_response_time']:.4f}s"
        )
    finally:
        del llm
        del tokenizer
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
