def initialize_support_stands() -> dict[str, dict[str, Any]]:
    """初始化A、B、C三区共19个保障站位。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        A区6个、B区8个、C区4个保障站位组成的字典。
    """

    stand_counts = {"A": 6, "B": 8, "C": 4}  # 将C区保障站位数量减少为4
    stands: dict[str, dict[str, Any]] = {}
    for zone, count in stand_counts.items():
        for index in range(1, count + 1):
            stand_id = f"{zone}{index}"
            if zone == "A" and index >= 5:  # 如果是A区且索引大于或等于5，则跳过该站位
                continue
            stands[stand_id] = {
                "location_id": stand_id,
                "kind": "保障站位",
                "zone": zone,
            }
    return stands
