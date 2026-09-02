from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_fixed_fuel_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定燃油资源。

    输入：
        units_per_zone（int）：
            每个区域内固定燃油资源的数量。论文设置为2。

    输出：
        list[dict[str, Any]]：
            当前可用的固定燃油资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("固定燃油资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            if zone == "A":
                # 针对A区，不初始化资源，表示资源不再可用
                continue
            resource_id = f"FIX-{zone}-FUEL-{index:02d}"
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "燃油",
                    "mobility": "固定",
                    "zone": zone,
                    "current_location_id": None,
                    "capacity": 1,
                    "status": "不可用",  # 代表燃油资源不再可用
                    "blocked_reason": "A区固定燃油资源FIX-A-FUEL-01已经不可用"  # 提供具体原因
                }
            )
    return resources
