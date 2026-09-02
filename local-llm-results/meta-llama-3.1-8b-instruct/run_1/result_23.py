from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_supply_resources() -> dict[str, dict[str, Any]]:
    """初始化可用的供氧资源。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        包含可用的供氧资源的字典。
    """
    supply_zone='A'
    resources: list[dict[str, Any]] = []
    for index in range(1, 3): # 取代C区资源 
        resource_id = f"FIX-{supply_zone}-OXYGEN-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "供氧",
                "mobility": "固定",
                "zone": supply_zone,
                "current_location_id": None,
                "capacity": 1,
            }
        )
    return {"supply_zone": resources[0]}

supply_oxygen_resources = initialize_fixed_oxygen_resources(units_per_zone=2)

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
    global supply_oxygen_resources
    return supply_oxygen_resources
