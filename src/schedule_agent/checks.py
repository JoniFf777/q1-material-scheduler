import json

from .result import save_result
from .trace import FORBIDDEN_CLAIMS


def check_invariants(result, trace, request, store, confirmations=None):
    errors = []
    text = json.dumps({"result": result, "trace": trace}, ensure_ascii=False)
    if any(word in text for word in FORBIDDEN_CLAIMS):
        errors.append("I1: 存在发布成功表述")
    saves = [s["observation"] for s in trace["steps"] if s["tool"] == "save_schedule_draft"]
    if result["draft_save"] != save_result(saves[-1] if saves else None):
        errors.append("I2: 保存状态与最后一次工具返回不同")
    requirements = {i["material_id"]: i for i in request.get("items", [])}
    for item in result["items"]:
        mid = item["material_id"]
        req = requirements.get(mid)
        if not req:
            errors.append(f"结果包含请求以外的素材：{mid}")
            continue
        start = item["suggested_slot"]
        if start and start != req["preferred_time"]:
            confirmed = any(c.get("material_id") == mid and c.get("type") == "time_change"
                and c.get("proposed_slot") == start and c.get("status") == "confirmed" for c in confirmations or [])
            if item["confirmation_status"] != "pending" and not (item["confirmation_status"] == "confirmed" and confirmed):
                errors.append(f"I3: {mid} 替代时段缺少确认")
        if req.get("time_policy") == "fixed" and start not in (None, req["preferred_time"]):
            errors.append(f"I4: {mid} fixed 时间被改变")
        if item["review_status"] in ("blocked", "need_info") and start:
            errors.append(f"I5: {mid} 不可排期却带时段")
    try:
        drafts = store.read()["drafts"]
    except (OSError, ValueError, KeyError):
        errors.append("I6: 草稿库不可验证")
        drafts = []
    keys = [d["idempotency_key"] for d in drafts]
    if len(keys) != len(set(keys)):
        errors.append("I6: 幂等键重复")
    limit = result.get("incomplete_reason") in ("MAX_STEPS_REACHED", "MAX_TOOL_CALLS_REACHED")
    if (result["status"] == "incomplete") != limit:
        errors.append("I7: incomplete 与限额终止不一致")
    if limit:
        reason = result["incomplete_reason"]
        reached = ((reason == "MAX_STEPS_REACHED" and len(trace["model_calls"]) >= trace["limits"]["max_steps"])
                   or (reason == "MAX_TOOL_CALLS_REACHED" and len(trace["steps"]) >= trace["limits"]["max_tool_calls"]))
        if not reached:
            errors.append("I7: 记录中未达到指定限额")
    return errors
