"""使用本地大模型逐条生成MAEH特情修复代码。"""

from __future__ import annotations

import gc
import json
import os
import shutil
from pathlib import Path
from typing import Any

import prompts as prompts_mod


SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_emergency_test_set.json"
)
BASE_OUT_DIR = PROJECT_ROOT / "local-llm-results"
MODEL_RUNS = 1
MAX_TOKENS = 8192

MODELS = [
    {
        "name": "Qwen2.5-Coder-7B-Instruct",
        "path": "/data/huggingface/Qwen2.5-Coder-7B-Instruct",
        "out_dir": "qwen2.5-coder-7b-instruct",
    },
    {
        "name": "Meta-Llama-3.1-8B-Instruct",
        "path": "/data/huggingface/Meta-Llama-3.1-8B-Instruct",
        "out_dir": "meta-llama-3.1-8b-instruct",
    },
    {
        "name": "glm-4-9b-chat",
        "path": "/data/huggingface/glm-4-9b-chat",
        "out_dir": "glm-4-9b-chat",
    },
]

BASE_OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset(
    dataset_file: str | os.PathLike[str],
) -> list[dict[str, str]]:
    """加载当前项目使用的单特情数据集。"""

    with open(dataset_file, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError("数据集顶层结构必须是列表")

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(dataset, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第{index}条数据不是字典")
        emergency = item.get("emergency")
        if not isinstance(emergency, str) or not emergency.strip():
            raise ValueError(
                f"第{index}条数据缺少非空emergency字段"
            )
        normalized.append({"emergency": emergency.strip()})
    return normalized


def extract_fenced_code(text: str) -> str | None:
    """提取模型输出中最长的Python代码块。"""

    lines = text.replace("\r\n", "\n").splitlines()
    blocks: list[tuple[str, str]] = []
    in_block = False
    block_language = ""
    block_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_block:
                blocks.append(
                    (
                        block_language,
                        "\n".join(block_lines).strip(),
                    )
                )
                in_block = False
                block_language = ""
                block_lines = []
            else:
                block_language = stripped[3:].strip().lower()
                in_block = True
            continue
        if in_block:
            block_lines.append(line)

    if in_block and block_lines:
        blocks.append(
            (
                block_language,
                "\n".join(block_lines).strip(),
            )
        )

    python_blocks = [
        code
        for language, code in blocks
        if language in {"", "python", "py"}
    ]
    candidates = python_blocks or [code for _, code in blocks]
    if not candidates:
        return None
    return max(candidates, key=len)


def strip_to_code_start(text: str) -> str:
    """去除无代码前缀，但不改写模型生成的Python内容。"""

    lines = text.strip().splitlines()
    code_prefixes = (
        "import ",
        "from ",
        "def ",
        "async def ",
        "class ",
        "@",
    )

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(code_prefixes):
            return "\n".join(lines[index:]).strip()
        if stripped.startswith(('"""', "'''")):
            lookahead = lines[index + 1:index + 12]
            if any(
                next_line.lstrip().startswith(code_prefixes)
                for next_line in lookahead
            ):
                return "\n".join(lines[index:]).strip()
    return text.strip()


def clean_code_block(text: str) -> str:
    """仅移除模型回复包装，不新增、删除或替换import。"""

    code = extract_fenced_code(text)
    if code is None:
        code = strip_to_code_start(text)
    return code.strip()


def build_plain_prompt(item: dict[str, str]) -> str:
    """为不支持chat template的分词器构建普通文本提示。"""

    user_prompt = prompts_mod.USER_PROMPT.format(
        EMERGENCY_SITUATIONS=item["emergency"],
        ORIGINAL_CODE=prompts_mod.ORIGINAL_CODE,
    )
    return (
        f"{prompts_mod.SYSTEM_PROMPT.strip()}\n\n"
        f"{user_prompt.strip()}\n\n"
        "修改后的完整 Python 代码:\n"
    )


def build_inputs(
    tokenizer: Any,
    dataset: list[dict[str, str]],
) -> list[str]:
    """按数据集顺序构造模型输入，保证result_N与第N条特情对应。"""

    inputs: list[str] = []
    for item in dataset:
        messages = [
            {
                "role": "system",
                "content": prompts_mod.SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompts_mod.USER_PROMPT.format(
                    EMERGENCY_SITUATIONS=item["emergency"],
                    ORIGINAL_CODE=prompts_mod.ORIGINAL_CODE,
                ),
            },
        ]
        try:
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except (AttributeError, ValueError, TypeError):
            text = build_plain_prompt(item)
        inputs.append(text)
    return inputs


def prepare_out_dir(out_dir: str | os.PathLike[str]) -> Path:
    """清空并重新创建单次实验输出目录。"""

    output_path = Path(out_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def seed_everything(seed: int) -> None:
    """设置本地推理使用的随机种子。"""

    import torch

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def call_local_model_batch(
    model_path: str,
    out_dir: str | os.PathLike[str],
    dataset: list[dict[str, str]],
) -> dict[str, int]:
    """调用一个本地模型并按顺序写出result_N.py。"""

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    seed_everything(SEED)
    output_path = Path(out_dir)
    tokenizer = None
    llm = None

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
        )
        llm = LLM(
            model=model_path,
            dtype="auto",
            trust_remote_code=True,
            gpu_memory_utilization=0.9,
            seed=SEED,
        )
        sampling_params = SamplingParams(
            temperature=0.8,
            top_p=1.0,
            max_tokens=MAX_TOKENS,
            seed=SEED,
        )

        inputs = build_inputs(tokenizer, dataset)
        outputs = llm.generate(inputs, sampling_params)
        if len(outputs) != len(dataset):
            raise RuntimeError(
                "模型输出数量与数据集数量不一致: "
                f"{len(outputs)} != {len(dataset)}"
            )

        for index, output in enumerate(outputs, start=1):
            if not output.outputs:
                raw_text = ""
            else:
                raw_text = output.outputs[0].text
            code = clean_code_block(raw_text)

            result_file = output_path / f"result_{index}.py"
            result_file.write_text(
                code + ("\n" if code else ""),
                encoding="utf-8",
            )
    finally:
        if llm is not None:
            del llm
        if tokenizer is not None:
            del tokenizer
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    return {
        "generated": len(dataset),
    }


def run_single_experiment(
    model_config: dict[str, str],
    run_index: int,
    dataset: list[dict[str, str]],
) -> None:
    """执行一轮代码生成。"""

    out_dir = (
        BASE_OUT_DIR
        / model_config["out_dir"]
        / f"run_{run_index}"
    )
    prepare_out_dir(out_dir)

    call_local_model_batch(
        model_config["path"],
        out_dir,
        dataset,
    )


def main() -> None:
    dataset = load_dataset(DATASET_FILE)
    for model_config in MODELS:
        for run_index in range(1, MODEL_RUNS + 1):
            run_single_experiment(
                model_config,
                run_index,
                dataset,
            )


if __name__ == "__main__":
    main()
