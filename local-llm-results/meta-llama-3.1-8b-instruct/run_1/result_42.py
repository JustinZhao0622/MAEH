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

    # 因为起飞跑道R1因设备异常停止使用，所以需要更新起飞跑道列表，R1变成不可用状态
    return {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": None,
            "status": "不可用",  # 新增status字段，标记R1为不可用
        }
        for runway_id in ("R1", "R2", "R3")
    }
