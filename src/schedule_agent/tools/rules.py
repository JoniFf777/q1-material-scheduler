from .common import ok, error

PRIORITY = {"pass": 0, "confirm": 1, "uncertain": 2, "need_info": 3, "block": 4}


def check_rules(ctx, material_id, scope="basic", publish_date=None):
    requirement = ctx.requirement(material_id)
    if not requirement:
        return error("INVALID_ARGUMENTS", "素材不在本请求中")
    target_date = requirement["preferred_time"][:10]
    if publish_date and publish_date != target_date:
        return error("INVALID_ARGUMENTS", "审核日期须与请求日期一致")
    if material_id not in ctx.views:
        material = ctx.repo.material(material_id)
        if material is None:
            ctx.missing.add(material_id)
            return error("NOT_FOUND", f"素材 {material_id} 不存在")
        material.pop("extended", None)
        ctx.views[material_id] = material
    view = ctx.views[material_id]
    if scope == "license":
        for key, value in ctx.repo.license_db.get(material_id, {}).items():
            view.setdefault(key, {}).update(value)
    if scope == "content":
        view["content_checked"] = True
    findings = []

    def add(rule_id, severity, message):
        findings.append(dict(rule_id=rule_id, severity=severity, message=message))

    def field_value(path):
        value = view
        for part in path.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        return value
    required_fields = list(ctx.repo.rules["R01"]["required_fields"])
    if view.get("type") == "video":
        required_fields += ctx.repo.rules["R01"]["video_required_fields"]
    fields = {field: field_value(field) for field in required_fields}
    for field, value in fields.items():
        if value is None or value == "":
            add("R01", "need_info", f"缺少 {field}")
    for key, rule_id in (("copyright", "R02"), ("music", "R03")):
        license_info = view.get(key, {})
        status = license_info.get("license_status")
        expiry = license_info.get("license_expiry")
        if status == "expired" or (expiry and expiry < target_date):
            add(rule_id, "block", f"{key} 授权已过期（{expiry or '未记录日期'}）")
        elif status == "unknown":
            add(rule_id, "uncertain", f"{key} 授权状态未知")
    text = view.get("title", "") + " " + view.get("description", "")
    if view.get("content_checked"):
        text += " " + view.get("subtitles", "")
    for group, severity in (("prohibited", "block"), ("extreme", "confirm")):
        for term in ctx.repo.terms[group]:
            if term in text:
                add("R04", severity, f"用语风险：{term}")
    verdict = max((f["severity"] for f in findings), key=PRIORITY.get, default="pass")
    ctx.checked[material_id] = verdict
    ctx.findings[material_id] = findings
    ctx.check_dates[material_id] = target_date
    return ok(dict(material_id=material_id, scope=scope, verdict=verdict, findings=findings),
              f"{material_id} 审核 {verdict}：" + ("；".join(f["message"] for f in findings) or "未发现风险"))
