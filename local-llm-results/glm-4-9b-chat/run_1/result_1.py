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
        if required_resource != "供电" or required_resource is None
    }  # Exclude tasks that require "供电" resource due to the emergency


def initialize_landing_points() -> dict[str, dict[str, Any]]:
    """初始化2个着陆点。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        包含L1和L2的着陆点字典。
    """

    return {
        point_id: {
            "location_id": point_id,
            "kind": "着陆点",
            "zone": None,
        }
        for point_id in ("L1", "L2")
    }


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


def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """初始化舰载机并依次放置在给定保障站位。

    输入：
        aircraft_count（int）：
            需要初始化的舰载机数量。
        support_stand_ids（Sequence[str]）：
            可供舰载机初始停放的保障站位编号序列。

    输出：
        dict[str, dict[str, Any]]：
        以舰载机编号为键的舰载机状态字典。

    异常：
        ValueError：
            舰载机数量小于0，或者超过给定保障站位数量时抛出。
    """

    if aircraft_count < 0:
        raise ValueError("aircraft_count不能小于0")
    if aircraft_count > len(support_stand_ids):
        raise ValueError("舰载机数量不能超过可用保障站位数量")

    aircraft: dict[str, dict[str, Any]] = {}
    for index in range(1, aircraft_count + 1):
        aircraft_id = f"AC{index:02d}"
        planned_arrival_time = 8 * 60 + (index - 1) * 3
        aircraft[aircraft_id] = {
            "aircraft_id": aircraft_id,
            "location_id": support_stand_ids[index - 1],
            "planned_arrival_time": float(planned_arrival_time),
            "actual_arrival_time": float(planned_arrival_time),
        }
    return aircraft


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


# Modified function to exclude the faulty power resource
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
    exclude_resource_id = "FIX-A-POWER-01"
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-POWER-{index:02d}"
            if resource_id != exclude_resource_id:
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


# ... (Other functions remain unchanged)
