from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_supply_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定供电资源。

    从C区中排除可用固定供电资源。

    输入：
        units_per_zone（int）：
            每个区域内固定供电资源的数量。

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
    for zone in ("A", "B"):
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


def initialize_fixed_oxygen_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定供氧资源。

    从C区排除可用固定供氧资源。

    输入：
        units_per_zone（int）：
            每个区域内固定供氧资源的数量。

    输出：
        list[dict[str, Any]]：
            当前可用的固定供氧资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("固定供氧资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B"):
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


def initialize_fixed_resources(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """初始化固定资源。

    输入：
        tasks（list[dict[str, Any]]）：
            作业列表。

    输出：
        list[dict[str, Any]]：
            当前可用固定资源列表。
    """

    fixed_power_resources = initialize_supply_resources(units_per_zone=2)
    fixed_oxygen_resources = initialize_fixed_oxygen_resources(units_per_zone=2)

    resources: list[dict[str, Any]] = fixed_power_resources + fixed_oxygen_resources

    # 根据作业需求动态调整资源数量
    for task in tasks:
        required_resource = task["required_resource"]
        if required_resource == "供电" and "MOB-POWER" not in [resource["resource_id"] for resource in resources]:
            resources.extend(initialize_mobile_power_resources(units_per_zone=1, initial_location_id=None))
        elif required_resource == "供氧" and "MOB-OXYGEN" not in [resource["resource_id"] for resource in resources]:
            resources.extend(initialize_mobile_oxygen_resources(units_per_zone=1, initial_location_id=None))

    return resources
