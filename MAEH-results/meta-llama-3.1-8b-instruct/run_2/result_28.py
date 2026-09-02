from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def initialize_mobile_hydraulic_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
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

    resources: list[dict[str, Any]] = []
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
                "status": "正常",  # 添加状态字段
                "fault": False  # 添加故障字段
            }
        )
    return resources

# 对于故障的移动液压资源MOB-HYDRAULIC-01进行标记
def mark_hydraulic_resource_as_faulty(resource_id: str):
    for resource in initialize_mobile_hydraulic_resources(10, "初始位置"):
        if resource["resource_id"] == resource_id:
            resource["status"] = "故障"
            resource["fault"] = True
            break

mark_hydraulic_resource_as_faulty("MOB-HYDRAULIC-01")
print(initialize_mobile_hydraulic_resources(10, "初始位置"))
