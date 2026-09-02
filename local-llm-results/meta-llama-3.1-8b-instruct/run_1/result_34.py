def initialize_mobile_fuel_resources(
    resource_count: int,
    initial_location_id: str,
    faulty_resource_id: str = None,  # 新增一个参数来接收故障资源的 ID
) -> list[dict[str, Any]]:
    """初始化当前可用的移动燃油资源，并检测故障资源

    输入：
        resource_count（int）：
            移动燃油资源的数量。
        initial_location_id（str）：
            移动燃油资源的初始位置编号。
        faulty_resource_id（str）：
            故障燃油资源的 ID（可选）。

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
    for index in range(1, resource_count + 1):
        resource_id = f"MOB-FUEL-{index:02d}"
        if resource_id == faulty_resource_id:
            nearest_stand_id = get_nearest_stand_id(initial_location_id, initialize_support_stands())
            resources.append(
                {
                    "resource_id": resource_id,
                    "resource_type": "燃油",
                    "mobility": "移动",
                    "zone": None,
                    "current_location_id": nearest_stand_id,
                    "capacity": 1,
                    "status": "故障",
                }
            )
        else:
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

def get_nearest_stand_id(location_id: str, stands: dict[str, dict[str, Any]]) -> str:
    nearest_stand_id = None
    min_distance = float('inf')
    for stand_id, stand in stands.items():
        if stand["zone"] == location_id[-1]:
            distance = calculate_distance(location_id, stand["location_id"])
            if distance < min_distance:
                min_distance = distance
                nearest_stand_id = stand_id
    return nearest_stand_id

def calculate_distance(location_id1: str, location_id2: str) -> float:
    return abs(int(location_id1) - int(location_id2))

def initialize_support_stands() -> dict[str, dict[str, Any]]:
    stand_counts = {"A": 6, "B": 8, "C": 5}
    stands: dict[str, dict[str, Any]] = {}
    for zone, count in stand_counts.items():
        for index in range(1, count + 1):
            stand_id = f"{zone}{index}"
            stands[stand_id] = {
                "location_id": stand_id,
                "kind": "保障站位",
                "zone": zone,
            }
    return stands
