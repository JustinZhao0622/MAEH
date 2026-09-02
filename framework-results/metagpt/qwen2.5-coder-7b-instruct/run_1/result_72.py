def initialize_route_segments() -> list[dict[str, Any]]:
    """初始化所有路径段。

    输入：
        无。

    输出：
        list[dict[str, Any]]：
        所有路径段的列表。

    异常：
        ValueError：
            起点与终点相同，或者距离不大于0时抛出。
    """

    segments = [
        create_route_segment("L1", "L2"),
        create_route_segment("L2", "R1"),
        create_route_segment("L2", "R2"),
        create_route_segment("R1", "C1"),
        create_route_segment("R2", "C1"),
        create_route_segment("C1", "L1"),
    ]

    # Disable the Segment SEG-L1-C1 due to local restrictions
    for segment in segments:
        if segment["start_location_id"] == "L1" and segment["end_location_id"] == "C1":
            segment["status"] = "不可通行"
            segment["blocked_reason"] = "局部区域受限"

    return segments
