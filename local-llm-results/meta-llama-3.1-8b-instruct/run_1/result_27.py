def initialize_mobile_power_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动供电资源。

    如果MOB-POWER-04故障，则忽略MOB-POWER-04资源。
    否则，正常添加MOB-POWER-04资源。

    输入：
        resource_count（int）：
            移动供电资源的数量。
        initial_location_id（str）：
            移动供电资源的初始位置编号。

    输出：
        list[dict[str, Any]]：
            当前可用的移动供电资源列表。
    """

    if resource_count < 0:
        raise ValueError("移动供电资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    for index in range(1, resource_count + 1):
        if f"MOB-POWER-04" == f"MOB-POWER-{index:02d}":
            # MOB-POWER-04故障，忽略此资源
            continue
        resource_id = f"MOB-POWER-{index:02d}"
        resources.append(
            {
                "resource_id": resource_id,
                "resource_type": "供电",
                "mobility": "移动",
                "zone": None,
                "current_location_id": initial_location_id,
                "capacity": 1,
            }
        )
    return resources
