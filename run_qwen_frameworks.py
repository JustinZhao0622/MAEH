"""Run the three framework benchmarks sequentially on the shared Qwen model."""

from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_SLUG = "qwen2.5-coder-7b-instruct"
RUNS = (
    (
        "AutoGen",
        PROJECT_ROOT / ".venv-autogen" / "bin" / "python",
        PROJECT_ROOT / "framework_autogen.py",
    ),
    (
        "MetaGPT",
        PROJECT_ROOT / ".venv-metagpt" / "bin" / "python",
        PROJECT_ROOT / "framework_metagpt.py",
    ),
    (
        "Mini-swe-agent",
        Path("/root/anaconda3/envs/llm/bin/python"),
        PROJECT_ROOT / "framework_mini_swe_agent.py",
    ),
)


def main() -> None:
    for _, python, script in RUNS:
        command = [
            str(python),
            str(script),
            "--model",
            MODEL_SLUG,
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=False)


if __name__ == "__main__":
    main()
