def initialize_mobile_fuel_resources(
    resource_count: int,
    initial_location_id: str,
) -> list[dict[str, Any]]:
    """初始化当前可用的移动燃油资源。

    输入：
        resource_count（int）：
            移动燃油资源的数量。
        initial_location_id（str）：
            移动燃油资源的初始位置编号。

    输出：
        list[dict[str, Any]]：
            当前可用的移动燃油资源列表。

    异常：
        ValueError：
            资源数量小于0时抛出。
    """

    if resource_count < 0:
        raise ValueError("移动燃油资源数量不能小于0")

    resources: list[dict[str, Any]] = []
    resource_id = f"MOB-FUEL-02"
    resources.append(
        {
            "resource_id": resource_id,
            "resource_type": "燃油",
            "mobility": "移动",
            "zone": None,
            "current_location_id": None,  # 修改为MOB-FUEL-02故障导致资源无法正常工作
            "capacity": 0,  # capacity设置为0表示资源不可用
        }
    )

    for index in range(1, resource_count + 1):
        if index != 2:  # 排除故障的MOB-FUEL-02资源
            resource_id = f"MOB-FUEL-{index:02d}"
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "燃油",
                    "mobility": "移动",
                    "zone": None,
                    "current_location_id": initial_location_id,
                    "capacity": 1,
                }
            )
    return resources


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

    # 如果MOB-FUEL-02资源不可用，则拒绝路径规划
    if any(resource['resource_id'] == 'MOB-FUEL-02' for resource in get_all_resources()):
        raise ValueError("MOB-FUEL-02资源不可用，无法规划路径")

    # ... (其余代码保持不变)
