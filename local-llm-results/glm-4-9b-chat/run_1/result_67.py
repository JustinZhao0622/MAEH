from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_support_tasks() -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_landing_points() -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_support_stands() -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_runways() -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_fixed_power_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_fixed_hydraulic_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_fixed_fuel_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_fixed_oxygen_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_mobile_power_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_mobile_hydraulic_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_mobile_fuel_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_mobile_oxygen_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def initialize_tow_tractors(
    tow_tractor_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    # Existing function body remains unchanged
    pass


def create_route_segment(
    start_location_id: str,
    end_location_id: str,
    distance: float = 1.0,
) -> dict[str, Any]:
    # Modify the existing function to handle the emergency situation
    segment_id = f"SEG-{start_location_id}-{end_location_id}"
    segment = {
        "segment_id": segment_id,
        "start_location_id": start_location_id,
        "end_location_id": end_location_id,
        "distance": float(distance),
        "status": "可通行",
        "blocked_reason": None,
    }

    # Check for the emergency situation L2 to B4
    if start_location_id == "L2" and end_location_id == "B4":
        segment["status"] = "不可通行"
        segment["blocked_reason"] = "局部区域受限"

    return segment
