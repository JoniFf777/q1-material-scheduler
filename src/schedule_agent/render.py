from .trace import safe_text


def render_result(result):
    save = result["draft_save"]["status"]
    pending = any(i["confirmation_status"] == "pending" for i in result["items"])
    save_text = {"created": "草稿已保存（待确认，未发布）" if pending else "草稿已保存（未发布）",
                 "updated": "草稿已更新（待确认，未发布）" if pending else "草稿已更新（未发布）",
                 "duplicate": "已存在相同草稿，未重复创建（未发布）",
                 "failed": "草稿保存失败", "not_saved": "草稿未保存"}[save]
    lines = [f"运行状态：{result['status']}", f"{save_text}；保存结果：{save}"]
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
