from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_support_tasks() -> dict[str, dict[str, Any]]:
    # 修改位置B6的作业为不可用
    task_rows = [
        ("T01", "机位确认", "基础准备", None),
        ("T02", "外观检查", "基础准备", None),
        ("T03", "供电接入", "基础准备", "供电"),
        ("T04", "通信测试", "基础准备", None),
        ("T05", "液压检查", "基础准备", "液压"),
        ("T06", "燃油加注", "保障实施", "燃油"),
        ("T07", "氧气补给", "保障实施", "供氧"),
        ("T08", "弹药装载", "保障实施", None),
        ("T09", "航电检测", "保障实施", None),
        ("T10", "参数校准", "保障实施", None),
        ("T11", "安全复核", "放飞确认", None),
        ("T12", "挂载确认", "放飞确认", None),
        ("T13", "放飞前检查", "放飞确认", None),
        # 删除位置B6的作业编号为T06的作业
        # ("T14", "放飞许可", "放飞确认", None),
    ]
    return {
        task_id: {
            "task_id": task_id,
            "name": name,
            "stage": stage,
            "required_resource": required_resource,
        }
        for task_id, name, stage, required_resource in task_rows
    }

# 其他函数保持不变，不进行任何修改
