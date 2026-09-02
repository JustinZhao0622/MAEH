"""MAEH舰载航空枢纽特情注入函数。

本文件仅使用普通函数和字典，不定义类、枚举或数据类。
每类特情由一个独立函数处理，函数直接修改传入的环境字典，
并返回本次特情的事件记录。
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Callable


def inject_fixed_resource_failure(
    environment: dict[str, Any],
    resource_id: str,
    occurred_at: float = 0.0,
    reason: str | None = None,
) -> dict[str, Any]:
    """注入固定资源故障。

    输入：
        environment（dict[str, Any]）：
            资源初始化文件生成的环境字典。
        resource_id（str）：
            发生故障的固定保障资源编号。
        occurred_at（float）：
            特情发生时刻。
        reason（str | None）：
            可选的故障原因描述。

    输出：
        dict[str, Any]：
        本次特情的事件记录。

    异常：
        KeyError：
            固定保障资源编号不存在时抛出。
    """

    resource = _remove_section_item(
        environment,
        "fixed_resources",
        resource_id,
        "固定保障资源",
    )
    return _record_event(
        environment=environment,
        emergency_type="固定资源故障",
        target_id=resource_id,
        occurred_at=occurred_at,
        description=reason or f"固定保障资源{resource_id}发生故障",
        metadata={
            "resource_type": resource.get("resource_type"),
            "zone": resource.get("zone"),
        },
    )


def inject_mobile_resource_failure(
    environment: dict[str, Any],
    resource_id: str,
    occurred_at: float = 0.0,
    reason: str | None = None,
) -> dict[str, Any]:
    """注入移动资源故障。

    输入：
        environment（dict[str, Any]）：
            资源初始化文件生成的环境字典。
        resource_id（str）：
            发生故障的移动保障资源编号。
        occurred_at（float）：
            特情发生时刻。
        reason（str | None）：
            可选的故障原因描述。

    输出：
        dict[str, Any]：
        本次特情的事件记录。

    异常：
        KeyError：
            移动保障资源编号不存在时抛出。
    """

    resource = _remove_section_item(
        environment,
        "mobile_resources",
        resource_id,
        "移动保障资源",
    )
    return _record_event(
        environment=environment,
        emergency_type="移动资源故障",
        target_id=resource_id,
        occurred_at=occurred_at,
        description=reason or f"移动保障资源{resource_id}发生故障",
        metadata={
            "resource_type": resource.get("resource_type"),
            "current_location_id": resource.get("current_location_id"),
        },
    )


def inject_runway_failure(
    environment: dict[str, Any],
    runway_id: str,
    occurred_at: float = 0.0,
    reason: str | None = None,
) -> dict[str, Any]:
    """注入跑道故障。

    输入：
        environment（dict[str, Any]）：
            资源初始化文件生成的环境字典。
        runway_id（str）：
            发生故障的起飞跑道编号。
        occurred_at（float）：
            特情发生时刻。
        reason（str | None）：
            可选的故障原因描述。

    输出：
        dict[str, Any]：
        本次特情的事件记录。

    异常：
        KeyError：
            跑道编号不存在时抛出。
        ValueError：
            目标编号不是起飞跑道时抛出。
    """

    _remove_location_by_kind(
        environment,
        runway_id,
        "起飞跑道",
    )
    return _record_event(
        environment=environment,
        emergency_type="跑道故障",
        target_id=runway_id,
        occurred_at=occurred_at,
        description=reason or f"起飞跑道{runway_id}发生故障并关闭",
        metadata={},
    )


def inject_path_planning_failure(
    environment: dict[str, Any],
    segment_id: str,
    occurred_at: float = 0.0,
    reason: str | None = None,
) -> dict[str, Any]:
    """注入路径规划故障。

    该函数只把指定路径段标记为不可通行，不执行路径搜索或重规划。

    输入：
        environment（dict[str, Any]）：
            资源初始化文件生成的环境字典。
        segment_id（str）：
            发生异常的路径段编号。
        occurred_at（float）：
            特情发生时刻。
        reason（str | None）：
            可选的路径不可通行原因。

    输出：
        dict[str, Any]：
        本次特情的事件记录。

    异常：
        KeyError：
            路径段编号不存在时抛出。
    """

    segment = _get_section_item(
        environment,
        "route_segments",
        segment_id,
        "路径段",
    )
    blocked_reason = reason or f"路径段{segment_id}不可通行"
    segment["status"] = "不可通行"
    segment["blocked_reason"] = blocked_reason
    return _record_event(
        environment=environment,
        emergency_type="路径规划故障",
        target_id=segment_id,
        occurred_at=occurred_at,
        description=blocked_reason,
        metadata={
            "start_location_id": segment.get("start_location_id"),
            "end_location_id": segment.get("end_location_id"),
        },
    )


def inject_aircraft_delayed_arrival(
    environment: dict[str, Any],
    aircraft_id: str,
    delay: float,
    occurred_at: float = 0.0,
    reason: str | None = None,
) -> dict[str, Any]:
    """注入舰载机延迟到达特情。

    输入：
        environment（dict[str, Any]）：
            资源初始化文件生成的环境字典。
        aircraft_id（str）：
            延迟到达的舰载机编号。
        delay（float）：
            本次增加的延迟分钟数，必须大于0。
        occurred_at（float）：
            特情发生时刻。
        reason（str | None）：
            可选的延迟原因描述。

    输出：
        dict[str, Any]：
        本次特情的事件记录。

    异常：
        KeyError：
            舰载机编号不存在时抛出。
        ValueError：
            延迟时间不大于0时抛出。
    """

    if delay <= 0:
        raise ValueError("延迟时间必须大于0")

    aircraft = _get_section_item(
        environment,
        "aircraft",
        aircraft_id,
        "舰载机",
    )
    aircraft["delay"] = float(aircraft.get("delay", 0.0)) + float(delay)
    aircraft["actual_arrival_time"] = (
        float(aircraft.get("planned_arrival_time", 0.0))
        + aircraft["delay"]
    )
    planned_minutes = int(
        float(aircraft.get("planned_arrival_time", 0.0))
    )
    planned_time = (
        f"{planned_minutes // 60:02d}:{planned_minutes % 60:02d}"
    )
    return _record_event(
        environment=environment,
        emergency_type="舰载机延迟到达",
        target_id=aircraft_id,
        occurred_at=occurred_at,
        description=(
            reason
            or (
                f"舰载机{aircraft_id}计划于{planned_time}到达，"
                f"现延迟{delay:g}分钟"
            )
        ),
        metadata={
            "delay": float(delay),
            "accumulated_delay": aircraft["delay"],
            "actual_arrival_time": aircraft["actual_arrival_time"],
        },
    )


def inject_support_stand_failure(
    environment: dict[str, Any],
    stand_id: str,
    occurred_at: float = 0.0,
    reason: str | None = None,
) -> dict[str, Any]:
    """注入保障站位故障。

    输入：
        environment（dict[str, Any]）：
            资源初始化文件生成的环境字典。
        stand_id（str）：
            发生故障的保障站位编号。
        occurred_at（float）：
            特情发生时刻。
        reason（str | None）：
            可选的站位故障原因描述。

    输出：
        dict[str, Any]：
        本次特情的事件记录。metadata中包含当前位于该站位的舰载机。

    异常：
        KeyError：
            保障站位编号不存在时抛出。
        ValueError：
            目标编号不是保障站位时抛出。
    """

    _remove_location_by_kind(
        environment,
        stand_id,
        "保障站位",
    )
    affected_aircraft_ids = sorted(
        aircraft_id
        for aircraft_id, aircraft in environment.get(
            "aircraft",
            {},
        ).items()
        if aircraft.get("location_id") == stand_id
    )
    return _record_event(
        environment=environment,
        emergency_type="保障站位故障",
        target_id=stand_id,
        occurred_at=occurred_at,
        description=reason or f"保障站位{stand_id}发生故障并关闭",
        metadata={"affected_aircraft_ids": affected_aircraft_ids},
    )


def inject_emergency(
    environment: dict[str, Any],
    emergency_type: str,
    target_id: str,
    occurred_at: float = 0.0,
    **parameters: Any,
) -> dict[str, Any]:
    """根据中文特情类型调用对应的特情注入函数。

    输入：
        environment（dict[str, Any]）：
            资源初始化文件生成的环境字典。
        emergency_type（str）：
            特情类型。支持固定资源故障、移动资源故障、跑道故障、
            路径规划故障、舰载机延迟到达和保障站位故障。
        target_id（str）：
            特情作用对象编号。
        occurred_at（float）：
            特情发生时刻。
        **parameters（Any）：
            对应特情函数所需的附加参数。舰载机延迟到达必须提供delay。

    输出：
        dict[str, Any]：
        对应特情注入函数返回的事件记录。

    异常：
        ValueError：
            特情类型不受支持时抛出。
        KeyError：
            目标编号不存在时抛出。
        TypeError：
            缺少对应特情函数的必要参数时抛出。
    """

    handlers: dict[str, Callable[..., dict[str, Any]]] = {
        "固定资源故障": inject_fixed_resource_failure,
        "移动资源故障": inject_mobile_resource_failure,
        "跑道故障": inject_runway_failure,
        "路径规划故障": inject_path_planning_failure,
        "舰载机延迟到达": inject_aircraft_delayed_arrival,
        "保障站位故障": inject_support_stand_failure,
    }
    try:
        handler = handlers[emergency_type]
    except KeyError as exc:
        supported_types = "、".join(handlers)
        raise ValueError(
            f"不支持的特情类型: {emergency_type}。"
            f"可用类型为: {supported_types}"
        ) from exc

    return handler(
        environment,
        target_id,
        occurred_at=occurred_at,
        **parameters,
    )


def get_supported_emergency_types() -> list[str]:
    """返回当前支持的特情类型。

    输入：
        无。

    输出：
        list[str]：
        六类中文特情名称组成的列表。
    """

    return [
        "固定资源故障",
        "移动资源故障",
        "跑道故障",
        "路径规划故障",
        "舰载机延迟到达",
        "保障站位故障",
    ]


def _get_section_item(
    environment: dict[str, Any],
    section_name: str,
    item_id: str,
    entity_name: str,
) -> dict[str, Any]:
    """从环境的指定部分获取目标数据项。

    输入：
        environment（dict[str, Any]）：
            环境字典。
        section_name（str）：
            环境中的数据部分名称。
        item_id（str）：
            目标数据项编号。
        entity_name（str）：
            错误信息中使用的实体名称。

    输出：
        dict[str, Any]：
        与目标编号对应的数据项。

    异常：
        KeyError：
            数据部分或目标编号不存在时抛出。
    """

    try:
        section = environment[section_name]
    except KeyError as exc:
        raise KeyError(f"环境缺少数据部分: {section_name}") from exc

    if isinstance(section, dict):
        try:
            return section[item_id]
        except KeyError as exc:
            raise KeyError(f"{entity_name}不存在: {item_id}") from exc
    if isinstance(section, list):
        for item in section:
            if (
                isinstance(item, dict)
                and _item_identifier(item) == item_id
            ):
                return item
        raise KeyError(f"{entity_name}不存在: {item_id}")
    raise TypeError(f"环境数据部分{section_name}必须是字典或列表")


def _remove_section_item(
    environment: dict[str, Any],
    section_name: str,
    item_id: str,
    entity_name: str,
) -> dict[str, Any]:
    """从可用实体集合中移除并返回指定数据项。"""

    try:
        section = environment[section_name]
    except KeyError as exc:
        raise KeyError(f"环境缺少数据部分: {section_name}") from exc

    if isinstance(section, dict):
        try:
            item = section.pop(item_id)
        except KeyError as exc:
            raise KeyError(f"{entity_name}不存在: {item_id}") from exc
        if not isinstance(item, dict):
            raise TypeError(f"{entity_name}{item_id}必须是字典")
        return item
    if isinstance(section, list):
        for index, item in enumerate(section):
            if (
                isinstance(item, dict)
                and _item_identifier(item) == item_id
            ):
                return section.pop(index)
        raise KeyError(f"{entity_name}不存在: {item_id}")
    raise TypeError(f"环境数据部分{section_name}必须是字典或列表")


def _item_identifier(item: dict[str, Any]) -> Any:
    """读取资源或场地数据项的编号。"""

    for field in (
        "resource_id",
        "location_id",
        "segment_id",
        "aircraft_id",
    ):
        if field in item:
            return item[field]
    return None


def _get_location_by_kind(
    environment: dict[str, Any],
    location_id: str,
    expected_kind: str,
) -> dict[str, Any]:
    """获取场地位置并校验其类型。

    输入：
        environment（dict[str, Any]）：
            环境字典。
        location_id（str）：
            场地位置编号。
        expected_kind（str）：
            期望的位置类型。

    输出：
        dict[str, Any]：
        对应的场地位置字典。

    异常：
        KeyError：
            场地位置不存在时抛出。
        ValueError：
            实际位置类型与期望类型不一致时抛出。
    """

    location = _get_section_item(
        environment,
        "locations",
        location_id,
        "场地位置",
    )
    actual_kind = location.get("kind")
    if actual_kind != expected_kind:
        raise ValueError(
            f"{location_id}不是{expected_kind}，实际类型为{actual_kind}"
        )
    return location


def _remove_location_by_kind(
    environment: dict[str, Any],
    location_id: str,
    expected_kind: str,
) -> dict[str, Any]:
    """校验场地类型并将目标从当前可用场地集合中移除。"""

    location = _get_location_by_kind(
        environment,
        location_id,
        expected_kind,
    )
    removed = _remove_section_item(
        environment,
        "locations",
        location_id,
        "场地位置",
    )
    if removed is not location and removed != location:
        raise RuntimeError(f"场地位置{location_id}移除结果不一致")
    return removed


def _record_event(
    environment: dict[str, Any],
    emergency_type: str,
    target_id: str,
    occurred_at: float,
    description: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """生成特情事件记录并写入环境日志。

    输入：
        environment（dict[str, Any]）：
            环境字典。
        emergency_type（str）：
            特情类型。
        target_id（str）：
            特情作用对象编号。
        occurred_at（float）：
            特情发生时刻。
        description（str）：
            特情描述。
        metadata（dict[str, Any]）：
            特情附加信息。

    输出：
        dict[str, Any]：
        新生成的事件记录。
    """

    next_sequence = int(environment.get("_event_sequence", 0)) + 1
    environment["_event_sequence"] = next_sequence
    event = {
        "event_id": f"E{next_sequence:04d}",
        "emergency_type": emergency_type,
        "target_id": target_id,
        "occurred_at": float(occurred_at),
        "description": description,
        "metadata": dict(metadata),
    }
    environment.setdefault("events", []).append(event)
    return event

def build_emergency_test_set(
    random_seed: int | None = 20260730,
) -> list[dict[str, str]]:
    """按照给定类型数量构建特情测试集。

    输入：
        random_seed（int | None）：
            舰载机随机延迟分钟数的种子。默认值用于保证测试集可复现；
            设为None时，每次运行生成不同的延迟分钟数。

    输出：
        list[dict[str, str]]：
        包含100个独立特情的测试集。其中，固定资源故障23条、
        移动资源故障18条、跑道故障16条、路径规划故障16条、
        舰载机延迟到达14条、保障站位故障13条。每个列表项只
        包含emergency字段，不包含其他数据。
    """

    random_generator = random.Random(random_seed)
    emergency_items: list[dict[str, str]] = []

    fixed_resource_types = (
        ("POWER", "供电"),
        ("HYDRAULIC", "液压"),
        ("FUEL", "燃油"),
        ("OXYGEN", "供氧"),
    )
    fixed_targets = [
        (zone, resource_code, resource_name, index)
        for zone in ("A", "B", "C")
        for resource_code, resource_name in fixed_resource_types
        for index in (1, 2)
    ][:23]
    for zone, resource_code, resource_name, index in fixed_targets:
        target_id = f"FIX-{zone}-{resource_code}-{index:02d}"
        emergency_items.append(
            {
                "emergency": (
                    f"{zone}区固定{resource_name}资源{target_id}"
                    "发生故障，当前不可用"
                )
            }
        )

    mobile_resource_types = (
        ("POWER", "供电"),
        ("HYDRAULIC", "液压"),
        ("FUEL", "燃油"),
        ("OXYGEN", "供氧"),
    )
    mobile_targets = [
        (resource_code, resource_name, index)
        for resource_code, resource_name in mobile_resource_types
        for index in range(1, 5)
    ]
    mobile_targets.extend(
        [
            ("TOW", "牵引车", 1),
            ("TOW", "牵引车", 2),
        ]
    )
    for resource_code, resource_name, index in mobile_targets:
        target_id = f"MOB-{resource_code}-{index:02d}"
        emergency_items.append(
            {
                "emergency": (
                    f"移动{resource_name}资源{target_id}"
                    "在保障过程中发生故障"
                )
            }
        )

    runway_causes = (
        "设备异常",
        "道面局部受损",
        "区域内存在障碍物",
        "状态检测异常",
        "通行条件不满足",
        "安全区域受限",
        "照明设备异常",
        "拦阻装置异常占用",
        "引导标志异常",
        "区域内存在作业冲突",
        "道面受到污染",
        "消防保障区域被占用",
        "临时检查任务占用",
        "出口通道受阻",
        "连接通道通行受限",
        "维护作业占用",
    )
    for index, cause in enumerate(runway_causes):
        runway_id = f"R{index % 3 + 1}"
        emergency_items.append(
            {
                "emergency": (
                    f"起飞跑道{runway_id}因{cause}停止使用"
                )
            }
        )

    path_stands = (
        "A1", "A2", "A3", "A4", "A5", "A6",
        "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8",
        "C1", "C2",
    )
    for index, stand_id in enumerate(path_stands):
        landing_id = "L1" if index % 2 == 0 else "L2"
        target_id = f"SEG-{landing_id}-{stand_id}"
        emergency_items.append(
            {
                "emergency": (
                    f"{landing_id}至{stand_id}之间的路径"
                    f"{target_id}因局部区域受限不可通行"
                )
            }
        )

    for index in range(1, 15):
        aircraft_id = f"AC{index:02d}"
        planned_minutes = 8 * 60 + (index - 1) * 3
        delay_minutes = random_generator.randint(2, 15)
        actual_minutes = planned_minutes + delay_minutes
        planned_time = (
            f"{planned_minutes // 60:02d}:{planned_minutes % 60:02d}"
        )
        actual_time = (
            f"{actual_minutes // 60:02d}:{actual_minutes % 60:02d}"
        )
        emergency_items.append(
            {
                "emergency": (
                    f"舰载机{aircraft_id}计划于{planned_time}到达，"
                    f"现延迟{delay_minutes}分钟，预计于{actual_time}到达"
                )
            }
        )

    support_stands = (
        "A1", "A2", "A3", "A4", "A5", "A6",
        "B1", "B2", "B3", "B4", "B5", "B6", "B7",
    )
    for stand_id in support_stands:
        emergency_items.append(
            {
                "emergency": (
                    f"保障站位{stand_id}发生故障并停止使用"
                )
            }
        )

    return emergency_items


def build_emergency_training_set(
    random_seed: int | None = 20260731,
) -> list[dict[str, str]]:
    """按照近似均匀的类型数量构建特情训练集。

    输入：
        random_seed（int | None）：
            舰载机随机延迟分钟数的种子。默认值用于保证训练集
            可复现；设为None时，每次运行生成不同的延迟分钟数。

    输出：
        list[dict[str, str]]：
        包含100个独立特情的训练集。其中，固定资源故障、移动
        资源故障、跑道故障和路径规划故障各17条，舰载机延迟
        到达和保障站位故障各16条。每个列表项只包含emergency
        字段，且不与默认测试集中的特情重复。
    """

    random_generator = random.Random(random_seed)
    training_items: list[dict[str, str]] = []
    test_emergencies = {
        item["emergency"]
        for item in build_emergency_test_set()
    }

    fixed_resource_types = (
        ("POWER", "供电"),
        ("HYDRAULIC", "液压"),
        ("FUEL", "燃油"),
        ("OXYGEN", "供氧"),
    )
    fixed_failure_modes = (
        "启动失败",
        "输出参数异常",
        "控制模块失效",
        "接口连接异常",
        "保护装置触发",
        "状态反馈中断",
        "输出能力下降",
        "内部组件异常",
        "供给压力不足",
        "通信链路中断",
        "设备过载停机",
        "执行机构失效",
        "监测数据异常",
        "供给过程意外中止",
        "无法响应控制指令",
        "输出状态不稳定",
        "自检未通过",
    )
    fixed_targets = [
        (zone, resource_code, resource_name, index)
        for zone in ("C", "B", "A")
        for resource_code, resource_name in reversed(
            fixed_resource_types
        )
        for index in (2, 1)
    ]
    for item_index, failure_mode in enumerate(fixed_failure_modes):
        zone, resource_code, resource_name, index = fixed_targets[
            item_index
        ]
        target_id = f"FIX-{zone}-{resource_code}-{index:02d}"
        training_items.append(
            {
                "emergency": (
                    f"{zone}区固定{resource_name}资源{target_id}"
                    f"{failure_mode}，无法继续执行当前保障作业"
                )
            }
        )

    mobile_resource_types = (
        ("POWER", "供电"),
        ("HYDRAULIC", "液压"),
        ("FUEL", "燃油"),
        ("OXYGEN", "供氧"),
    )
    mobile_targets = [
        (resource_code, resource_name, index)
        for resource_code, resource_name in mobile_resource_types
        for index in range(5, 9)
    ]
    mobile_targets.append(("TOW", "牵引车", 3))
    for item_index, (
        resource_code,
        resource_name,
        index,
    ) in enumerate(mobile_targets, start=1):
        target_id = f"MOB-{resource_code}-{index:02d}"
        training_items.append(
            {
                "emergency": (
                    f"移动{resource_name}资源{target_id}"
                    f"在第{item_index}项保障任务执行期间失效"
                )
            }
        )

    runway_causes = (
        "导航引导设备故障",
        "通信设备失效",
        "甲板作业车辆占道",
        "保障物资散落",
        "安全检查未通过",
        "跑道边界标志缺失",
        "监视设备异常",
        "气象条件临时变化",
        "消防设备异常",
        "牵引作业占用",
        "舰载机停留超时",
        "跑道入口被占用",
        "跑道末端区域受限",
        "异物检测系统告警",
        "紧急保障任务占用",
        "地面引导信号中断",
        "运行状态信息缺失",
    )
    for index, cause in enumerate(runway_causes):
        runway_id = f"R{(index + 1) % 3 + 1}"
        training_items.append(
            {
                "emergency": (
                    f"起飞跑道{runway_id}因{cause}暂时关闭"
                )
            }
        )

    path_stands = (
        "A1", "A2", "A3", "A4", "A5", "A6",
        "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8",
        "C1", "C2", "C3",
    )
    for index, stand_id in enumerate(path_stands):
        runway_id = f"R{index % 3 + 1}"
        target_id = f"SEG-{stand_id}-{runway_id}"
        training_items.append(
            {
                "emergency": (
                    f"保障站位{stand_id}至起飞跑道{runway_id}的"
                    f"路径{target_id}因通道异常无法使用"
                )
            }
        )

    for index in range(1, 17):
        aircraft_id = f"AC{index:02d}"
        planned_minutes = 8 * 60 + (index - 1) * 3
        planned_time = (
            f"{planned_minutes // 60:02d}:{planned_minutes % 60:02d}"
        )
        delay_minutes = random_generator.randint(2, 15)
        actual_minutes = planned_minutes + delay_minutes
        actual_time = (
            f"{actual_minutes // 60:02d}:{actual_minutes % 60:02d}"
        )
        emergency = (
            f"舰载机{aircraft_id}计划于{planned_time}到达，"
            f"现延迟{delay_minutes}分钟，预计于{actual_time}到达"
        )
        while emergency in test_emergencies:
            delay_minutes = 2 + (delay_minutes - 1) % 14
            actual_minutes = planned_minutes + delay_minutes
            actual_time = (
                f"{actual_minutes // 60:02d}:"
                f"{actual_minutes % 60:02d}"
            )
            emergency = (
                f"舰载机{aircraft_id}计划于{planned_time}到达，"
                f"现延迟{delay_minutes}分钟，预计于{actual_time}到达"
            )
        training_items.append({"emergency": emergency})

    support_stands = (
        "B8", "C1", "C2", "C3", "C4", "C5",
        "A1", "A2", "A3", "A4", "A5", "A6",
        "B1", "B2", "B3", "B4",
    )
    stand_failure_causes = (
        "系留装置异常",
        "供电接口损坏",
        "液压接口异常",
        "燃油接口失效",
        "供氧接口异常",
        "安全区域被占用",
        "地面标志缺失",
        "保障设备无法接入",
        "作业空间受到限制",
        "停放状态检测异常",
        "防护装置失效",
        "通信接口中断",
        "牵引通道被占用",
        "邻近区域存在冲突",
        "保障条件不满足",
        "站位状态信息异常",
    )
    for stand_id, failure_cause in zip(
        support_stands,
        stand_failure_causes,
    ):
        training_items.append(
            {
                "emergency": (
                    f"保障站位{stand_id}因{failure_cause}无法使用"
                )
            }
        )

    return training_items


def write_emergency_json(
    emergency_items: list[dict[str, str]],
    output_path: str | Path,
) -> Path:
    """将特情信息列表写入JSON文件。

    输入：
        emergency_items（list[dict[str, str]]）：
            待输出的特情信息列表。每个列表项只能包含一个
            emergency字段。
        output_path（str | Path）：
            JSON文件的输出路径。

    输出：
        Path：
        实际生成的JSON文件路径。

    异常：
        ValueError：
            列表项不是字典、字段不唯一或特情内容为空时抛出。
    """

    for index, item in enumerate(emergency_items):
        if not isinstance(item, dict):
            raise ValueError(f"第{index + 1}个特情项不是字典")
        if set(item) != {"emergency"}:
            raise ValueError(f"第{index + 1}个特情项只能包含emergency字段")
        if not isinstance(item["emergency"], str) or not item["emergency"]:
            raise ValueError(f"第{index + 1}个特情项内容为空")

    json_path = Path(output_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as file:
        json.dump(emergency_items, file, ensure_ascii=False, indent=2)
    return json_path


if __name__ == "__main__":
    test_output_path = Path(__file__).with_name(
        "maeh_emergency_test_set.json"
    )
    training_output_path = Path(__file__).with_name(
        "maeh_emergency_training_set.json"
    )
    test_items = build_emergency_test_set()
    training_items = build_emergency_training_set()
    test_emergencies = {item["emergency"] for item in test_items}
    training_emergencies = {
        item["emergency"] for item in training_items
    }
    if test_emergencies & training_emergencies:
        raise ValueError("训练集与测试集包含重复特情")
    write_emergency_json(
        test_items,
        test_output_path,
    )
    write_emergency_json(
        training_items,
        training_output_path,
    )
