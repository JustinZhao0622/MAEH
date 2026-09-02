"""Use GLM-5.2 to generate MAEH supervised fine-tuning data."""

from __future__ import annotations

import ast
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from zai import ZhipuAiClient

import prompts


PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_emergency_training_set.json"
)
SOURCE_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_resource_initialization.py"
)
API_KEY_FILE = PROJECT_ROOT / "zhipu_api_key.txt"
OUTPUT_DIR = PROJECT_ROOT / "glm-training-results"
RESPONSE_DIR = OUTPUT_DIR / "responses"
TRAINING_FILE = PROJECT_ROOT / "datasets" / "maeh_glm52_sft.json"

MODEL = "glm-5.2"
MAX_ATTEMPTS = 3
MAX_TOKENS = 8192
REQUEST_INTERVAL_SECONDS = 10.0

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


def load_dataset() -> list[dict[str, str]]:
    """Read the training emergencies without modifying the source file."""

    raw_dataset = json.loads(DATASET_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw_dataset, list):
        raise ValueError("训练集顶层结构必须是列表")

    dataset: list[dict[str, str]] = []
    for index, item in enumerate(raw_dataset, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第{index}条训练数据不是字典")
        emergency = item.get("emergency")
        if not isinstance(emergency, str) or not emergency.strip():
            raise ValueError(f"第{index}条训练数据缺少非空emergency字段")
        dataset.append({"emergency": emergency.strip()})
    return dataset


def load_api_key() -> str:
    """Read the Zhipu API key from the environment or local key file."""

    configured = os.getenv("ZHIPU_API_KEY", "").strip()
    if configured:
        return configured
    try:
        api_key = API_KEY_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise RuntimeError(f"找不到智谱API密钥文件：{API_KEY_FILE}") from error
    if not api_key:
        raise RuntimeError("智谱API密钥不能为空")
    return api_key


def load_source_functions() -> tuple[str, dict[str, str]]:
    """Extract shared imports and every top-level function with AST."""

    source = SOURCE_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=os.fspath(SOURCE_FILE))
    lines = source.splitlines()
    imports: list[str] = []
    functions: dict[str, str] = {}

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end_lineno = node.end_lineno or node.lineno
            imports.append("\n".join(lines[node.lineno - 1:end_lineno]))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_lineno = node.end_lineno or node.lineno
            functions[node.name] = "\n".join(
                lines[node.lineno - 1:end_lineno]
            )

    if not functions:
        raise ValueError(f"没有在{SOURCE_FILE}中找到顶层函数")
    return "\n".join(imports), functions


def function_name_for_emergency(emergency: str) -> str:
    """Map one emergency to the single function that owns its entity."""

    fixed_match = re.search(
        r"FIX-[A-C]-(POWER|HYDRAULIC|FUEL|OXYGEN)-\d+",
        emergency,
    )
    if fixed_match:
        return RESOURCE_FUNCTIONS[("FIX", fixed_match.group(1))]

    mobile_match = re.search(
        r"MOB-(POWER|HYDRAULIC|FUEL|OXYGEN)-\d+",
        emergency,
    )
    if mobile_match:
        return RESOURCE_FUNCTIONS[("MOB", mobile_match.group(1))]
    if re.search(r"MOB-TOW-\d+", emergency):
        return "initialize_tow_tractors"
    if "SEG-" in emergency:
        return "create_route_segment"
    if re.search(r"舰载机AC\d+", emergency):
        return "initialize_aircraft"
    if "起飞跑道" in emergency:
        return "initialize_runways"
    if "保障站位" in emergency:
        return "initialize_support_stands"
    if "着陆点" in emergency:
        return "initialize_landing_points"
    if re.search(r"保障作业|作业T\d+", emergency):
        return "initialize_support_tasks"
    raise ValueError(f"无法确定特情对应的函数：{emergency}")


def source_for_emergency(
    emergency: str,
    import_source: str,
    functions: dict[str, str],
) -> tuple[str, str]:
    """Return imports plus exactly one function for the current emergency."""

    function_name = function_name_for_emergency(emergency)
    try:
        function_source = functions[function_name]
    except KeyError as error:
        raise ValueError(f"源文件缺少函数：{function_name}") from error
    source = f"{import_source}\n\n{function_source}".strip()
    return function_name, source


