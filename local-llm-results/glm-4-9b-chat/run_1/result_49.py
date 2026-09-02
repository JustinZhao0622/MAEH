from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_support_tasks() -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
    task_rows = [
        # ... (existing task data)
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
    # Modify to handle the emergency situation where R2 is blocked
    runways = {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": None,
        }
        for runway_id in ("R1", "R2", "R3")
    }
    runways["R2"]["blocked"] = True  # Mark R2 as blocked due to the emergency
    return runways

def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
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

# ... (other functions remain unchanged)
