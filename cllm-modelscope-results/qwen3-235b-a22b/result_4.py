"""MAEH舰载航空枢纽资源初始化函数。
"""

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
    }


def initialize_landing_points() -> dict[str, dict[str, Any]]:
    """初始化2个着陆点.

    输入:
        无.

    输出:
        dict[str, dict[str, Any]]:
        包含L1和L2的着陆点字典.
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
    """初始化A、B、C三区共19个保障站位.

    输入:
        无.

    输出:
        dict[str, dict[str, Any]]:
        A区6个、B区8个、C区5个保障站位组成的字典.
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
    """初始化3条起飞跑道.

    输入:
        无.

    输出:
        dict[str, dict[str, Any]]:
        包含R1、R2和R3的起飞跑道字典.
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
    """初始化舰载机并依次放置在给定保障站位.

    输入:
        aircraft_count（int）：
            需要初始化的舰载机数量.
        support_stand_ids（Sequence[str]）：
            可供舰载机初始停放的保障站位编号序列.

    输出:
        dict[str, dict[str, Any]]：
        以舰载机编号为键的舰载机状态字典.

    异常:
        ValueError：
            舰载机数量小于0，或者超过给定保障站位数量时抛出.
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
    """初始化A、B、C三区当前可用的固定供电资源.

    输入:
        units_per_zone（int）：
            每个区域内固定供电资源的数量.论文设置为2.

    输出:
        list[dict[str, Any]]：
            当前可用的固定供电资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
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


def initialize_fixed_hydraulic_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定液压资源.

    输入:
        units_per_zone（int）：
            每个区域内固定液压资源的数量.论文设置为2.

    输出:
        list[dict[str, Any]]：
            当前可用的固定液压资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
    """

    if units_per_zone < 0:
        raise ValueError("固定液压资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-HYDRAULIC-{index:02d}"
            # 特情处理：A区固定液压资源FIX-A-HYDRAULIC-02发生故障，当前不可用
            if resource_id == "FIX-A-HYDRAULIC-02":
                continue
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


def initialize_fixed_fuel_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定燃油资源.

    输入:
        units_per_zone（int）：
            每个区域内固定燃油资源的数量.论文设置为2.

    输出:
        list[dict[str, Any]]：
            当前可用的固定燃油资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
    """

    if units_per_zone < 0:
        raise ValueError("固定燃油资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-FUEL-{index:02d}"
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "燃油",
                    "mobility": "固定",
                    "zone": zone,
                    "current_location_id": None,
                    "capacity": 1,
                }
            )
    return resources


def initialize_fixed_oxygen_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定供氧资源.

    输入:
        units_per_zone（int）：
            每个区域内固定供氧资源的数量.论文设置为2.

    输出:
        list[dict[str, Any]]：
            当前可用的固定供氧资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
    """

    if units_per_zone < 0:
        raise ValueError("固定供氧资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-OXYGEN-{index:02d}"
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "供氧",
                    "mobility": "固定",
                    "zone": zone,
                    "current_location_id": None,
                    "capacity": 1,
                }
            )
    return resources


def initialize_mobile_power_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动供电资源.

    输入:
        resource_count（int）：
            移动供电资源的数量.
        initial_location_id（str）：
            移动供电资源的初始位置编号.

    输出:
        list[dict[str, Any]]：
            当前可用的移动供电资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
    """

    if resource_count < 0:
        raise ValueError("移动供电资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-POWER-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "供电",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources


def initialize_mobile_hydraulic_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动液压资源.

    输入:
        resource_count（int）：
            移动液压资源的数量.
        initial_location_id（str）：
            移动液压资源的初始位置编号.

    输出:
        list[dict[str, Any]]：
            当前可用的移动液压资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
    """

    if resource_count < 0:
        raise ValueError("移动液压资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-HYDRAULIC-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "液压",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources


def initialize_mobile_fuel_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动燃油资源.

    输入:
        resource_count（int）：
            移动燃油资源的数量.
        initial_location_id（str）：
            移动燃油资源的初始位置编号.

    输出:
        list[dict[str, Any]]：
            当前可用的移动燃油资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
    """

    if resource_count < 0:
        raise ValueError("移动燃油资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-FUEL-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "燃油",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources


def initialize_mobile_oxygen_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动供氧资源.

    输入:
        resource_count（int）：
            移动供氧资源的数量.
        initial_location_id（str）：
            移动供氧资源的初始位置编号.

    输出:
        list[dict[str, Any]]：
            当前可用的移动供氧资源列表.

    异常:
        ValueError：
            资源数量小于0时抛出.
    """

    if resource_count < 0:
        raise ValueError("移动供氧资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-OXYGEN-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "供氧",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources


def initialize_tow_tractors(
    tow_tractor_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的牵引车.

    输入:
        tow_tractor_count（int）：
            牵引车数量.
        initial_location_id（str）：
            牵引车初始位置编号.

    输出:
        list[dict[str, Any]]：
            当前可用的牵引车资源列表.

    异常:
        ValueError：
            牵引车数量小于0时抛出.
    """

    if tow_tractor_count < 0:
        raise ValueError("牵引车数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, tow_tractor_count + 1):
        resource_id = f"MOB-TOW-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "牵引车",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources


def create_route_segment(
    start_location_id: str,
    end_location_id: str,
    distance: float = 1.0,
) -> dict[str, Any]:
    """创建一条单向路径段.

    输入:
        start_location_id（str）：
            路径起点编号.
        end_location_id（str）：
            路径终点编号.
        distance（float）：
            路径距离，默认值为1.0.

    输出:
        dict[str, Any]：
        包含路径编号、起点、终点、距离和通行状态的字典.

    异常:
        ValueError：
            起点与终点相同，或者距离不大于0时抛出.
    """

    if start_location_id == end_location_id:
        raise ValueError("路径段的起点和终点不能相同")
    if distance <= 0:
        raise ValueError("路径距离必须大于0")

    segment_id = f"SEG-{start_location_id}-{end_location_id}"
    return {
        "segment_id": segment_id,
        "start_location_id": start_location_id,
        "end_location_id": end_location_id,
        "distance": float(distance),
        "status": "可通行",
        "blocked_reason": None,
    }
