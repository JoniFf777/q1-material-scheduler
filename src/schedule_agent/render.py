from .trace import safe_text


def render_result(result):
    lines = [f"运行状态：{result['status']}", f"草稿保存：{result['draft_save']['status']}"]
    if result["draft_save"].get("error_code"):
        lines.append("保存错误：" + result["draft_save"]["error_code"])
    if result.get("failure_reason") or result.get("incomplete_reason"):
        lines.append("结束原因：" + (result.get("failure_reason") or result["incomplete_reason"]))
    for item in result["items"]:
        lines.append(f"{item['material_id']} | {item['review_status']} | {item['suggested_slot'] or '无建议时段'} | {item['confirmation_status']}")
        lines.extend("  风险：" + reason for reason in item["risk_reasons"])
        lines.extend("  待确认：" + question for question in item["pending_items"])
    lines.extend("一致性提醒：" + note for note in result["consistency_warnings"])
    lines.append(result["notice"])
    return safe_text("\n".join(lines))
