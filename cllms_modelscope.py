"""通过ModelScope API运行云端模型并生成特情处置代码。"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

import prompts


PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_emergency_test_set.json"
)
BASE_RESULT_DIR = PROJECT_ROOT / "cllm-modelscope-results"
API_KEYS_FILE = PROJECT_ROOT / "modelscope_api_keys.json"
BASE_URL = "https://api-inference.modelscope.cn/v1"
MAX_ATTEMPTS = 3
MAX_TOKENS = 8192
REQUEST_TIMEOUT = 600.0

MODELS: list[dict[str, Any]] = [
    # {
    #     "name": "Qwen3-235B-A22B",
    #     "model": "Qwen/Qwen3-235B-A22B",
    #     "out_dir": "qwen3-235b-a22b",
    #     "temperature": 0.8,
    #     "top_p": 1,
    #     "extra_body": {
    #         "enable_thinking": False,
    #         "top_k": 20,
    #     },
    # },
    {
        "name": "Kimi-K2.6",
        "model": "moonshotai/Kimi-K2.6:DashScope",
        "out_dir": "kimi-k2.6",
        "temperature": 0.8,
        "top_p": 1,
        "extra_body": {"enable_thinking": False},
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


def load_api_keys() -> list[str]:
    """优先读取环境变量，否则读取项目中的密钥文件。"""

    configured = os.getenv("MODELSCOPE_API_KEYS", "")
    if configured.strip():
        keys = re.split(r"[,;\s]+", configured)
    else:
        try:
            keys = json.loads(
                API_KEYS_FILE.read_text(encoding="utf-8")
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                f"找不到ModelScope密钥文件：{API_KEYS_FILE}"
            ) from error
        if not isinstance(keys, list):
            raise ValueError("ModelScope密钥文件必须是JSON列表")

    unique_keys: list[str] = []
    for key in keys:
        if not isinstance(key, str):
            raise ValueError("ModelScope密钥必须是字符串")
        stripped = key.strip()
        if stripped and stripped not in unique_keys:
            unique_keys.append(stripped)
    if not unique_keys:
        raise RuntimeError("没有可用的ModelScope API key")
    return unique_keys


def make_client(api_key: str) -> AsyncOpenAI:
    """创建异步客户端，任务级重试由队列统一处理。"""

    return AsyncOpenAI(
        base_url=BASE_URL,
        api_key=api_key,
        timeout=REQUEST_TIMEOUT,
        max_retries=0,
    )


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
    """去掉推理文本和Markdown包装，保留模型生成的代码。"""

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


def model_request(
    model_config: dict[str, Any],
    messages: list[dict[str, str]],
    max_tokens: int,
) -> dict[str, Any]:
    """按照不同模型的官方推荐参数构造请求体。"""

    request: dict[str, Any] = {
        "model": model_config["model"],
        "messages": messages,
        "temperature": model_config["temperature"],
        "top_p": model_config["top_p"],
        "max_tokens": max_tokens,
    }
    if model_config["extra_body"]:
        request["extra_body"] = dict(model_config["extra_body"])
    return request


def response_content(response: Any) -> str:
    """读取OpenAI兼容响应中的最终答案。"""

    if not response.choices:
        raise RuntimeError("模型响应不包含choices")
    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("模型响应不包含最终content")
    return content


async def call_case(
    index: int,
    client: AsyncOpenAI,
    model_config: dict[str, Any],
    dataset: list[dict[str, str]],
    result_dir: Path,
) -> None:
    """请求一条特情并写出对应的完整Python代码。"""

    response = await client.chat.completions.create(
        **model_request(
            model_config,
            build_messages(dataset[index]["emergency"]),
            max_tokens=MAX_TOKENS,
        )
    )
    code = clean_code_block(response_content(response))
    (result_dir / f"result_{index + 1}.py").write_text(
        code + ("\n" if code else ""),
        encoding="utf-8",
    )


async def run_model(
    model_config: dict[str, Any],
    dataset: list[dict[str, str]],
    keys: list[str],
) -> None:
    """使用全部有效key并发跑完一个模型的一轮测试集。"""

    result_dir = BASE_RESULT_DIR / model_config["out_dir"]
    if result_dir.exists():
        shutil.rmtree(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)

    queue: asyncio.Queue[int] = asyncio.Queue()
    for index in range(len(dataset)):
        queue.put_nowait(index)

    attempts = [0] * len(dataset)
    completed = 0

    async def worker(client: AsyncOpenAI) -> None:
        nonlocal completed
        while True:
            index = await queue.get()
            attempts[index] += 1
            try:
                await call_case(
                    index,
                    client,
                    model_config,
                    dataset,
                    result_dir,
                )
            except Exception:
                if attempts[index] < MAX_ATTEMPTS:
                    queue.put_nowait(index)
                else:
                    (result_dir / f"result_{index + 1}.py").write_text(
                        "",
                        encoding="utf-8",
                    )
            else:
                completed += 1
                print(
                    f"[{model_config['name']}] "
                    f"{completed}/{len(dataset)}"
                )
            finally:
                queue.task_done()

    clients: list[AsyncOpenAI] = []
    workers: list[asyncio.Task[None]] = []
    for key in keys:
        client = make_client(key)
        clients.append(client)
        workers.append(asyncio.create_task(worker(client)))

    try:
        await queue.join()
    finally:
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        await asyncio.gather(
            *(client.close() for client in clients),
            return_exceptions=True,
        )

async def async_main() -> None:
    """依次运行三个模型各一轮。"""

    dataset = load_dataset(DATASET_FILE)
    keys = load_api_keys()
    for model_config in MODELS:
        await run_model(
            model_config,
            dataset,
            keys,
        )


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