def build_messages(
    emergency: str,
    relevant_source: str,
) -> list[dict[str, str]]:
    """Build the exact system and user messages used for generation."""

    return [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {
            "role": "user",
            "content": prompts.USER_PROMPT.format(
                EMERGENCY_SITUATIONS=emergency,
                ORIGINAL_CODE=relevant_source,
            ),
        },
    ]


def extract_fenced_code(text: str) -> str | None:
    matches = re.findall(
        r"```(?:python|py)?\s*\n?(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not matches:
        return None
    return max((item.strip() for item in matches), key=len)


def clean_code_block(text: str) -> str:
    """Remove response prose without changing the generated Python code."""

    fenced = extract_fenced_code(text)
    if fenced is not None:
        return fenced

    lines = text.strip().splitlines()
    prefixes = ("import ", "from ", "def ", "async def ", '"""', "'''")
    for index, line in enumerate(lines):
        if line.lstrip().startswith(prefixes):
            return "\n".join(lines[index:]).strip()
    return text.strip()


def response_content(response: Any) -> str:
    if not response.choices:
        raise RuntimeError("模型响应不包含choices")
    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("模型响应不包含最终content")
    return content


def write_training_file(
    dataset: list[dict[str, str]],
    import_source: str,
    functions: dict[str, str],
) -> int:
    """Rebuild the JSON array from all successful response files."""

    records: list[dict[str, str]] = []
    for index, item in enumerate(dataset, start=1):
        response_file = RESPONSE_DIR / f"result_{index}.py"
        if not response_file.exists():
            continue
        answer = response_file.read_text(encoding="utf-8").strip()
        if not answer:
            continue
        _, relevant_source = source_for_emergency(
            item["emergency"],
            import_source,
            functions,
        )
        messages = build_messages(item["emergency"], relevant_source)
        records.append(
            {
                "system": messages[0]["content"],
                "instruction": messages[1]["content"],
                "input": "",
                "output": answer,
            }
        )

    TRAINING_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = TRAINING_FILE.with_suffix(".json.tmp")
    temporary_file.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_file.replace(TRAINING_FILE)
    return len(records)


def main() -> None:
    dataset = load_dataset()
    import_source, functions = load_source_functions()
    api_key = load_api_key()
    client = ZhipuAiClient(api_key=api_key)
    RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
    next_request_at = 0.0

    try:
        for index, item in enumerate(dataset, start=1):
            response_file = RESPONSE_DIR / f"result_{index}.py"
            if response_file.exists() and response_file.stat().st_size > 0:
                print(f"[GLM-5.2] {index}/{len(dataset)} 已存在，跳过")
                continue

            function_name, relevant_source = source_for_emergency(
                item["emergency"],
                import_source,
                functions,
            )
            messages = build_messages(item["emergency"], relevant_source)

            for attempt in range(1, MAX_ATTEMPTS + 1):
                wait_seconds = next_request_at - time.perf_counter()
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        thinking={"type": "disabled"},
                        temperature=0.8,
                        top_p=1.0,
                        max_tokens=MAX_TOKENS,
                    )
                    answer = clean_code_block(response_content(response))
                    if not answer:
                        raise RuntimeError("模型返回了空代码")
                except Exception as error:
                    if attempt == MAX_ATTEMPTS:
                        print(
                            f"[GLM-5.2] {index}/{len(dataset)} 失败："
                            f"{type(error).__name__}: {error}"
                        )
                else:
                    response_file.write_text(answer + "\n", encoding="utf-8")
                    write_training_file(dataset, import_source, functions)
                    print(
                        f"[GLM-5.2] {index}/{len(dataset)} "
                        f"完成，函数={function_name}"
                    )
                    break
                finally:
                    next_request_at = (
                        time.perf_counter() + REQUEST_INTERVAL_SECONDS
                    )
    finally:
        record_count = write_training_file(dataset, import_source, functions)
        print(f"训练文件：{TRAINING_FILE}，样本数={record_count}")


if __name__ == "__main__":
    main()
