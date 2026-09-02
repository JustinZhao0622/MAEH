def initialize_runways() -> dict[str, dict[str, Any]]:
    """初始化3条起飞跑道。

    输入：
        无。

    输出：
        dict[str, dict[str, Any]]：
        包含R1、R2和R3的起飞跑道字典。
    """

    return {
        runway_id: {
            "location_id": runway_id,
            "kind": "起飞跑道",
            "zone": None,
            "status": "可通行" if runway_id != "R1" else "不可通行"
        }
        for runway_id in ("R1", "R2", "R3")
    }
