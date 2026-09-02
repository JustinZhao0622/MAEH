def initialize_tow_tractors(
    tow_tractor_count: int,
    initial_location_id: str,
) -> dict[str, dict[str, Any]]:
    """初始化当前可用的牵引车。

    输入：
        tow_tractor_count（int）：
            牵引车数量。
        initial_location_id（str）：
            牵引车初始位置编号。

    输出：
        dict[str, dict[str, Any]]：
            以牵引车id为键的牵引车状态字典。

    异常：
        ValueError：
            牵引车数量小于0时抛出。
    """

    if tow_tractor_count < 0:
        raise ValueError("牵引车数量不能小于0")

    resources: dict[str, dict[str, Any]] = {}
    for index in range(1, tow_tractor_count + 1):
        resource_id = f"MOB-TOW-{index:02d}"
        resources[resource_id] = {
            "resource_id": resource_id,
            "resource_type": "牵引车",
            "mobility": "移动",
            "zone": None,
            "current_location_id": initial_location_id,
            "capacity": 1,
            "status": "可用" if index != 1 else "故障"
        }
    return resources
