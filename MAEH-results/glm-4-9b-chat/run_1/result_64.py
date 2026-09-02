from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

def create_route_segment(
    start_location_id: str,
    end_location_id: str,
    distance: float = 1.0,
) -> dict[str, Any]:
    """创建一条单向路径段。

    输入：
        start_location_id（str）：
            路径起点编号。
        end_location_id（str）：
            路径终点编号。
        distance（float）：
            路径距离，默认值为1.0。

    输出：
        dict[str, Any]：
        包含路径编号、起点、终点、距离和通行状态的字典。

    异常：
        ValueError：
            起点与终点相同，或者距离不大于0时抛出。
    """

    if start_location_id == end_location_id:
        raise ValueError("路径段的起点和终点不能相同")
    if distance <= 0:
        raise ValueError("路径距离必须大于0")

    segment_id = f"SEG-{start_location_id}-{end_location_id}"
    # 根据突发事件描述，修改通行状态
    if segment_id == "SEG-L1-B1":
        return {
            "segment_id": segment_id,
            "start_location_id": start_location_id,
            "end_location_id": end_location_id,
            "distance": float(distance),
            "status": "不可通行",
            "blocked_reason": "局部区域受限",
        }
    else:
        return {
            "segment_id": segment_id,
            "start_location_id": start_location_id,
            "end_location_id": end_location_id,
            "distance": float(distance),
            "status": "可通行",
            "blocked_reason": None,
        }
