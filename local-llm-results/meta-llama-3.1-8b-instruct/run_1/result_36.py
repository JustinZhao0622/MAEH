def initialize_fixed_oxygen_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定供氧资源。

    输入：
        units_per_zone（int）：
            每个区域内固定供氧资源的数量。论文设置为2。

    输出：
        list[dict[str, Any]]：
            当前可用的固定供氧资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("固定供氧资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            if zone == "A" and index == 1:
                # MOB-OXYGEN-01故障，禁用固定供氧资源
                resources.append(
                    {
                        "resource_id": f"FIX-{zone}-OXYGEN-{index:02d}",
                        "resource_type": "供氧",
                        "mobility": "固定",
                        "zone": zone,
                        "current_location_id": None,
                        "capacity": 0,
                        "status": "故障",
                    }
                )
            else:
                resources.append(
                    {
                        "resource_id": f"FIX-{zone}-OXYGEN-{index:02d}",
                        "resource_type": "供氧",
                        "mobility": "固定",
                        "zone": zone,
                        "current_location_id": None,
                        "capacity": 1,
                    }
                )
    return resources


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
        if index == 1:
            # MOB-OXYGEN-01故障，禁用移动供氧资源
            resources.append(
                {
                    "resource_id": f"MOB-OXYGEN-{index:02d}",
                    "resource_type": "供氧",
                    "mobility": "移动",
                    "zone": None,
                    "current_location_id": initial_location_id,
                    "capacity": 0,
                    "status": "故障",
                }
            )
        else:
            resources.append(
                {
                    "resource_id": f"MOB-OXYGEN-{index:02d}",
                    "resource_type": "供氧",
                    "mobility": "移动",
                    "zone": None,
                    "current_location_id": initial_location_id,
                    "capacity": 1,
                }
            )
    return resources
