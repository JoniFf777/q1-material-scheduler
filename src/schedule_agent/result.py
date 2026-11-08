"""Build public results from facts. Model prose is never the final summary."""
import copy

from .domain.guards import validate
from .trace import safe_text


def save_result(observation):
    if observation is None:
        return {"status": "not_saved"}
    if observation["ok"]:
        data = copy.deepcopy(observation["data"])
        return {"status": data.pop("result"), **data}
    return {"status": "failed", "error_code": observation["error_code"],
            "message": observation["message"]}


def finalize(ctx, report=None, termination=None):
    saved = save_result(ctx.save_observation)
    warnings = []
    reports = {i["material_id"]: i for i in (report or {}).get("items", [])}
    source = ctx.saved_items if saved["status"] in ("created", "updated", "duplicate") else ctx.attempt_items
    if source is None:
        source = []
        for req in ctx.items:
            mid = req["material_id"]
            item = reports.get(mid, {})
            start = item.get("suggested_slot")
            records = [c for c in ctx.confirmation_records.values() if c["material_id"] == mid
                       and (c["type"] != "time_change" or c.get("proposed_slot") == start)]
            source.append({"material_id": mid, "review_status": item.get("review_status", "unknown"),
                "risk_reasons": item.get("risk_reasons", []),
                "slot": {"channel": req["channel"], "start": start} if start else None,
                "confirmation_status": item.get("confirmation_status", "not_required"),
                "confirmation_ids": [c["id"] for c in records]})
        source = ctx.canonical_items(source)
        # Treat an unsafe report as a claim, never as evidence of a valid slot or approval.
        unsafe = {v["material_id"] for v in validate(ctx, source) if v["code"] in (
            "RULE_CHECK_REQUIRED", "BLOCKED_ITEM_HAS_SLOT", "HARD_CONSTRAINT_VIOLATION",
            "CONFIRMATION_REQUIRED", "UNAUTHORIZED_CONFIRMATION", "SLOT_CONFLICT", "INVALID_SLOT")}
        for item in source:
            if item["material_id"] in unsafe:
                if item.get("slot") or item["confirmation_status"] == "confirmed":
                    warnings.append(f"{item['material_id']}：报告中的排期或确认缺少事实支持，已纠正")
                item["slot"] = None
                item["confirmation_status"] = "pending" if item["confirmation_ids"] else "not_required"
    sources = {i["material_id"]: i for i in source}
    items = []
    verdict_review = {"pass": "approved", "confirm": "needs_confirmation", "need_info": "need_info", "block": "blocked", "uncertain": "unknown"}
    for req in ctx.items:
        mid = req["material_id"]
        item = copy.deepcopy(sources.get(mid, {}))
        review = "need_info" if mid in ctx.missing else verdict_review.get(ctx.checked.get(mid), "unknown")
        slot = item.get("slot")
        if review in ("blocked", "need_info", "unknown"):
            slot = None
        records = [ctx.confirmation_records[cid] for cid in item.get("confirmation_ids", [])
                   if cid in ctx.confirmation_records]
        pending = [c["question"] for c in records if c["status"] == "pending"]
        confirmation = item.get("confirmation_status", "not_required")
        if confirmation == "confirmed" and (not records or any(c["status"] != "confirmed" for c in records)):
            confirmation = "pending" if records else "not_required"
            warnings.append(f"{mid}：确认状态已按用户答复纠正")
        facts = {"material_id": mid, "review_status": review,
            "risk_reasons": item.get("risk_reasons", []), "suggested_slot": slot["start"] if slot else None,
            "channel": slot["channel"] if slot else req["channel"],
            "slot_status": ("as_requested" if slot["start"] == req["preferred_time"] else "alternative") if slot else "none",
            "confirmation_status": confirmation, "pending_items": pending,
            "confirmation_ids": item.get("confirmation_ids", []), "draft_save_status": saved["status"]}
        reported = reports.get(mid)
        if reported and any(reported.get(k) != facts[k] for k in ("review_status", "suggested_slot", "confirmation_status", "risk_reasons")):
            warnings.append(f"{mid}：模型结论与工具事实不同，已采用工具事实")
        items.append(facts)
    if report and saved["status"] in ("failed", "not_saved") and any(
            word in report.get("overall_note", "") for word in ("已保存", "保存成功", "created", "updated", "duplicate")):
        warnings.append("模型声称保存成功，但保存记录不支持，已纠正")
    result = {"run_id": ctx.run_id, "request_key": ctx.key, "items": items,
        "draft_save": saved, "publish_action": "none", "consistency_warnings": warnings,
        "notice": "本系统仅生成排期草稿，未执行任何发布"}
    if termination in ("MAX_STEPS_REACHED", "MAX_TOOL_CALLS_REACHED"):
        result.update(status="incomplete", incomplete_reason=termination)
    elif termination:
        result.update(status="failed", failure_reason=termination)
    elif saved["status"] == "failed":
        result["status"] = "save_failed"
    elif saved["status"] == "not_saved":
        result.update(status="failed", failure_reason="DRAFT_NOT_SAVED")
    else:
        result["status"] = "completed_with_pending" if any(i["pending_items"] or i["confirmation_status"] == "pending" or i["review_status"] in ("need_info", "unknown") for i in items) else "completed"
    return safe_text(result)
