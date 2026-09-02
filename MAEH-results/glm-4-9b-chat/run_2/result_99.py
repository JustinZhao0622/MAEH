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
        A区6个、B区7个、C区5个保障站位组成的字典，B6站位因故障被排除。
    """

    stand_counts = {"A": 6, "B": 7, "C": 5}  # 修改B区的站位数量为7，排除B6站位
    stands: dict[str, dict[str, Any]] = {}
    for zone, count in stand_counts.items():
        for index in range(1, count + 1):
            stand_id = f"{zone}{index}"
            if stand_id != "B6":  # 排除B6站位
                stands[stand_id] = {
                    "location_id": stand_id,
                    "kind": "保障站位",
                    "zone": zone,
                }
    return stands
