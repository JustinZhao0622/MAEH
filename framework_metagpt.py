"""Benchmark a MetaGPT sequential SOP on the MAEH repair test set."""

from __future__ import annotations

import argparse
import asyncio
import time
from typing import Any

import framework_common as common


FRAMEWORK = "metagpt"


def dependency_error() -> RuntimeError:
    return RuntimeError(
        "缺少MetaGPT依赖。请安装：pip install metagpt"
    )


async def repair_case(
    metagpt_config: Any,
    emergency: str,
) -> common.RepairResult:
    """Run MetaGPT's analyze, implement, and review Actions by order."""

    try:
        from metagpt.actions import Action
        from metagpt.roles import Role
        from metagpt.schema import Message
    except ImportError as error:
        raise dependency_error() from error

    task_text = common.build_repair_task(emergency)

    class AnalyzeRepair(Action):
        name: str = "AnalyzeRepair"

        async def run(self, task: str) -> str:
            prompt = f"""
你是MetaGPT软件团队的代码分析人员。请分析下面的特情修复任务，明确：
1. 受影响函数及其返回契约；
2. 目标实体在修复后应该被删除、标记不可用还是更新时间；
3. 其他实体和函数必须保持的行为；
4. 实现时容易造成评测失败的风险。

只输出简洁的修复方案，不输出完整代码。

任务：
{task}
""".strip()
            return await self._aask(prompt)

    class ImplementRepair(Action):
        name: str = "ImplementRepair"

        async def run(self, task: str, analysis: str) -> str:
            prompt = f"""
你是MetaGPT软件团队的实现工程师。根据原始任务和分析方案完成代码修复。
严格遵守任务中的修改范围和输出要求，只输出修改后的完整Python代码。
不要输出Markdown、分析或说明。

分析方案：
{analysis}

原始任务：
{task}
""".strip()
            return await self._aask(prompt)

    class ReviewRepair(Action):
        name: str = "ReviewRepair"

        async def run(
            self,
            task: str,
            analysis: str,
            candidate: str,
        ) -> str:
            prompt = f"""
你是MetaGPT软件团队的最终审查人员。检查候选代码是否准确处置特情，
是否保留原始imports、函数、参数和返回结构，并检查语法和无关修改。
直接修正所有问题。最终只输出一份可直接运行的完整Python代码，不要
输出Markdown、审查意见或其他文本。

分析方案：
{analysis}

原始任务：
{task}

候选代码：
{candidate}
""".strip()
            return await self._aask(prompt)

    class RepairRole(Role):
        name: str = "MAEHEngineer"
        profile: str = "MAEH Repair Engineer"
        goal: str = "按照标准作业流程生成正确的特情修复代码"
        constraints: str = "只做最小修改并输出完整可运行代码"
        task_text: str = ""
        analysis_text: str = ""
        candidate_code: str = ""
        final_code: str = ""
        call_count: int = 0

        def __init__(self, task: str, **kwargs):
            super().__init__(**kwargs)
            self.task_text = task
            self.set_actions(
                [AnalyzeRepair, ImplementRepair, ReviewRepair]
            )
            self._set_react_mode(react_mode="by_order")

        async def _act(self) -> Message:
            todo = self.rc.todo
            if isinstance(todo, AnalyzeRepair):
                result = await todo.run(self.task_text)
                self.analysis_text = result
            elif isinstance(todo, ImplementRepair):
                result = await todo.run(
                    self.task_text,
                    self.analysis_text,
                )
                self.candidate_code = result
            elif isinstance(todo, ReviewRepair):
                result = await todo.run(
                    self.task_text,
                    self.analysis_text,
                    self.candidate_code,
                )
                self.final_code = result
            else:
                raise RuntimeError(f"未知MetaGPT Action：{todo}")

            self.call_count += 1
            message = Message(
                content=result,
                role=self.profile,
                cause_by=type(todo),
            )
            self.rc.memory.add(message)
            return message

    role = RepairRole(task=task_text, config=metagpt_config)
    result = await role.run(task_text)
    final_text = role.final_code or result.content
    memories = []
    for message in role.get_memories():
        memories.append(
            {
                "role": message.role,
                "cause_by": str(message.cause_by),
                "content": message.content,
            }
        )

    return common.RepairResult(
        code=common.clean_code(final_text),
        model_calls=role.call_count,
        trace={
            "emergency": emergency,
            "analysis": role.analysis_text,
            "candidate": role.candidate_code,
            "final": final_text,
            "messages": memories,
        },
    )


async def run_model(
    args: argparse.Namespace,
    model: dict[str, str],
    dataset: list[dict[str, str]],
) -> None:
    """Run one common base model through the MetaGPT SOP."""

    try:
        from metagpt.config2 import Config
    except ImportError as error:
        raise dependency_error() from error

    out_dir = common.prepare_output_dir(FRAMEWORK, model["slug"])
    traces: list[dict[str, Any]] = []
    case_times: list[float] = []
    model_calls = 0
    failures = 0

    server = common.make_server(args, model)
    with server:
        metagpt_config = Config.from_llm_config(
            {
                "api_type": "open_llm",
                "api_key": "EMPTY",
                "base_url": server.base_url,
                "model": model["slug"],
                "temperature": common.TEMPERATURE,
                "top_p": common.TOP_P,
                "max_token": common.MAX_TOKENS,
                "timeout": common.REQUEST_TIMEOUT,
                "stream": False,
                "seed": common.SEED,
                "calc_usage": False,
            }
        )

        for index, item in enumerate(dataset, start=1):
            started_at = time.perf_counter()
            try:
                repaired = await repair_case(
                    metagpt_config,
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
        description="使用MetaGPT SOP对MAEH特情修复进行统一框架评测。",
    )
    common.add_common_arguments(parser, default_port=18102)
    args = parser.parse_args()
    common.validate_common_arguments(args)

    dataset = common.load_dataset(args.limit)
    for model in common.selected_models(args.model):
        await run_model(args, model, dataset)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
