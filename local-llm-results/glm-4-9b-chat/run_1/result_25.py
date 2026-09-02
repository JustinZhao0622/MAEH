from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_support_tasks() -> dict[str, dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_landing_points() -> dict[str, dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_support_stands() -> dict[str, dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_runways() -> dict[str, dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_fixed_power_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_fixed_hydraulic_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_fixed_fuel_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_fixed_oxygen_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_mobile_power_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # Since MOB-POWER-02 is out of service, we remove one unit from the list
    if resource_count > 0:
        resources: list[dict[str, Any]] = []
        for index in range(1, resource_count + 1):
            resource_id = f"MOB-POWER-{index:02d}"
            if index == 2:  # Skip the faulty resource
                continue
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
    else:
        raise ValueError("移动供电资源数量不能小于0")


def initialize_mobile_hydraulic_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_mobile_fuel_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_mobile_oxygen_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def initialize_tow_tractors(
    tow_tractor_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # ... (No changes required for this function)


def create_route_segment(
    start_location_id: str,
    end_location_id: str,
    distance: float = 1.0,
) -> dict[str, Any]:
    # ... (No changes required for this function)
