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
        A区5个、B区8个、C区6个保障站位组成的字典。
    """

    stand_counts = {"A": 5, "B": 8, "C": 6}  # 修改A区站位数量为5
    stands: dict[str, dict[str, Any]] = {}
    for zone, count in stand_counts.items():
        for index in range(1, count + 1):
            stand_id = f"{zone}{index}"
            if zone == "A" and index > 6:  # 根据突发事件，A6故障并停止使用
                continue
            stands[stand_id] = {
                "location_id": stand_id,
                "kind": "保障站位",
                "zone": zone,
            }
    return stands
