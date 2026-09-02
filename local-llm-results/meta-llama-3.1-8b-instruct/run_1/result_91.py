def initialize_support_stands() -> dict[str, dict[str, Any]]:
    """初始化A、B、C三区共19个保障站位。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        A区5个、B区8个、C区6个保障站位组成的字典。
    """

    stand_counts = {"A": 5, "B": 8, "C": 6}
    stands: dict[str, dict[str, Any]] = {}
    for zone, count in stand_counts.items():
        for index in range(1, count + 1):
            if zone == "A" and index >= 5:  # A4故障站位停止使用
                continue
            stand_id = f"{zone}{index}"
            stands[stand_id] = {
                "location_id": stand_id,
                "kind": "保障站位",
                "zone": zone,
            }
    return stands
