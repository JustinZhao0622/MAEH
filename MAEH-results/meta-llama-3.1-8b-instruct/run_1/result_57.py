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

    # 根据突发事件，R1因维护作业占用停止使用
    # 修改R1的状态为“维护中”
    runways = {
        "R1": {
            "location_id": "R1",
            "kind": "维护跑道",
            "zone": "维护区",
        },
        "R2": {
            "location_id": "R2",
            "kind": "起飞跑道",
            "zone": None,
        },
        "R3": {
            "location_id": "R3",
            "kind": "起飞跑道",
            "zone": None,
        }
    }

    return runways
