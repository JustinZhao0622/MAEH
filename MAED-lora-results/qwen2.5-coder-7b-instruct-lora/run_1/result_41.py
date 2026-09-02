from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_tow_tractors(
    tow_tractor_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的牵引车。

    输入：
        tow_tractor_count（int）：
            牵引车数量。
        initial_location_id（str）：
            牵引车初始位置编号。

    输出：
        list[dict[str, Any]]：
            当前可用的牵引车资源列表。

    异常：
        ValueError：
            牵引车数量小于0时抛出。
    """

    if tow_tractor_count < 0:
        raise ValueError("牵引车数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, tow_tractor_count + 1):
        resource_id = f"MOB-TOW-{index:02d}"
        resource = {
            "resource_id": resource_id,
            "resource_type": "牵引车",
            "mobility": "移动",
            "zone": None,
            "current_location_id": initial_location_id,
            "capacity": 1,
        }
        if resource_id == "MOB-TOW-02":
            resource["status"] = "故障"
        resources.append(resource)
    return resources
