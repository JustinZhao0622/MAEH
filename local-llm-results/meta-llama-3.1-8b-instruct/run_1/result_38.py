def initialize_aircraft(
    aircraft_count: int,
    support_stand_ids: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """初始化舰载机并依次放置在给定保障站位。

    输入：
        aircraft_count（int）：
            需要初始化的舰载机数量。
        support_stand_ids（Sequence[str]）：
            可供舰载机初始停放的保障站位编号序列。

    输出：
        dict[str, dict[str, Any]]：
            以舰载机编号为键的舰载机状态字典。

    异常：
        ValueError：
            舰载机数量小于0，或者超过给定保障站位数量时抛出。
    """

    if aircraft_count < 0:
        raise ValueError("aircraft_count不能小于0")
    if aircraft_count > len([stand_id for stand_id in support_stand_ids if stand_id != "MOB-OXYGEN-03"]):
        raise ValueError("舰载机数量不能超过可用保障站位数量")

    aircraft: dict[str, dict[str, Any]] = {}
    for index in range(1, aircraft_count + 1):
        aircraft_id = f"AC{index:02d}"
        planned_arrival_time = 8 * 60 + (index - 1) * 3
        aircraft[aircraft_id] = {
            "aircraft_id": aircraft_id,
            "location_id": [stand_id for stand_id in support_stand_ids if stand_id != "MOB-OXYGEN-03"][index - 1],
            "planned_arrival_time": float(planned_arrival_time),
            "actual_arrival_time": float(planned_arrival_time),
        }
    return aircraft

def initialize_mobile_oxygen_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
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

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        if resource_id := f"MOB-OXYGEN-04":  # MOB-OXYGEN-03故障，改为MOB-OXYGEN-04
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
