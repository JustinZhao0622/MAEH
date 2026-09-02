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
    for zone in ("A", "B"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-OXYGEN-{index:02d}"
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "供氧",
                    "mobility": "固定",
                    "zone": zone,
                    "current_location_id": None,
                    "capacity": 1,
                }
            )
    # 根据突发事件，C区固定供氧资源FIX-C-OXYGEN-01发生故障，当前不可用
    for resource in resources:
        if resource["resource_id"] == "FIX-C-OXYGEN-01":
            resource["current_location_id"] = "故障"
            resource["capacity"] = 0
    return resources
