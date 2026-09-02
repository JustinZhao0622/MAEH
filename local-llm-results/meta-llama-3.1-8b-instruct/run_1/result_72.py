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

    # 检查路径段是否与受限区域相交
    # 为每个路径段维护一个列表，存储受限区域
    blocked_segments: dict[str, list[str]] = {
        "L1-C1": ["SEG-L1-C1"],
    }
    if f"SEG-{start_location_id}-{end_location_id}" in blocked_segments.get((start_location_id, end_location_id), []):
        raise ValueError(f"路径段{start_location_id}->{end_location_id}受限区域受限")

    segment_id = f"SEG-{start_location_id}-{end_location_id}"
    return {
        "segment_id": segment_id,
        "start_location_id": start_location_id,
        "end_location_id": end_location_id,
        "distance": float(distance),
        "status": "可通行",
        "blocked_reason": None,
    }
