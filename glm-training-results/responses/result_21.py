from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_mobile_power_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动供电资源。

    输入：
        resource_count（int）：
            移动供电资源的数量。
        initial_location_id（str）：
            移动供电资源的初始位置编号。

    输出：
        list[dict[str, Any]]：
            当前可用的移动供电资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if resource_count < 0:
        raise ValueError("移动供电资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-POWER-{index:02d}"
        resource = {
            "resource_id": resource_id,
            "resource_type": "供电",
            "mobility": "移动",
            "zone": None,
            "current_location_id": initial_location_id,
            "capacity": 1,
        }
        if resource_id == "MOB-POWER-08":
            resource["status"] = "失效"
            resource["failure_task_index"] = 4
        resources.append(resource)
    return resources
