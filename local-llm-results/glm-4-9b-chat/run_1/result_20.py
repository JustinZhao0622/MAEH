from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_support_tasks() -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
    task_rows = [
        # ... (existing task rows)
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
    # Existing function body remains unchanged
    return {
        point_id: {
            "location_id": point_id,
            "kind": "着陆点",
            "zone": None,
        }
        for point_id in ("L1", "L2")
    }

def initialize_support_stands() -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
    # ... (existing aircraft initialization logic)

    return aircraft

def initialize_fixed_power_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
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
    # Modify to reflect the emergency situation
    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-HYDRAULIC-{index:02d}"
            if zone == "C" and index == 2:
                # Simulate the affected resource as unavailable
                resources.append({
                    "resource_id": resource_id,
                    "resource_type": "液压",
                    "mobility": "固定",
                    "zone": zone,
                    "current_location_id": None,
                    "capacity": 0,  # Simulate the resource as not available
                    "status": "故障"
                })
            else:
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
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
    # Existing function body remains unchanged
    # ... (existing route segment creation logic)
    return {
        "segment_id": segment_id,
        "start_location_id": start_location_id,
        "end_location_id": end_location_id,
        "distance": float(distance),
        "status": "可通行",
        "blocked_reason": None,
    }
