# 运行 Trace

模式：live；模型：deepseek-flash；状态：completed

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"material_id": "M01", "detail": "basic", "reason": "先读取素材基本信息用于审核"} | 读取 M01（basic） | check_rules {"material_id": "M01", "scope": "basic"} | 先读取素材基本信息用于审核 |
| 2 | check_rules | {"material_id": "M01", "scope": "basic", "reason": "按基础信息审核素材合规性", "publish_date": "2026-11-10"} | M01 审核 pass：未发现风险 | query_slots {"date": "2026-11-10"} | 按基础信息审核素材合规性 |
| 3 | query_slots | {"channel": "douyin", "date": "2026-11-10", "from": "18:00", "to": "21:00", "reason": "查询硬约束内可用时段"} | 18:00 available；19:00 occupied(M90)；20:00 available；21:00 available | save_schedule_draft {} | 查询硬约束内可用时段 |
| 4 | save_schedule_draft | {"items": [{"material_id": "M01", "review_status": "approved", "risk_reasons": [], "slot": {"channel": "douyin", "start": "2026-11-10T18:00"}, "confirmation_status": "not_required", "confirmation_ids": []}], "reason": "审核通过且首选时段可用，保存草稿"} | 草稿 updated（v2，未发布） | submit_report {} | 审核通过且首选时段可用，保存草稿 |
| 5 | submit_report | {"items": [{"material_id": "M01", "review_status": "approved", "risk_reasons": [], "suggested_slot": "2026-11-10T18:00 douyin", "confirmation_status": "not_required", "pending_items": []}], "overall_note": "M01 基础审核通过，抖音 2026-11-10 18:00 首选时段可用，草稿已保存（D-7f6c48bff24f，未发布）。", "reason": "提交逐项审核与排期报告"} | 报告已接收；保存状态以工具记录为准 | 结束：completed | 提交逐项审核与排期报告 |

Token 用量：{"prompt_tokens": 12419, "completion_tokens": 756}
