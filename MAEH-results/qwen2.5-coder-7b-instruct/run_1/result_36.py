from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

import json
from typing import Any, List, Dict

def initialize_mobile_oxygen_resources(
    resource_count: int,
    initial_location_id: str,
) -> List[Dict[str, Any]]:
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

    resources: List[Dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-OXYGEN-{index:02d}"
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

def update_mobile_oxygen_resource_status(
    resource_id: str,
    new_location_id: str,
) -> None:
    """更新移动供氧资源的状态。

    输入：
        resource_id（str）：
            移动供氧资源的编号。
        new_location_id（str）：
            移动供氧资源的新位置编号。

    输出：
        None
    """
    # 假设这里有一个全局资源列表
    global resources
    for resource in resources:
        if resource["resource_id"] == resource_id:
            resource["current_location_id"] = new_location_id
            break

# 示例调用
resources = initialize_mobile_oxygen_resources(3, "LOC-001")
update_mobile_oxygen_resource_status("MOB-OXYGEN-01", "LOC-002")
print(json.dumps(resources, ensure_ascii=False, indent=4))
