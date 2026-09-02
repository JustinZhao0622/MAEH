"""Run MAED with base Qwen for Agent1 and merged LoRA Qwen for Agent2."""

from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

import prompts
from MAEH import (
    build_chat_input,
    build_function_catalog,
    clean_agent2_code,
    load_dataset,
    load_source_functions,
    output_text,
    parse_function_name,
    prepare_out_dir,
    seed_everything,
)


SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_emergency_test_set.json"
)
SOURCE_FILE = (
    PROJECT_ROOT / "datasets" / "maeh_resource_initialization.py"
)

EDIT_MODEL_PATH = Path(
    "/data/huggingface/Qwen2.5-Coder-7B-Instruct"
)
DECISION_MODELS_PATH = (
    PROJECT_ROOT / "datasets" / "train_2026-08-02-21-31-45"
)
DECISION_COMBINED_MODELS_PATH = (
    PROJECT_ROOT / "datasets" / "train_2026-08-02-21-31-45-merged"
)
BASE_OUT_DIR = PROJECT_ROOT / "MAED-lora-results"
OUT_DIR = (
    BASE_OUT_DIR
    / "qwen2.5-coder-7b-instruct-lora"
    / "run_1"
)

AGENT1_MAX_TOKENS = 64
AGENT2_MAX_TOKENS = 4096


def merged_model_is_complete(model_path: Path) -> bool:
    """Return whether the target contains config, tokenizer, and weights."""

    weight_files = [
        *model_path.glob("model*.safetensors"),
        *model_path.glob("pytorch_model*.bin"),
    ]
    return (
        (model_path / "config.json").is_file()
        and (model_path / "tokenizer_config.json").is_file()
        and bool(weight_files)
    )


def merge_lora_model(force: bool = False) -> Path:
    """Merge the trained LoRA adapter into the original Qwen model."""

    if not (DECISION_MODELS_PATH / "adapter_config.json").is_file():
        raise FileNotFoundError(
            f"找不到LoRA配置：{DECISION_MODELS_PATH}"
        )
    if merged_model_is_complete(DECISION_COMBINED_MODELS_PATH) and not force:
        return DECISION_COMBINED_MODELS_PATH

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    temporary_path = DECISION_COMBINED_MODELS_PATH.with_name(
        f"{DECISION_COMBINED_MODELS_PATH.name}.tmp"
    )
    if temporary_path.exists():
        shutil.rmtree(temporary_path)

    base_model = None
    lora_model = None
    combined_model = None
    base_tokenizer = None
    try:
        base_model = AutoModelForCausalLM.from_pretrained(
            EDIT_MODEL_PATH,
            torch_dtype="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        base_tokenizer = AutoTokenizer.from_pretrained(
            EDIT_MODEL_PATH,
            trust_remote_code=True,
        )
        lora_model = PeftModel.from_pretrained(
            base_model,
            DECISION_MODELS_PATH,
        )
        combined_model = lora_model.merge_and_unload()
        combined_model.save_pretrained(
            temporary_path,
            safe_serialization=True,
            max_shard_size="5GB",
        )
        base_tokenizer.save_pretrained(temporary_path)

        if DECISION_COMBINED_MODELS_PATH.exists():
            shutil.rmtree(DECISION_COMBINED_MODELS_PATH)
        temporary_path.replace(DECISION_COMBINED_MODELS_PATH)
    finally:
        if combined_model is not None:
            del combined_model
        if lora_model is not None:
            del lora_model
        if base_model is not None:
            del base_model
        if base_tokenizer is not None:
            del base_tokenizer
        gc.collect()

    if not merged_model_is_complete(DECISION_COMBINED_MODELS_PATH):
        raise RuntimeError("LoRA合并产物不完整")
    return DECISION_COMBINED_MODELS_PATH


