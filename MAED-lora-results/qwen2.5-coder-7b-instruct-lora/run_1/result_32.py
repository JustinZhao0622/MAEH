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
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "燃油",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources

def handle_emergency_situation(resource_id: str) -> None:
    """处理突发事件，更新移动燃油资源的状态。

    输入：
        resource_id（str）：
            发生故障的移动燃油资源的编号。

    输出：
        None
    """

    resources = initialize_mobile_fuel_resources(1, "INITIAL_LOCATION")
    for resource in resources:
        if resource["resource_id"] == resource_id:
            resource["status"] = "故障"
            resource["current_location_id"] = None
            break
