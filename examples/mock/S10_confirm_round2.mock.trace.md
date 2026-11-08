# 运行 Trace

模式：mock；模型：scripted-mock；状态：completed

离线固定脚本，只验证流程；不证明真实模型决策效果。

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M01"} | 读取 M01（basic） | check_rules {"material_id": "M01", "scope": "basic"} | 离线脚本验证此步骤 |
| 2 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M01", "scope": "basic"} | M01 审核 pass：未发现风险 | query_slots {"date": "2026-11-10"} | 离线脚本验证此步骤 |
| 3 | query_slots | {"reason": "离线脚本验证此步骤", "channel": "douyin", "date": "2026-11-10", "from": "08:00", "to": "21:00"} | 08:00 available；09:00 available；10:00 available；11:00 available；12:00 available；13:00 available；14:00 available；15:00 available；16:00 available；17:00 occupied(M92)；18:00 occupied(M90)；19:00 held_by_this_request(M01)；20:00 available；21:00 available | request_confirmation {"material_id": "M01", "proposed_slot": "2026-11-10T19:00"} | 离线脚本验证此步骤 |
| 4 | request_confirmation | {"reason": "离线脚本验证此步骤", "material_id": "M01", "type": "time_change", "question": "18:00 被 M90 占用，是否改到 19:00？", "options": ["同意", "补充信息或拒绝"], "proposed_slot": "2026-11-10T19:00"} | M01 time_change：confirmed | save_schedule_draft {} | 离线脚本验证此步骤 |
| 5 | save_schedule_draft | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M01", "review_status": "approved", "risk_reasons": [], "slot": {"channel": "douyin", "start": "2026-11-10T19:00"}, "confirmation_status": "confirmed", "confirmation_ids": ["C-cb7a91b624"]}]} | 草稿 updated（v2，未发布） | submit_report {} | 离线脚本验证此步骤 |
| 6 | submit_report | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M01", "review_status": "approved", "risk_reasons": [], "suggested_slot": "2026-11-10T19:00", "confirmation_status": "confirmed", "pending_items": []}], "overall_note": "仅生成草稿，未发布"} | 报告已接收；保存状态以工具记录为准 | 结束：completed | 离线脚本验证此步骤 |

Token 用量：{"prompt_tokens": 0, "completion_tokens": 0}
