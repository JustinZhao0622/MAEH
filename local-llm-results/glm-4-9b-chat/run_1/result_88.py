from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_support_tasks() -> dict[str, dict[str, Any]]:
    """初始化定义的14项舰载机保障作业。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        以作业编号为键的保障作业字典。每项作业包含作业编号、名称、
        所属阶段和所需资源类型。
    """

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
        ("T14", "放飞许可", "放飞确认", None),
    ]
    return {
        task_id: {
            "task_id": task_id,
            "name": name,
            "stage": stage,
            "required_resource": required_resource,
        }
        for task_id, name, stage, required_resource in task_rows
        if required_resource not in ("供电", "液压") or (required_resource in ("供电", "液压") and task_id != "T03" and task_id != "T05")
    }  # Exclude T03 and T05 tasks which are related to the power and hydraulic resources of A1


def initialize_support_stands() -> dict[str, dict[str, Any]]:
    """初始化A、B、C三区共19个保障站位。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        A区6个、B区8个、C区5个保障站位组成的字典。
    """

    stand_counts = {"A": 6, "B": 8, "C": 5}
    stands: dict[str, dict[str, Any]] = {}
    for zone, count in stand_counts.items():
        for index in range(1, count + 1):
            stand_id = f"{zone}{index}"
            stands[stand_id] = {
                "location_id": stand_id,
                "kind": "保障站位",
                "zone": zone,
            }
    return stands


def initialize_runways() -> dict[str, dict[str, Any]]:
    """初始化3条起飞跑道。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        包含R1、R2和R3的起飞跑道字典。
    """

    return {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": None,
        }
        for runway_id in ("R1", "R2", "R3")
    }
