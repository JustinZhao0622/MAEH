from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from typing import Any, Sequence

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

    if aircraft_count < 0:
        raise ValueError("aircraft_count不能小于0")
    if aircraft_count > len(support_stand_ids):
        raise ValueError("舰载机数量不能超过可用保障站位数量")

    aircraft: dict[str, dict[str, Any]] = {}
    for index in range(1, aircraft_count + 1):
        aircraft_id = f"AC{index:02d}"
        planned_arrival_time = 8 * 60 + (index - 1) * 3
        actual_arrival_time = planned_arrival_time + 13  # 延迟13分钟
        aircraft[aircraft_id] = {
            "aircraft_id": aircraft_id,
            "location_id": support_stand_ids[index - 1],
            "planned_arrival_time": float(planned_arrival_time),
            "actual_arrival_time": float(actual_arrival_time),
        }
    return aircraft
