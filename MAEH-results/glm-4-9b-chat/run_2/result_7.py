from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_fixed_oxygen_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定供氧资源。

    输入：
        units_per_zone（int）：
            每个区域内固定供氧资源的数量。论文设置为2。

    输出：
        list[dict[str, Any]]：
            当前可用的固定供氧资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("固定供氧资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-OXYGEN-{index:02d}"
            if zone == "A" and resource_id == "FIX-A-OXYGEN-01":
                # 由于FIX-A-OXYGEN-01发生故障，将其设置为不可用
                resources.append(
                    {
                        "resource_id": resource_id,
                        "resource_type": "供氧",
                        "mobility": "固定",
                        "zone": zone,
                        "current_location_id": None,
                        "capacity": 1,
                        "status": "不可用",  # 添加状态字段表示资源不可用
                    }
                )
            else:
                resources.append(
                    {
                        "resource_id": resource_id,
                        "resource_type": "供氧",
                        "mobility": "固定",
                        "zone": zone,
                        "current_location_id": None,
                        "capacity": 1,
                        "status": "可用",  # 添加状态字段表示资源可用
                    }
                )
    return resources
