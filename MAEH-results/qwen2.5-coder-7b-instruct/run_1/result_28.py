from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

import json
from typing import Any, List, Dict

def initialize_mobile_hydraulic_resources(
    resource_count: int,
    initial_location_id: str,
) -> List[Dict[str, Any]]:
    """初始化当前可用的移动液压资源。

    输入：
        resource_count（int）：
            移动液压资源的数量。
        initial_location_id（str）：
            移动液压资源的初始位置编号。

    输出：
        list[dict[str, Any]]：
            当前可用的移动液压资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if resource_count < 0:
        raise ValueError("移动液压资源数量不能小于0")

    resources: List[Dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-HYDRAULIC-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "液压",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources

def handle_emergency_situation(resource_id: str) -> None:
    """处理移动液压资源故障的应急情况。

    输入：
        resource_id（str）：
            故障移动液压资源的编号。

    输出：
        None
    """

    # 模拟故障处理逻辑
    print(f"处理资源 {resource_id} 的故障")

# 示例调用
resources = initialize_mobile_hydraulic_resources(3, "ZONE-01")
for resource in resources:
    if resource["resource_id"] == "MOB-HYDRAULIC-01":
        handle_emergency_situation(resource["resource_id"])
