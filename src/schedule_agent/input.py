"""Validate structured input before it reaches tools or persistence."""
import copy
import re
from datetime import datetime, time


def validate_scenario(scenario):
    scenario = copy.deepcopy(scenario)
    if not isinstance(scenario, dict) or not isinstance(scenario.get("request"), dict):
        raise ValueError("输入需要 request 对象")
    if not isinstance(scenario.get("name"), str) or not re.fullmatch(r"[A-Za-z0-9_-]+", scenario["name"]):
        raise ValueError("场景 name 须为不带路径的英文、数字、下划线或连字符")
    if not isinstance(scenario.get("setup", {}), dict) or not isinstance(scenario.get("expect", {}), dict):
        raise ValueError("setup 与 expect 须为对象")
    request = scenario["request"]
    if "scope" in request and request["scope"] != "pending":
        raise ValueError("未知 scope")
    if set(request) - {"items", "scope", "defaults", "note"}:
        raise ValueError("未知请求字段")
    if request.get("scope") == "pending":
        if "items" in request:
            raise ValueError("scope=pending 与 items 不可同时提供")
        records = [request.get("defaults", {})]
    else:
        records = request.get("items")
        if not isinstance(records, list) or not records:
            raise ValueError("request.items 不能为空")
        mids = [item.get("material_id") for item in records if isinstance(item, dict)]
        if len(mids) != len(records) or any(not isinstance(mid, str) or not mid for mid in mids) or len(set(mids)) != len(mids):
            raise ValueError("素材 ID 须为非空字符串且不可重复")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("请求条目须为对象")
        if not isinstance(record.get("channel"), str) or not record["channel"]:
            raise ValueError("必须指定 channel")
        allowed = {"material_id", "channel", "preferred_time", "time_policy", "constraints"}
        if set(record) - allowed:
            raise ValueError("未知请求条目字段")
        start = record.get("preferred_time", "")
        parsed = datetime.strptime(start, "%Y-%m-%dT%H:%M")
        if parsed.strftime("%Y-%m-%dT%H:%M") != start:
            raise ValueError("时间须使用 YYYY-MM-DDTHH:MM")
        record.setdefault("time_policy", "flexible")
        if record["time_policy"] not in ("fixed", "flexible"):
            raise ValueError("未知 time_policy")
        constraints = record.setdefault("constraints", {})
        if not isinstance(constraints, dict) or set(constraints) - {"date_fixed", "channel_fixed", "not_before", "not_after"}:
            raise ValueError("约束字段无效")
        for key in ("date_fixed", "channel_fixed"):
            if key in constraints and not isinstance(constraints[key], bool):
                raise ValueError("约束开关须为布尔值")
        for key in ("not_before", "not_after"):
            if key in constraints:
                value = constraints[key]
                if time.fromisoformat(value).strftime("%H:%M") != value:
                    raise ValueError("约束时间须使用 HH:MM")
        if constraints.get("not_before", "00:00") > constraints.get("not_after", "23:59"):
            raise ValueError("约束窗口为空")
    confirmations = scenario.get("confirmations", [])
    if not isinstance(confirmations, list):
        raise ValueError("confirmations 须为数组")
    for reply in confirmations:
        if (not isinstance(reply, dict) or not isinstance(reply.get("material_id"), str)
                or reply.get("type") not in ("time_change", "risk_ack", "info_needed", "constraint_relax")
                or reply.get("status") not in ("confirmed", "rejected")):
            raise ValueError("用户确认记录格式无效")
        if reply["type"] == "time_change" and not reply.get("proposed_slot"):
            raise ValueError("时间确认须指定 proposed_slot")
        if reply.get("proposed_slot"):
            value = reply["proposed_slot"]
            if datetime.strptime(value, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%dT%H:%M") != value:
                raise ValueError("用户确认中的时段格式无效")
    return scenario
