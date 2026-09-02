from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from typing import Any

def initialize_runways() -> dict[str, dict[str, Any]]:
    """初始化3条起飞跑道。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        包含R1、R2和R3的起飞跑道字典。
    """

    return {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": "R3" if runway_id == "R3" else None,
        }
        for runway_id in ("R1", "R2", "R3")
    }
