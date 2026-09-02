from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_support_tasks() -> dict[str, dict[str, Any]]:
    # ... 保持不变 ...


def initialize_landing_points() -> dict[str, dict[str, Any]]:
    # ... 保持不变 ...


def initialize_support_stands() -> dict[str, dict[str, Any]]:
    # ... 保持不变 ...


def initialize_runways() -> dict[str, dict[str, Any]]:
    # ... 保持不变 ...


def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    # ... 保持不变 ...


def initialize_fixed_power_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
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
    if units_per_zone < 0:
        raise ValueError("固定液压资源数量不能小于0")

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


def initialize_fixed_fuel_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
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
    if resource_count < 0:
        raise ValueError("移动供电资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-POWER-{index:02d}"
        if resource_id != "MOB-POWER-03":
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
    # ... 保持不变 ...
