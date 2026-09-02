from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_runways() -> dict[str, dict[str, Any]]:
    """初始化3条起飞跑道。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        包含R1、R2和R3的起飞跑道字典。
    """

    # 因为起飞跑道R3因区域内存在障碍物停止使用，所以把R3替换为R4
    return {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": None,
        }
        for runway_id in ("R1", "R2", "R4")
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

    # 检查是否有足够的保障站位
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

def initialize_hydraulic_resource_availability(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的液压资源。

    输入：
        units_per_zone（int）：
            每个区域内液压资源的数量。论文设置为2。

    输出：
        list[dict[str, Any]]：
            当前可用的液压资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("液压资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
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

def initialize_fixed_resources(
    units_per_zone: dict[str, int],
) -> dict[str, list[dict[str, Any]]]:
    """初始化固定资源。

    输入：
        units_per_zone（dict[str, int]）：
            每个区域内固定资源的数量。

    输出：
        dict[str, list[dict[str, Any]]]：
            固定资源列表。
    """

    fixed_resources: dict[str, list[dict[str, Any]]] = {
        "供电": initialize_fixed_power_resources(units_per_zone["供电"]),
        "液压": initialize_hydraulic_resource_availability(units_per_zone["液压"]),
        "燃油": initialize_fixed_fuel_resources(units_per_zone["燃油"]),
        "供氧": initialize_fixed_oxygen_resources(units_per_zone["供氧"]),
    }
    return fixed_resources

def initialize_mobile_resources(
    resource_count: dict[str, int],
    initial_location_id: str,
) -> dict[str, list[dict[str, Any]]]:
    """初始化移动资源。

    输入：
        resource_count（dict[str, int]）：
            移动资源数量。
        initial_location_id（str）：
            移动资源的初始位置编号。

    输出：
        dict[str, list[dict[str, Any]]]：
            移动资源列表。
    """

    mobile_resources: dict[str, list[dict[str, Any]]] = {
        "供电": initialize_mobile_power_resources(resource_count["供电"], initial_location_id),
        "液压": initialize_mobile_hydraulic_resources(resource_count["液压"], initial_location_id),
        "燃油": initialize_mobile_fuel_resources(resource_count["燃油"], initial_location_id),
        "供氧": initialize_mobile_oxygen_resources(resource_count["供氧"], initial_location_id),
    }
    return mobile_resources
