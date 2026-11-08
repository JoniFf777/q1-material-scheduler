"""The save boundary: model arguments are untrusted; facts come from RunContext."""
from datetime import datetime


def validate(ctx, items):
    violations = []

    def add(code, mid, message):
        violations.append({"code": code, "material_id": mid, "message": message})

    ids = [i["material_id"] for i in items]
    expected = {i["material_id"] for i in ctx.items}
    if not expected or set(ids) != expected or len(ids) != len(set(ids)):
        add("MISSING_ITEMS", None, "必须且只能覆盖本请求的全部素材，不可重复")
    used_slots = set()
    for item in items:
        mid = item["material_id"]
        requirement = ctx.requirement(mid)
        if not requirement:
            continue
        verdict = ctx.checked.get(mid)
        review = item["review_status"]
        slot = item.get("slot")
        confirmation = item["confirmation_status"]
        if verdict is None and mid not in ctx.missing:
            add("RULE_CHECK_REQUIRED", mid, "本次运行尚未审核")
        allowed = {"pass": {"approved"}, "confirm": {"needs_confirmation"},
                   "uncertain": {"unknown"}, "need_info": {"need_info"}, "block": {"blocked"}}
        if mid in ctx.missing:
            allowed_review = {"need_info"}
        else:
            allowed_review = allowed.get(verdict, {"unknown"})
        if review not in allowed_review:
            add("RISK_STATUS_MISMATCH", mid, "审核结论与事实不一致")
        if review in ("blocked", "need_info", "unknown") and slot:
            add("BLOCKED_ITEM_HAS_SLOT", mid, "不可排期的素材不能带时段")
        refs = item.get("confirmation_ids", [])
        records = [ctx.confirmation_records[c] for c in refs if c in ctx.confirmation_records
                   and ctx.confirmation_records[c]["material_id"] == mid]
        if len(records) != len(refs):
            add("CONFIRMATION_REQUIRED", mid, "确认引用无效")
        start = slot["start"] if slot else None
        kinds = set()
        if slot and start != requirement["preferred_time"]:
            kinds.add("time_change")
        if verdict == "confirm":
            kinds.add("risk_ack")
        if review == "need_info":
            kinds.add("info_needed")
        if review == "approved" and not slot:
            kinds.add("constraint_relax")
        if kinds and confirmation not in ("pending", "confirmed"):
            add("CONFIRMATION_REQUIRED", mid, "需要用户确认")
        for kind in kinds:
            matching = [r for r in records if r["type"] == kind
                        and (kind != "time_change" or r.get("proposed_slot") == start)]
            if not matching or not any(r["status"] in ("pending", "confirmed") for r in matching):
                add("CONFIRMATION_REQUIRED", mid, f"缺少 {kind} 确认记录")
            if confirmation == "confirmed" and not any(r["status"] == "confirmed" for r in matching):
                add("UNAUTHORIZED_CONFIRMATION", mid, f"{kind} 未经用户同意")
        if confirmation == "confirmed" and (not records or any(r["status"] != "confirmed" for r in records)):
            add("UNAUTHORIZED_CONFIRMATION", mid, "confirmed 只能来自用户答复")
        if confirmation == "pending" and not records:
            add("CONFIRMATION_REQUIRED", mid, "pending 必须有登记的确认项")
        if not slot:
            continue
        try:
            dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
            if dt.strftime("%Y-%m-%dT%H:%M") != start:
                raise ValueError("noncanonical time")
        except ValueError:
            add("INVALID_SLOT", mid, "时间格式无效")
            continue
        cfg = ctx.repo.slot_config
        if dt.minute != 0 or not cfg["start_hour"] <= dt.hour <= cfg["end_hour"] or slot["channel"] not in cfg["channels"]:
            add("INVALID_SLOT", mid, "不在渠道和整点时段网格中")
        constraints = requirement.get("constraints", {})
        hard = []
        if requirement.get("time_policy", "flexible") == "fixed" and start != requirement["preferred_time"]:
            hard.append("fixed 时间")
        if constraints.get("date_fixed", True) and start[:10] != requirement["preferred_time"][:10]:
            hard.append("日期")
        if constraints.get("channel_fixed", True) and slot["channel"] != requirement["channel"]:
            hard.append("渠道")
        if constraints.get("not_before") and start[11:] < constraints["not_before"]:
            hard.append("not_before")
        if constraints.get("not_after") and start[11:] > constraints["not_after"]:
            hard.append("not_after")
        embargo = ctx.views.get(mid, {}).get("embargo_until")
        if embargo and start < embargo:
            hard.append("素材禁发期")
        # A specific user relaxation must match the actual proposal. A generic yes is insufficient.
        relaxed = ctx.approved_by_user(mid, "constraint_relax", start)
        if hard and not relaxed:
            add("HARD_CONSTRAINT_VIOLATION", mid, "违反：" + "、".join(hard))
        for key in ("copyright", "music"):
            info = ctx.views.get(mid, {}).get(key, {})
            expiry = info.get("license_expiry")
            if expiry and expiry < start[:10]:
                add("RISK_STATUS_MISMATCH", mid, f"{key} 在建议日期已过期")
        status, _ = ctx.repo.occupancy(ctx, slot["channel"], start)
        identity = (slot["channel"], start)
        if status == "occupied" or identity in used_slots:
            add("SLOT_CONFLICT", mid, "与已有排期、其他草稿或本请求条目冲突")
        used_slots.add(identity)
    return violations