def release_vllm() -> None:
    """Release vLLM distributed state before loading the next model."""

    gc.collect()
    try:
        import torch
        from vllm.distributed import (
            destroy_distributed_environment,
            destroy_model_parallel,
        )

        destroy_model_parallel()
        destroy_distributed_environment()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def run_agent1(
    dataset: list[dict[str, str]],
    functions: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str | None]]:
    """Use the unmodified Qwen model to select one function per case."""

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    tokenizer = None
    llm = None
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            EDIT_MODEL_PATH,
            trust_remote_code=True,
        )
        llm = LLM(
            model=os.fspath(EDIT_MODEL_PATH),
            dtype="auto",
            trust_remote_code=True,
            gpu_memory_utilization=0.9,
            seed=SEED,
        )
        function_catalog = build_function_catalog(functions)
        inputs = [
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
        outputs = llm.generate(
            inputs,
            SamplingParams(
                temperature=0.8,
                top_p=1.0,
                max_tokens=AGENT1_MAX_TOKENS,
                seed=SEED,
            ),
        )
        if len(outputs) != len(dataset):
            raise RuntimeError("Agent1输出数量与测试集数量不一致")

        valid_names = set(functions)
        traces: list[dict[str, Any]] = []
        function_names: list[str | None] = []
        for index, (item, output) in enumerate(
            zip(dataset, outputs),
            start=1,
        ):
            raw_text = output_text(output)
            function_name = parse_function_name(raw_text, valid_names)
            function_names.append(function_name)
            traces.append(
                {
                    "case": index,
                    "emergency": item["emergency"],
                    "agent1_model": os.fspath(EDIT_MODEL_PATH),
                    "agent1_raw": raw_text,
                    "function": function_name,
                    "function_source": (
                        functions[function_name]
                        if function_name is not None
                        else None
                    ),
                    "agent2_model": os.fspath(
                        DECISION_COMBINED_MODELS_PATH
                    ),
                    "agent2_raw": None,
                }
            )
        return traces, function_names
    finally:
        if llm is not None:
            del llm
        if tokenizer is not None:
            del tokenizer
        release_vllm()


def run_agent2(
    dataset: list[dict[str, str]],
    functions: dict[str, str],
    import_source: str,
    function_names: list[str | None],
    traces: list[dict[str, Any]],
) -> dict[int, str]:
    """Use the merged LoRA model to repair Agent1's selected functions."""

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    tokenizer = None
    llm = None
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            DECISION_COMBINED_MODELS_PATH,
            trust_remote_code=True,
        )
        llm = LLM(
            model=os.fspath(DECISION_COMBINED_MODELS_PATH),
            dtype="auto",
            trust_remote_code=True,
            gpu_memory_utilization=0.9,
            seed=SEED,
        )

        inputs: list[str] = []
        case_indices: list[int] = []
        for case_index, (item, function_name) in enumerate(
            zip(dataset, function_names)
        ):
            if function_name is None:
                continue
            relevant_source = "\n\n".join(
                (import_source, functions[function_name])
            ).strip()
            inputs.append(
                build_chat_input(
                    tokenizer,
                    prompts.SYSTEM_PROMPT,
                    prompts.USER_PROMPT.format(
                        EMERGENCY_SITUATIONS=item["emergency"],
                        ORIGINAL_CODE=relevant_source,
                    ),
                )
            )
            case_indices.append(case_index)

        outputs = llm.generate(
            inputs,
            SamplingParams(
                temperature=0.0,
                top_p=1.0,
                max_tokens=AGENT2_MAX_TOKENS,
                seed=SEED,
            ),
        ) if inputs else []
        if len(outputs) != len(inputs):
            raise RuntimeError("Agent2输出数量与输入数量不一致")

        generated: dict[int, str] = {}
        for case_index, output in zip(case_indices, outputs):
            raw_text = output_text(output)
            traces[case_index]["agent2_raw"] = raw_text
            generated[case_index] = clean_agent2_code(raw_text)
        return generated
    finally:
        if llm is not None:
            del llm
        if tokenizer is not None:
            del tokenizer
        release_vllm()


def run_experiment() -> int:
    """Run one full test-set pass with the two configured models."""

    seed_everything(SEED)
    dataset = load_dataset(DATASET_FILE)
    functions, import_source = load_source_functions(SOURCE_FILE)
    prepare_out_dir(OUT_DIR)

    traces, function_names = run_agent1(dataset, functions)
    generated = run_agent2(
        dataset,
        functions,
        import_source,
        function_names,
        traces,
    )

    for case_index in range(len(dataset)):
        function_code = generated.get(case_index, "")
        module_parts = [
            part for part in (import_source, function_code) if part
        ]
        (OUT_DIR / f"result_{case_index + 1}.py").write_text(
            "\n\n".join(module_parts).strip() + "\n",
            encoding="utf-8",
        )

    (OUT_DIR / "agent_traces.json").write_text(
        json.dumps(traces, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(dataset)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Agent1使用原始Qwen，Agent2使用LoRA合并模型运行MAED。"
        )
    )
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="仅合并LoRA并保存模型，不运行测试集。",
    )
    parser.add_argument(
        "--force-merge",
        action="store_true",
        help="即使合并模型已存在，也重新执行合并。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    combined_path = merge_lora_model(force=args.force_merge)
    print(f"LoRA合并模型：{combined_path}")
    if not args.merge_only:
        experiment_started_at = time.perf_counter()
        case_count = run_experiment()
        experiment_time = time.perf_counter() - experiment_started_at
        average_response_time = (
            experiment_time / case_count if case_count else 0.0
        )
        metrics = {
            "cases": case_count,
            "experiment_time": experiment_time,
            "average_response_time": average_response_time,
            "merge_time_included": False,
            "agent1_model": os.fspath(EDIT_MODEL_PATH),
            "agent2_model": os.fspath(DECISION_COMBINED_MODELS_PATH),
        }
        (OUT_DIR / "metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"推理结果：{OUT_DIR}")
        print(
            f"实验耗时：{experiment_time:.2f}s，"
            f"平均响应时间：{average_response_time:.4f}s"
        )


if __name__ == "__main__":
    main()
