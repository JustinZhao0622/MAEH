"""Shared benchmark utilities for agent-framework comparisons."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
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
BASE_RESULT_DIR = PROJECT_ROOT / "framework-results"
RUN_INDEX = 1
TEMPERATURE = 0.8
TOP_P = 1.0
MAX_TOKENS = 8192
REQUEST_TIMEOUT = 600
VLLM_PYTHON = os.getenv(
    "MAEH_VLLM_PYTHON",
    "/root/anaconda3/envs/llm/bin/python",
)

MODELS: tuple[dict[str, str], ...] = (
    {
        "name": "Qwen2.5-Coder-7B-Instruct",
        "path": "/data/huggingface/Qwen2.5-Coder-7B-Instruct",
        "slug": "qwen2.5-coder-7b-instruct",
    },
)


@dataclass
class RepairResult:
    """One framework's output and accounting for a single test case."""

    code: str
    model_calls: int
    trace: dict[str, Any]


@dataclass
class BenchmarkMetrics:
    """Metrics written after one model completes one framework run."""

    framework: str
    model: str
    model_path: str
    run: int
    cases: int
    generated: int
    failed: int
    model_calls: int
    startup_time: float
    time: float
    average_response_time: float
    out_dir: str


def load_dataset(limit: int = 0) -> list[dict[str, str]]:
    """Load and normalize the single-emergency benchmark."""

    with open(DATASET_FILE, "r", encoding="utf-8") as file:
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
    return dataset[:limit] if limit > 0 else dataset


def build_repair_task(emergency: str, source: str | None = None) -> str:
    """Build the common task given to every framework."""

    original_code = source if source is not None else prompts.ORIGINAL_CODE
    user_prompt = prompts.USER_PROMPT.format(
        EMERGENCY_SITUATIONS=emergency,
        ORIGINAL_CODE=original_code,
    )
    return (
        f"{prompts.SYSTEM_PROMPT.strip()}\n\n"
        f"{user_prompt.strip()}"
    )


