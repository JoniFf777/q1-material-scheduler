# 运行 Trace

模式：mock；模型：scripted-mock；状态：completed_with_pending

离线固定脚本，只验证流程；不证明真实模型决策效果。

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M04"} | 读取 M04（basic） | get_material {"material_id": "M05"} | 离线脚本验证此步骤 |
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M05"} | 读取 M05（basic） | get_material {"material_id": "M07"} | 离线脚本验证此步骤 |
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M07"} | 读取 M07（basic） | check_rules {"material_id": "M04", "scope": "basic"} | 离线脚本验证此步骤 |
| 2 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M04", "scope": "basic"} | M04 审核 uncertain：music 授权状态未知 | check_rules {"material_id": "M05", "scope": "basic"} | 离线脚本验证此步骤 |
| 2 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M05", "scope": "basic"} | M05 审核 confirm：用语风险：第一 | check_rules {"material_id": "M07", "scope": "basic"} | 离线脚本验证此步骤 |
| 2 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M07", "scope": "basic"} | M07 审核 uncertain：music 授权状态未知 | check_rules {"material_id": "M04", "scope": "license"} | 离线脚本验证此步骤 |
| 3 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M04", "scope": "license"} | M04 审核 block：music 授权已过期（2026-10-31） | check_rules {"material_id": "M07", "scope": "license"} | 离线脚本验证此步骤 |
| 3 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M07", "scope": "license"} | M07 审核 pass：未发现风险 | query_slots {"date": "2026-11-10"} | 离线脚本验证此步骤 |
| 4 | query_slots | {"reason": "离线脚本验证此步骤", "channel": "xiaohongshu", "date": "2026-11-10", "from": "08:00", "to": "21:00"} | 08:00 available；09:00 available；10:00 available；11:00 available；12:00 available；13:00 available；14:00 available；15:00 available；16:00 available；17:00 available；18:00 available；19:00 available；20:00 available；21:00 available | query_slots {"date": "2026-11-10"} | 离线脚本验证此步骤 |
| 4 | query_slots | {"reason": "离线脚本验证此步骤", "channel": "douyin", "date": "2026-11-10", "from": "08:00", "to": "21:00"} | 08:00 available；09:00 available；10:00 available；11:00 available；12:00 available；13:00 available；14:00 available；15:00 available；16:00 available；17:00 occupied(M92)；18:00 occupied(M90)；19:00 available；20:00 available；21:00 available | request_confirmation {"material_id": "M05"} | 离线脚本验证此步骤 |
| 5 | request_confirmation | {"reason": "离线脚本验证此步骤", "material_id": "M05", "type": "risk_ack", "question": "标题含极限用语‘第一’，请确认风险或修改素材。", "options": ["同意", "补充信息或拒绝"]} | M05 risk_ack：pending | save_schedule_draft {} | 离线脚本验证此步骤 |
| 6 | save_schedule_draft | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M04", "review_status": "blocked", "risk_reasons": [], "slot": null, "confirmation_status": "not_required", "confirmation_ids": []}, {"material_id": "M05", "review_status": "needs_confirmation", "risk_reasons": [], "slot": {"channel": "xiaohongshu", "start": "2026-11-10T12:00"}, "confirmation_status": "pending", "confirmation_ids": ["C-1ad5c3fa5f"]}, {"material_id": "M07", "review_status": "approved", "risk_reasons": [], "slot": {"channel": "douyin", "start": "2026-11-10T21:00"}, "confirmation_status": "not_required", "confirmation_ids": []}]} | 草稿 created（v1，未发布） | submit_report {} | 离线脚本验证此步骤 |
| 7 | submit_report | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M04", "review_status": "blocked", "risk_reasons": [], "suggested_slot": null, "confirmation_status": "not_required", "pending_items": []}, {"material_id": "M05", "review_status": "needs_confirmation", "risk_reasons": [], "suggested_slot": "2026-11-10T12:00", "confirmation_status": "pending", "pending_items": []}, {"material_id": "M07", "review_status": "approved", "risk_reasons": [], "suggested_slot": "2026-11-10T21:00", "confirmation_status": "not_required", "pending_items": []}], "overall_note": "仅生成草稿，未发布"} | 报告已接收；保存状态以工具记录为准 | 结束：completed_with_pending | 离线脚本验证此步骤 |

Token 用量：{"prompt_tokens": 0, "completion_tokens": 0}
