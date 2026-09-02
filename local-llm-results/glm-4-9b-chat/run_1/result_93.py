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
    }  # Exclude T03 and T05 tasks which are related to the power and hydraulic resources of A6


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
            if zone == "A" and index == 6:  # Exclude A6 stand
                continue
            stands[stand_id] = {
                "location_id": stand_id,
                "kind": "保障站位",
                "zone": zone,
            }
    return stands


def initialize_fixed_power_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定供电资源。

    输入：
        units_per_zone（int）：
            每个区域内固定供电资源的数量。论文设置为2。

    输出：
        list[dict[str, Any]]：
            当前可用的固定供电资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("固定供电资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            if zone == "A" and index == 6:  # Exclude power resources at A6
                continue
            resource_id = f"FIX-{zone}-POWER-{index:02d}"
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "供电",
                    "mobility": "固定",
                    "zone": zone,
                    "current_location_id": None,
                    "capacity": 1,
                }
            )
    return resources


def initialize_fixed_hydraulic_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定液压资源。

    输入：
        units_per_zone（int）：
            每个区域内固定液压资源的数量。论文设置为2。

    输出：
        list[dict[str, Any]]：
            当前可用的固定液压资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("固定液压资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            if zone == "A" and index == 6:  # Exclude hydraulic resources at A6
                continue
            resource_id = f"FIX-{zone}-HYDRAULIC-{index:02d}"
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "液压",
                    "mobility": "固定",
                    "zone": zone,
                    "current_location_id": None,
                    "capacity": 1,
                }
            )
    return resources


# The rest of the functions remain unchanged

# The rest of the code remains unchanged
