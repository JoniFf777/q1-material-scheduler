# 运行 Trace

模式：mock；模型：scripted-mock；状态：completed_with_pending

离线固定脚本，只验证流程；不证明真实模型决策效果。

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M06"} | 读取 M06（basic） | check_rules {"material_id": "M06", "scope": "basic"} | 离线脚本验证此步骤 |
| 2 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M06", "scope": "basic"} | M06 审核 pass：未发现风险 | query_slots {"date": "2026-11-11"} | 离线脚本验证此步骤 |
| 3 | query_slots | {"reason": "离线脚本验证此步骤", "channel": "douyin", "date": "2026-11-11", "from": "08:00", "to": "21:00"} | 08:00 available；09:00 available；10:00 available；11:00 available；12:00 available；13:00 available；14:00 available；15:00 available；16:00 available；17:00 available；18:00 available；19:00 available；20:00 occupied(M91)；21:00 available | request_confirmation {"material_id": "M06"} | 离线脚本验证此步骤 |
| 4 | request_confirmation | {"reason": "离线脚本验证此步骤", "material_id": "M06", "type": "constraint_relax", "question": "20:00 被 M91 占用，请决定是否提出新的时间要求。", "options": ["同意", "补充信息或拒绝"]} | M06 constraint_relax：pending | save_schedule_draft {} | 离线脚本验证此步骤 |
| 5 | save_schedule_draft | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M06", "review_status": "approved", "risk_reasons": [], "slot": null, "confirmation_status": "pending", "confirmation_ids": ["C-2e4381ef17"]}]} | 草稿 created（v1，未发布） | submit_report {} | 离线脚本验证此步骤 |
| 6 | submit_report | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M06", "review_status": "approved", "risk_reasons": [], "suggested_slot": null, "confirmation_status": "pending", "pending_items": []}], "overall_note": "仅生成草稿，未发布"} | 报告已接收；保存状态以工具记录为准 | 结束：completed_with_pending | 离线脚本验证此步骤 |

Token 用量：{"prompt_tokens": 0, "completion_tokens": 0}
