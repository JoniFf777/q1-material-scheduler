# 运行 Trace

模式：mock；模型：scripted-mock；状态：completed_with_pending

离线固定脚本，只验证流程；不证明真实模型决策效果。

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M03"} | 读取 M03（basic） | get_material {"material_id": "M08"} | 离线脚本验证此步骤 |
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M08"} | 素材 M08 不存在 | check_rules {"material_id": "M03", "scope": "basic"} | 离线脚本验证此步骤 |
| 2 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M03", "scope": "basic"} | M03 审核 need_info：缺少 copyright.owner；缺少 copyright.license_status；缺少 duration_sec | get_material {"material_id": "M03"} | 离线脚本验证此步骤 |
| 3 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M03", "detail": "full"} | 读取 M03（full） | check_rules {"material_id": "M03", "scope": "basic"} | 离线脚本验证此步骤 |
| 4 | check_rules | {"reason": "离线脚本验证此步骤", "material_id": "M03", "scope": "basic"} | M03 审核 need_info：缺少 copyright.owner；缺少 copyright.license_status | request_confirmation {"material_id": "M03"} | 离线脚本验证此步骤 |
| 5 | request_confirmation | {"reason": "离线脚本验证此步骤", "material_id": "M03", "type": "info_needed", "question": "请补充版权方和授权状态。", "options": ["同意", "补充信息或拒绝"]} | M03 info_needed：pending | request_confirmation {"material_id": "M08"} | 离线脚本验证此步骤 |
| 5 | request_confirmation | {"reason": "离线脚本验证此步骤", "material_id": "M08", "type": "info_needed", "question": "素材 M08 不存在，请提供正确的素材 ID。", "options": ["同意", "补充信息或拒绝"]} | M08 info_needed：pending | save_schedule_draft {} | 离线脚本验证此步骤 |
| 6 | save_schedule_draft | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M03", "review_status": "need_info", "risk_reasons": [], "slot": null, "confirmation_status": "pending", "confirmation_ids": ["C-849768b35c"]}, {"material_id": "M08", "review_status": "need_info", "risk_reasons": [], "slot": null, "confirmation_status": "pending", "confirmation_ids": ["C-d04efbe430"]}]} | 草稿 created（v1，未发布） | submit_report {} | 离线脚本验证此步骤 |
| 7 | submit_report | {"reason": "离线脚本验证此步骤", "items": [{"material_id": "M03", "review_status": "need_info", "risk_reasons": [], "suggested_slot": null, "confirmation_status": "pending", "pending_items": []}, {"material_id": "M08", "review_status": "need_info", "risk_reasons": [], "suggested_slot": null, "confirmation_status": "pending", "pending_items": []}], "overall_note": "仅生成草稿，未发布"} | 报告已接收；保存状态以工具记录为准 | 结束：completed_with_pending | 离线脚本验证此步骤 |

Token 用量：{"prompt_tokens": 0, "completion_tokens": 0}
