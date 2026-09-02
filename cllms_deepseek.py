"""通过DeepSeek API运行V4-Flash并生成特情处置代码。"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

import prompts


PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_emergency_test_set.json"
)
BASE_RESULT_DIR = PROJECT_ROOT / "cllm-deepseek-results"
API_KEY_FILE = PROJECT_ROOT / "deepseek_api_key.txt"
BASE_URL = "https://api.deepseek.com"
MAX_ATTEMPTS = 3
MAX_TOKENS = 8192
REQUEST_INTERVAL_SECONDS = 10.0

MODELS: list[dict[str, str]] = [
    {
        "name": "DeepSeek-V4-Flash",
        "model": "deepseek-v4-flash",
        "out_dir": "deepseek-v4-flash",
    },
]

BASE_RESULT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset(
    dataset_file: str | os.PathLike[str],
) -> list[dict[str, str]]:
    """加载测试集并统一特情字段名。"""

    with open(dataset_file, "r", encoding="utf-8") as file:
        raw_dataset = json.load(file)
    if not isinstance(raw_dataset, list):
        raise ValueError("测试集顶层结构必须是列表")

    dataset: list[dict[str, str]] = []
    for index, item in enumerate(raw_dataset, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第{index}条测试数据不是字典")
        emergency = item.get(
            "emergency",
            item.get("emergency_situation"),
        )
        if not isinstance(emergency, str) or not emergency.strip():
            raise ValueError(f"第{index}条测试数据缺少特情内容")
        dataset.append({"emergency": emergency.strip()})
    return dataset


def load_api_key() -> str:
    """优先读取环境变量，否则读取项目中的DeepSeek密钥文件。"""

    configured = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if configured:
        return configured
    try:
        api_key = API_KEY_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise RuntimeError(
            f"找不到DeepSeek API密钥文件：{API_KEY_FILE}"
        ) from error
    if not api_key:
        raise RuntimeError("DeepSeek API密钥不能为空")
    return api_key


def extract_fenced_code(text: str) -> str | None:
    """提取回复中最长的Python代码块。"""

    matches = re.findall(
        r"```(?:python|py)?\s*\n?(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not matches:
        return None
    return max((item.strip() for item in matches), key=len)


def clean_code_block(text: str) -> str:
    """去掉Markdown包装和说明文字，只保留模型生成的代码。"""

    fenced = extract_fenced_code(text)
    if fenced is not None:
        return fenced

    lines = text.strip().splitlines()
    code_prefixes = (
        "import ",
        "from ",
        "def ",
        "async def ",
        '"""',
        "'''",
    )
    for index, line in enumerate(lines):
        if line.lstrip().startswith(code_prefixes):
            return "\n".join(lines[index:]).strip()
    return text.strip()


def build_messages(emergency: str) -> list[dict[str, str]]:
    """构造完整代码修复对话。"""

    return [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {
            "role": "user",
            "content": prompts.USER_PROMPT.format(
                EMERGENCY_SITUATIONS=emergency,
                ORIGINAL_CODE=prompts.ORIGINAL_CODE,
            ),
        },
    ]


def response_content(response: Any) -> str:
    """读取DeepSeek响应中的最终答案。"""

    if not response.choices:
        raise RuntimeError("模型响应不包含choices")
    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("模型响应不包含最终content")
    return content


def run_model(
    model_config: dict[str, str],
    dataset: list[dict[str, str]],
    api_key: str,
) -> None:
    """串行运行完整测试集，并在请求之间至少等待10秒。"""

    result_dir = BASE_RESULT_DIR / model_config["out_dir"]
    if result_dir.exists():
        shutil.rmtree(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    next_request_at = 0.0

    try:
        for index, item in enumerate(dataset, start=1):
            for attempt in range(1, MAX_ATTEMPTS + 1):
                wait_seconds = next_request_at - time.perf_counter()
                if wait_seconds > 0:
                    time.sleep(wait_seconds)

                try:
                    response = client.chat.completions.create(
                        model=model_config["model"],
                        messages=build_messages(item["emergency"]),
                        stream=False,
                        temperature=0.8,
                        top_p=1.0,
                        max_tokens=MAX_TOKENS,
                        extra_body={
                            "thinking": {"type": "disabled"},
                        },
                    )
                    code = clean_code_block(
                        response_content(response)
                    )
                except Exception:
                    if attempt == MAX_ATTEMPTS:
                        (
                            result_dir / f"result_{index}.py"
                        ).write_text("", encoding="utf-8")
                else:
                    (
                        result_dir / f"result_{index}.py"
                    ).write_text(
                        code + ("\n" if code else ""),
                        encoding="utf-8",
                    )
                    print(
                        f"[{model_config['name']}] "
                        f"{index}/{len(dataset)}"
                    )
                    break
                finally:
                    next_request_at = (
                        time.perf_counter()
                        + REQUEST_INTERVAL_SECONDS
                    )
    finally:
        client.close()

def main() -> None:
    dataset = load_dataset(DATASET_FILE)
    api_key = load_api_key()
    for model_config in MODELS:
        run_model(model_config, dataset, api_key)


if __name__ == "__main__":
    main()
