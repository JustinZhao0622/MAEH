from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_mobile_oxygen_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动供氧资源。

    输入：
        resource_count（int）：
            移动供氧资源的数量。
        initial_location_id（str）：
            移动供氧资源的初始位置编号。

    输出：
        list[dict[str, Any]]：
            当前可用的移动供氧资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if resource_count < 0:
        raise ValueError("移动供氧资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-OXYGEN-{index:02d}"
        if resource_id == "MOB-OXYGEN-02":
            # 根据突发事件描述，MOB-OXYGEN-02发生故障，故将其设置为不可用
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "供氧",
                    "mobility": "移动",
                    "zone": None,
                    "current_location_id": initial_location_id,
                    "capacity": 0,
                    "status": "故障"
                }
            )
        else:
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "供氧",
                    "mobility": "移动",
                    "zone": None,
                    "current_location_id": initial_location_id,
                    "capacity": 1,
                }
            )
    return resources
