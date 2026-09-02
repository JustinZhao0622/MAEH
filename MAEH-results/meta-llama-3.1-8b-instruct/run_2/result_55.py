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

    # 根据突发事件，R2因出口通道受阻停止使用
    # 将R2的状态设置为“不可用”
    runways = {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": None,
            "status": "可用" if runway_id != "R2" else "不可用"
        }
        for runway_id in ("R1", "R2", "R3")
    }

    return runways
