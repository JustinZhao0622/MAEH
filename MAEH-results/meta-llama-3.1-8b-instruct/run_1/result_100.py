from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_support_stands() -> dict[str, dict[str, Any]]:
    """初始化A、B、C三区共19个保障站位。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        A区6个、B区7个、C区5个保障站位组成的字典。
    """

    stand_counts = {"A": 6, "B": 7, "C": 5}  # B区站位数量减少为7
    stands: dict[str, dict[str, Any]] = {}
    for zone, count in stand_counts.items():
        for index in range(1, count + 1):
            stand_id = f"{zone}{index}"
            if zone == "B" and index > 7:  # B区站位超过7号时跳过
                continue
            stands[stand_id] = {
                "location_id": stand_id,
                "kind": "保障站位",
                "zone": zone,
            }
    return stands
