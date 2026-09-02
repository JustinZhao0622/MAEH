from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence


def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
    delayed_arrival: bool = False,
) -> dict[str, dict[str, Any]]:
    if delayed_arrival:
        # 根据突发事件调整舰载机到达时间
        delay_minutes = 4
        initial_arrival_time = 8 * 60 + 39
        aircraft_arrival_time = initial_arrival_time + delay_minutes * 60
    else:
        # 根据原有逻辑计算舰载机到达时间
        aircraft_arrival_time = 8 * 60 + (aircraft_count - 1) * 3

    if aircraft_count < 0:
        raise ValueError("aircraft_count不能小于0")
    if aircraft_count > len(support_stand_ids):
        raise ValueError("舰载机数量不能超过可用保障站位数量")

    aircraft: dict[str, dict[str, Any]] = {}
    for index in range(1, aircraft_count + 1):
        aircraft_id = f"AC{index:02d}"
        aircraft[aircraft_id] = {
            "aircraft_id": aircraft_id,
            "location_id": support_stand_ids[index - 1],
            "planned_arrival_time": float(aircraft_arrival_time),
            "actual_arrival_time": float(aircraft_arrival_time),
        }
    return aircraft
