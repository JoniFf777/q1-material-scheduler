# 运行 Trace

模式：mock；模型：scripted-mock；状态：completed_with_pending

离线固定脚本，只验证流程；不证明真实模型决策效果。

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"material_id": "M01", "reason": "离线固定脚本验证流程"} | 读取 M01（basic） | check_rules {"material_id": "M01", "scope": "basic"} | 离线固定脚本验证流程 |
| 2 | check_rules | {"material_id": "M01", "scope": "basic", "reason": "离线固定脚本验证流程"} | M01 审核 pass：未发现风险 | query_slots {"date": "2026-11-10"} | 离线固定脚本验证流程 |
| 3 | query_slots | {"channel": "douyin", "date": "2026-11-10", "from": "17:00", "to": "21:00", "reason": "离线固定脚本验证流程"} | 17:00 occupied(M92)；18:00 occupied(M90)；19:00 available；20:00 available；21:00 available | request_confirmation {"material_id": "M01", "proposed_slot": "2026-11-10T19:00"} | 离线固定脚本验证流程 |
| 4 | request_confirmation | {"material_id": "M01", "type": "time_change", "question": "18:00 被 M90 占用，是否改到 19:00？", "options": ["同意", "拒绝"], "proposed_slot": "2026-11-10T19:00", "reason": "离线固定脚本验证流程"} | M01 time_change：pending | save_schedule_draft {} | 离线固定脚本验证流程 |
| 5 | save_schedule_draft | {"items": [{"material_id": "M01", "review_status": "approved", "risk_reasons": [], "slot": {"channel": "douyin", "start": "2026-11-10T19:00"}, "confirmation_status": "pending", "confirmation_ids": ["C-cb7a91b624"]}], "reason": "离线固定脚本验证流程"} | 草稿 created（v1，未发布） | submit_report {} | 离线固定脚本验证流程 |
| 6 | submit_report | {"items": [{"material_id": "M01", "review_status": "approved", "risk_reasons": [], "suggested_slot": "2026-11-10T19:00", "confirmation_status": "pending", "pending_items": ["确认改到19:00"]}], "overall_note": "草稿待确认", "reason": "离线固定脚本验证流程"} | 报告已接收；保存状态以工具记录为准 | 结束：completed_with_pending | 离线固定脚本验证流程 |

Token 用量：{"prompt_tokens": 0, "completion_tokens": 0}
