from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

import json
from typing import Any, List, Dict

def initialize_tow_tractors(
    tow_tractor_count: int,
    initial_location_id: str,
) -> List[Dict[str, Any]]:
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

    resources: List[Dict[str, Any]] = []
    for index in range(1, tow_tractor_count + 1):
        resource_id = f"MOB-TOW-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "牵引车",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources

def handle_tow_tractor_failure(resource_id: str) -> None:
    """处理牵引车故障。

    输入：
        resource_id（str）：
            故障牵引车的资源编号。

    输出：
        None
    """

    # 模拟故障处理逻辑
    print(f"处理牵引车 {resource_id} 的故障")

# 示例调用
if __name__ == "__main__":
    tow_tractors = initialize_tow_tractors(3, "LOC-001")
    print(json.dumps(tow_tractors, ensure_ascii=False, indent=4))

    # 模拟故障发生
    handle_tow_tractor_failure("MOB-TOW-01")
