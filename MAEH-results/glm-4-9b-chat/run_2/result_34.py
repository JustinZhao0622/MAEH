from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_mobile_fuel_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动燃油资源。

    输入：
        resource_count（int）：
            移动燃油资源的数量。
        initial_location_id（str）：
            移动燃油资源的初始位置编号。

    输出：
        list[dict[str, Any]]：
            当前可用的移动燃油资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if resource_count < 0:
        raise ValueError("移动燃油资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-FUEL-{index:02d}"
        # 检查是否有移动燃油资源MOB-FUEL-03发生故障
        if resource_id == "MOB-FUEL-03":
            # 假设故障资源被标记为不可用
            is_available = False
        else:
            is_available = True
        
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "燃油",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
                "is_available": is_available,  # 添加可用性字段
            }
        )
    return resources
