from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """初始化舰载机并依次放置于给定保障站位。

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

    # 由于舰载机AC13出现延迟，更新其预计到达时间
    aircraft = initialize_aircraft_base(support_stand_ids, aircraft_count)
    aircraft["AC13"]["planned_arrival_time"] = 8 * 60 + 38
    return aircraft

def initialize_aircraft_base(
    support_stand_ids: Sequence[str],
    aircraft_count: int,
) -> dict[str, dict[str, Any]]:
    # ... (同原函数代码)
