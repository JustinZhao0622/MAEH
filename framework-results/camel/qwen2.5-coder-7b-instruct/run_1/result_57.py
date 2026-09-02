from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_runways() -> dict[str, dict[str, Any]]:
    """初始化3条起飞跑道。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        包含R1、R2和R3的起飞跑道字典。
    """

    return {
        "R1": {
            "location_id": "R1",
            "kind": "起飞跑道",
            "zone": None,
            "status": "维护中"
        },
        "R2": {
            "location_id": "R2",
            "kind": "起飞跑道",
            "zone": None,
            "status": "可用"
        },
        "R3": {
            "location_id": "R3",
            "kind": "起飞跑道",
            "zone": None,
            "status": "可用"
        }
    }
