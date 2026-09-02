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

    # 假设runway_status_dict是存储跑道状态的全局变量
    global runway_status_dict
    runway_status_dict[runway_id] = status

def check_runway_availability(runway_id: str) -> bool:
    """检查指定跑道是否可用。

    输入：
        runway_id (str)：跑道ID。

    输出：
        bool：跑道是否可用。
    """

    # 假设runway_status_dict是存储跑道状态的全局变量
    global runway_status_dict
    return runway_status_dict.get(runway_id, {}).get("zone") is None

# 初始化跑道状态
runway_status_dict = initialize_runways()

# 更新R1跑道状态为不可用
update_runway_status("R1", {"zone": "作业冲突"})

# 检查R1跑道是否可用
if not check_runway_availability("R1"):
    print("R1跑道因区域内存在作业冲突停止使用")
else:
    print("R1跑道可用")
