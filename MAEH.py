"""使用两个智能体完成MAEH特情定位和函数修改。"""

from __future__ import annotations

import ast
import gc
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

import prompts


SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_emergency_test_set.json"
)
SOURCE_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_resource_initialization.py"
)
BASE_OUT_DIR = PROJECT_ROOT / "MAEH-results"
MODEL_RUNS = 1
AGENT1_MAX_TOKENS = 64
AGENT2_MAX_TOKENS = 4096

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
    """加载单特情测试集。"""

    with open(dataset_file, "r", encoding="utf-8") as file:
        raw_dataset = json.load(file)
    if not isinstance(raw_dataset, list):
        raise ValueError("数据集顶层结构必须是列表")

    dataset: list[dict[str, str]] = []
    for index, item in enumerate(raw_dataset, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第{index}条数据不是字典")
        emergency = item.get("emergency")
        if not isinstance(emergency, str) or not emergency.strip():
            raise ValueError(f"第{index}条数据缺少非空emergency字段")
        dataset.append({"emergency": emergency.strip()})
    return dataset


def load_source_functions(
    source_file: str | os.PathLike[str],
) -> tuple[dict[str, str], str]:
    """读取顶层函数完整源码以及原文件的import部分。"""

    source_path = Path(source_file)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=os.fspath(source_path))
    lines = source.splitlines()
    functions: dict[str, str] = {}
    imports: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end_lineno = node.end_lineno or node.lineno
            imports.append(
                "\n".join(lines[node.lineno - 1:end_lineno])
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_lineno = node.end_lineno or node.lineno
            functions[node.name] = "\n".join(
                lines[node.lineno - 1:end_lineno]
            )

    if not functions:
        raise ValueError(f"没有在{source_path}中找到顶层函数")
    return functions, "\n".join(imports).strip()


def build_function_catalog(functions: dict[str, str]) -> str:
    """构造供Agent1选择的函数名称、参数和职责目录。"""

    entries: list[str] = []
    for name, source in functions.items():
        tree = ast.parse(source)
        function_node = tree.body[0]
        if not isinstance(
            function_node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue
        signature_lines: list[str] = []
        for line in source.splitlines():
            signature_lines.append(line.strip())
            if line.rstrip().endswith(":"):
                break
        signature = " ".join(signature_lines)
        docstring = ast.get_docstring(function_node, clean=True) or ""
        summary = docstring.splitlines()[0].strip() if docstring else ""
        entries.append(f"- {signature} {summary}".rstrip())
    return "\n".join(entries)


def build_chat_input(
    tokenizer: Any,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """使用模型chat template构造输入，不支持时退回普通文本。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except (AttributeError, ValueError, TypeError):
        return (
            f"{system_prompt.strip()}\n\n"
            f"{user_prompt.strip()}\n\n"
        )


def output_text(output: Any) -> str:
    """读取vLLM单条输出文本。"""

    if not output.outputs:
        return ""
    return output.outputs[0].text.strip()


def parse_function_name(
    raw_text: str,
    valid_names: set[str],
) -> str | None:
    """从Agent1回复中读取唯一的合法函数名。"""

    cleaned = raw_text.replace("```", " ").strip()
    exact = cleaned.strip("'\"` \t\r\n.,:;，。；：")
    if exact in valid_names:
        return exact

    matches = [
        name
        for name in valid_names
        if re.search(rf"\b{re.escape(name)}\b", cleaned)
    ]
    if len(matches) == 1:
        return matches[0]
    return None


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


def clean_agent2_code(raw_text: str) -> str:
    """仅移除Agent2回复外层包装。"""

    fenced = extract_fenced_code(raw_text)
    if fenced is not None:
        return fenced

    lines = raw_text.strip().splitlines()
    for index, line in enumerate(lines):
        if line.lstrip().startswith(("def ", "async def ", "@")):
            return "\n".join(lines[index:]).strip()
    return raw_text.strip()


def prepare_out_dir(out_dir: str | os.PathLike[str]) -> Path:
    """清空并创建单轮输出目录。"""

    output_path = Path(out_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def seed_everything(seed: int) -> None:
    """设置本地推理随机种子。"""

    import torch

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def run_two_agents(
    model_path: str,
    out_dir: str | os.PathLike[str],
    dataset: list[dict[str, str]],
) -> None:
    """使用同一本地模型依次运行Agent1和Agent2。"""

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    seed_everything(SEED)
    functions, import_source = load_source_functions(SOURCE_FILE)
    function_catalog = build_function_catalog(functions)
    valid_names = set(functions)
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

        agent1_inputs = [
            build_chat_input(
                tokenizer,
                prompts.AGENT1_SYSTEM_PROMPT,
                prompts.AGENT1_USER_PROMPT.format(
                    EMERGENCY=item["emergency"],
                    FUNCTION_CATALOG=function_catalog,
                ),
            )
            for item in dataset
        ]
        agent1_outputs = llm.generate(
            agent1_inputs,
            SamplingParams(
                temperature=0.8,
                top_p=1.0,
                max_tokens=AGENT1_MAX_TOKENS,
                seed=SEED,
            ),
        )
        if len(agent1_outputs) != len(dataset):
            raise RuntimeError("Agent1输出数量与数据集数量不一致")

        traces: list[dict[str, Any]] = []
        agent2_inputs: list[str] = []
        agent2_case_indices: list[int] = []
        for case_index, (item, output) in enumerate(
            zip(dataset, agent1_outputs),
        ):
            raw_agent1 = output_text(output)
            function_name = parse_function_name(
                raw_agent1,
                valid_names,
            )
            trace = {
                "case": case_index + 1,
                "emergency": item["emergency"],
                "agent1_raw": raw_agent1,
                "function": function_name,
                "function_source": (
                    functions[function_name]
                    if function_name is not None
                    else None
                ),
                "agent2_raw": None,
            }
            traces.append(trace)

            if function_name is None:
                continue
            function_source = functions[function_name]
            agent2_inputs.append(
                build_chat_input(
                    tokenizer,
                    prompts.SYSTEM_PROMPT,
                    prompts.USER_PROMPT.format(
                        EMERGENCY_SITUATIONS=item["emergency"],
                        ORIGINAL_CODE=function_source,
                    ),
                )
            )
            agent2_case_indices.append(case_index)

        agent2_outputs = llm.generate(
            agent2_inputs,
            SamplingParams(
                temperature=0.0,
                top_p=1.0,
                max_tokens=AGENT2_MAX_TOKENS,
                seed=SEED,
            ),
        ) if agent2_inputs else []
        if len(agent2_outputs) != len(agent2_inputs):
            raise RuntimeError("Agent2输出数量与输入数量不一致")

        generated_by_case: dict[int, str] = {}
        for case_index, output in zip(
            agent2_case_indices,
            agent2_outputs,
        ):
            raw_agent2 = output_text(output)
            traces[case_index]["agent2_raw"] = raw_agent2
            generated_by_case[case_index] = clean_agent2_code(
                raw_agent2
            )

        for case_index in range(len(dataset)):
            function_code = generated_by_case.get(case_index, "")
            module_parts = [part for part in (
                import_source,
                function_code,
            ) if part]
            result_file = output_path / f"result_{case_index + 1}.py"
            result_file.write_text(
                "\n\n".join(module_parts).strip() + "\n",
                encoding="utf-8",
            )

        (output_path / "agent_traces.json").write_text(
            json.dumps(traces, ensure_ascii=False, indent=2) + "\n",
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


def run_single_experiment(
    model_config: dict[str, str],
    run_index: int,
    dataset: list[dict[str, str]],
) -> None:
    """执行一个模型的一轮两智能体实验。"""

    out_dir = (
        BASE_OUT_DIR
        / model_config["out_dir"]
        / f"run_{run_index}"
    )
    prepare_out_dir(out_dir)

    run_two_agents(
        model_config["path"],
        out_dir,
        dataset,
    )


def main() -> None:
    """依次运行三个模型，每个模型执行两轮。"""

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
