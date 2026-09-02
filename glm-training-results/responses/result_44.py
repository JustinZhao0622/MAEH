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

    runways = {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": None,
        }
        for runway_id in ("R1", "R2", "R3")
    }

    runways["R2"]["status"] = "关闭"
    runways["R2"]["reason"] = "牵引作业占用"

    return runways
