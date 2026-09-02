def can_assign_to_runway(aircraft_id: str) -> bool:
    """判断舰载机是否可以分配给起飞跑道。

    输入：
        aircraft_id（str）：
            舰载机编号。

    输出：
        bool：
        舰载机是否可以分配给起飞跑道。
    """

    aircraft = get_aircraft(aircraft_id)
    if not aircraft:
        return False
    runway_id = aircraft["location_id"]
    runway = get_runway(runway_id)
    if not runway:
        return False
    return runway["is_operational"] and runway_id != "R1"
