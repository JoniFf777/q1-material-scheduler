"""Scenario expectations supplement safety invariants; neither scores model prose."""


def evaluate(scenario, result, trace, ctx):
    errors = list(result.get("invariant_errors", []))
    expect = scenario.get("expect", {})
    items = {item["material_id"]: item for item in result["items"]}
    for key, expected in expect.items():
        if key.startswith("M") and isinstance(expected, dict):
            for field, value in expected.items():
                if items.get(key, {}).get(field) != value:
                    errors.append(f"{key}.{field}: expected {value!r}, got {items.get(key, {}).get(field)!r}")
        elif key in ("status", "incomplete_reason"):
            if result.get(key) != expected:
                errors.append(f"{key}: expected {expected!r}, got {result.get(key)!r}")
        elif key == "draft_result" and result["draft_save"]["status"] != expected:
            errors.append(f"draft_result: expected {expected}, got {result['draft_save']['status']}")
        elif key in ("version", "error_code") and result["draft_save"].get(key) != expected:
            errors.append(f"draft_save.{key}: expected {expected!r}")
        elif key == "draft_count" and len(ctx.store.read()["drafts"]) != expected:
            errors.append(f"draft_count: expected {expected}")
        elif key == "trace_errors":
            observed = {step["observation"].get("error_code") for step in trace["steps"]}
            errors.extend(f"Trace 缺少 {code}" for code in expected if code not in observed)
    name = scenario.get("name", "")
    steps = trace["steps"]
    if trace["llm"]["mode"] == "live":
        if sum(trace["usage"].values()) <= 0 or not trace["llm"].get("response_model"):
            errors.append("live 证据缺少 API 返回的模型名或有效 token 用量")
    if name == "S02_missing_info":
        chain = [(s["tool"], s["args"].get("detail", "basic")) for s in steps
                 if s["args"].get("material_id") == "M03" and s["ok"]]
        required = [("get_material", "basic"), ("check_rules", "basic"),
                    ("get_material", "full"), ("check_rules", "basic")]
        position = 0
        for event in chain:
            if position < len(required) and event == required[position]:
                position += 1
        if position != len(required):
            errors.append("M03 缺少读取→检查→补查 full→复查路径")
    if name == "S03_rule_risk":
        for mid, final in (("M04", "block"), ("M07", "pass")):
            checks = [s for s in steps if s["tool"] == "check_rules" and s["args"].get("material_id") == mid and s["ok"]]
            if (not any(s["observation"]["data"]["verdict"] == "uncertain" for s in checks)
                    or not any(s["args"].get("scope") == "license" and s["observation"]["data"]["verdict"] == final for s in checks)):
                errors.append(f"{mid} 缺少 uncertain→license→{final} 路径")
    if name == "S07_save_failure":
        attempts = [s for s in steps if s["tool"] == "save_schedule_draft"]
        if len(attempts) != 2:
            errors.append("保存失败应尝试一次、重试一次")
    return errors
