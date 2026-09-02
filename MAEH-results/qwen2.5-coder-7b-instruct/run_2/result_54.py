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
        runway_id (str)：跑道ID。
        status (dict[str, Any])：跑道状态。

    输出：
        无。
    """

    # 假设runway_status是一个全局变量，存储所有跑道的状态
    global runway_status
    runway_status[runway_id] = status

def check_runway_availability(runway_id: str) -> bool:
    """检查指定跑道是否可用。

    输入：
        runway_id (str)：跑道ID。

    输出：
        bool：跑道是否可用。
    """

    # 假设runway_status是一个全局变量，存储所有跑道的状态
    global runway_status
    return runway_status.get(runway_id, {}).get("zone") is None

def schedule_flight(flight_id: str, runway_id: str) -> None:
    """调度航班。

    输入：
        flight_id (str)：航班ID。
        runway_id (str)：跑道ID。

    输出：
        无。
    """

    if not check_runway_availability(runway_id):
        raise ValueError(f"跑道 {runway_id} 不可用")

    # 假设flight_status是一个全局变量，存储所有航班的状态
    global flight_status
    flight_status[flight_id] = {
        "runway_id": runway_id,
        "status": "调度中",
    }

# 初始化跑道状态
runway_status = initialize_runways()

# 更新跑道R1的状态
update_runway_status("R1", {"zone": "临时检查"})

# 调度航班
try:
    schedule_flight("F1", "R1")
except ValueError as e:
    print(e)
