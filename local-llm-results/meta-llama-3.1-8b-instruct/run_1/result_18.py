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


def initialize_fixed_resources(tasks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    supply_resources = initialize_supply_resources()
    oxygen_resources = initialize_fixed_oxygen_resources()
    return supply_resources + oxygen_resources


def initialize_fixed_resources_with_emergency_situation(tasks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """
    根据突发事件，排除可用固定供电和供氧资源中的C区资源。
    """

    return initialize_fixed_resources(tasks)
