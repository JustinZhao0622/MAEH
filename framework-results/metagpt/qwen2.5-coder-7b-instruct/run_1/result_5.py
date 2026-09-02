def initialize_fixed_fuel_resources(
    units_per_zone: int = 2,
) -> list[dict[str, Any]]:
    """初始化A、B、C三区当前可用的固定燃油资源。

    输入：
        units_per_zone（int）：
            每个区域内固定燃油资源的数量。论文设置为2。

    输出：
        list[dict[str, Any]]：
            当前可用的固定燃油资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if units_per_zone < 0:
        raise ValueError("固定燃油资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for zone in ("A", "B", "C"):
        for index in range(1, units_per_zone + 1):
            resource_id = f"FIX-{zone}-FUEL-{index:02d}"
            if resource_id == "FIX-A-FUEL-01":
                resources.append(
                    {
                        "resource_id": resource_id,
                        "resource_type": "燃油",
                        "mobility": "固定",
                        "zone": zone,
                        "current_location_id": None,
                        "capacity": 0,  # 标记为不可用
                    }
                )
            else:
                resources.append(
                    {
                        "resource_id": resource_id,
                        "resource_type": "燃油",
                        "mobility": "固定",
                        "zone": zone,
                        "current_location_id": None,
                        "capacity": 1,
                    }
                )
    return resources