def extract_fenced_code(text: str) -> str | None:
    """Return the longest Python-compatible fenced block."""

    matches = re.findall(
        r"```(?:python|py)?\s*\n?(.*?)```",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not matches:
        return None
    return max((match.strip() for match in matches), key=len)


def clean_code(text: str) -> str:
    """Remove response prose while preserving generated Python."""

    fenced = extract_fenced_code(text)
    if fenced is not None:
        return fenced

    lines = text.strip().splitlines()
    prefixes = (
        "from ",
        "import ",
        "def ",
        "async def ",
        '"""',
        "'''",
    )
    for index, line in enumerate(lines):
        if line.lstrip().startswith(prefixes):
            return "\n".join(lines[index:]).strip()
    return text.strip()


def prepare_output_dir(framework: str, model_slug: str) -> Path:
    """Create a clean result directory for one framework/model run."""

    out_dir = (
        BASE_RESULT_DIR
        / framework
        / model_slug
        / f"run_{RUN_INDEX}"
    )
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def selected_models(model_slug: str) -> list[dict[str, str]]:
    """Return all models or the selected common base model."""

    if model_slug == "all":
        return [dict(model) for model in MODELS]
    for model in MODELS:
        if model["slug"] == model_slug:
            return [dict(model)]
    raise ValueError(f"未知模型：{model_slug}")


def add_common_arguments(
    parser: argparse.ArgumentParser,
    default_port: int,
) -> None:
    """Add identical benchmark and local-server options."""

    parser.add_argument(
        "--model",
        choices=["all", *(model["slug"] for model in MODELS)],
        default="all",
        help="要测试的基础模型；当前仅配置Qwen2.5-Coder-7B-Instruct。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="只运行前N条；0表示完整100条测试集。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help="脚本自动启动的vLLM OpenAI服务端口。",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="复用已经启动的OpenAI兼容服务，例如http://127.0.0.1:8000/v1。",
    )
    parser.add_argument(
        "--server-start-timeout",
        type=float,
        default=600.0,
        help="等待本地vLLM服务完成模型加载的秒数。",
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.9,
        help="自动启动vLLM时使用的GPU显存比例。",
    )
    parser.add_argument(
        "--max-model-len",
        type=int,
        default=32768,
        help="自动启动vLLM时设置的最大上下文长度。",
    )


def validate_common_arguments(args: argparse.Namespace) -> None:
    """Reject ambiguous external-server and model combinations."""

    if args.limit < 0:
        raise ValueError("--limit不能小于0")
    if args.base_url and args.model == "all":
        raise ValueError(
            "使用--base-url时必须通过--model指定该服务加载的模型"
        )


class VLLMServer(AbstractContextManager["VLLMServer"]):
    """Start one local vLLM OpenAI server, or reuse an external endpoint."""

    def __init__(
        self,
        model: dict[str, str],
        *,
        port: int,
        external_base_url: str,
        startup_timeout: float,
        gpu_memory_utilization: float,
        max_model_len: int,
    ):
        self.model = model
        self.port = port
        self.external_base_url = external_base_url.rstrip("/")
        self.startup_timeout = startup_timeout
        self.gpu_memory_utilization = gpu_memory_utilization
        self.max_model_len = max_model_len
        self.process: subprocess.Popen[str] | None = None
        self.startup_time = 0.0

    @property
    def base_url(self) -> str:
        if self.external_base_url:
            return self.external_base_url
        return f"http://127.0.0.1:{self.port}/v1"

    @property
    def health_url(self) -> str:
        return f"{self.base_url.removesuffix('/v1')}/health"

    def _healthy(self) -> bool:
        try:
            with urllib.request.urlopen(
                self.health_url,
                timeout=2,
            ) as response:
                return 200 <= response.status < 300
        except (OSError, urllib.error.URLError):
            return False

    def _wait_until_ready(self) -> None:
        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self._healthy():
                return
            if self.process is not None and self.process.poll() is not None:
                raise RuntimeError(
                    "vLLM服务启动失败，退出码="
                    f"{self.process.returncode}"
                )
            time.sleep(2)
        raise TimeoutError(
            f"等待vLLM服务超时：{self.health_url}"
        )

    def __enter__(self) -> "VLLMServer":
        started_at = time.perf_counter()
        if not self.external_base_url:
            command = [
                VLLM_PYTHON,
                "-m",
                "vllm.entrypoints.openai.api_server",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--model",
                self.model["path"],
                "--served-model-name",
                self.model["slug"],
                "--trust-remote-code",
                "--dtype",
                "auto",
                "--gpu-memory-utilization",
                str(self.gpu_memory_utilization),
                "--max-model-len",
                str(self.max_model_len),
                "--seed",
                str(SEED),
            ]
            self.process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                start_new_session=True,
            )
        self._wait_until_ready()
        self.startup_time = time.perf_counter() - started_at
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.process is not None and self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=10)


def make_server(
    args: argparse.Namespace,
    model: dict[str, str],
) -> VLLMServer:
    """Create the common local-model server context manager."""

    return VLLMServer(
        model,
        port=args.port,
        external_base_url=args.base_url,
        startup_timeout=args.server_start_timeout,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
    )


def write_result(out_dir: Path, index: int, code: str) -> None:
    """Write one generated Python module."""

    (out_dir / f"result_{index}.py").write_text(
        code + ("\n" if code else ""),
        encoding="utf-8",
    )


def write_trace(out_dir: Path, traces: list[dict[str, Any]]) -> None:
    """Persist framework conversations or tool trajectories."""

    (out_dir / "traces.json").write_text(
        json.dumps(traces, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def finish_benchmark(
    *,
    framework: str,
    model: dict[str, str],
    out_dir: Path,
    case_times: list[float],
    model_calls: int,
    failed: int,
    startup_time: float,
) -> BenchmarkMetrics:
    """Write the common generation and timing summary."""

    framework_time = sum(case_times)
    cases = len(case_times)
    metrics = BenchmarkMetrics(
        framework=framework,
        model=model["name"],
        model_path=model["path"],
        run=RUN_INDEX,
        cases=cases,
        generated=cases - failed,
        failed=failed,
        model_calls=model_calls,
        startup_time=startup_time,
        time=framework_time,
        average_response_time=(
            framework_time / cases if cases else 0.0
        ),
        out_dir=os.fspath(out_dir),
    )
    (out_dir / "metrics.json").write_text(
        json.dumps(
            asdict(metrics),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return metrics


def safe_error(error: BaseException) -> str:
    """Return a compact error suitable for result traces."""

    return (
        f"{type(error).__name__}: {error}"
        .replace("\n", " ")
        [:1200]
    )
