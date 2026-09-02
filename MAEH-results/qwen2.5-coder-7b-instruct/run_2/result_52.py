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
            "zone": None,
        }
        for runway_id in ("R1", "R2", "R3")
    }

def update_runway_status(runway_id: str, status: dict[str, Any]) -> None:
    """更新指定跑道的状态。

    输入：
        runway_id (str)：跑道编号。
        status (dict[str, Any])：跑道状态。

    输出：
        无。
    """

    # 假设 runway_status 是一个全局变量，存储所有跑道的状态
    global runway_status
    runway_status[runway_id] = status

def handle_emergency_situation() -> None:
    """处理起飞跑道R2因道面受到污染停止使用的情况。

    输入：
        无。

    输出：
        无。
    """

    # 假设 runway_status 是一个全局变量，存储所有跑道的状态
    global runway_status

    # 更新跑道R2的状态
    update_runway_status("R2", {
        "location_id": "R2",
        "kind": "起飞跑道",
        "zone": None,
        "status": "停止使用"
    })

# 初始化跑道状态
runway_status = initialize_runways()

# 处理突发事件
handle_emergency_situation()
