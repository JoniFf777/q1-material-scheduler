# 运行 Trace

模式：live；模型：deepseek-flash；状态：completed

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"material_id": "M02", "detail": "basic", "reason": "读取素材基本信息用于审核"} | 读取 M02（basic） | check_rules {"material_id": "M02", "scope": "basic"} | 读取素材基本信息用于审核 |
| 1 | check_rules | {"material_id": "M02", "scope": "basic", "publish_date": "2026-11-10", "reason": "按计划日期执行基础规则校验"} | M02 审核 pass：未发现风险 | query_slots {"date": "2026-11-10"} | 按计划日期执行基础规则校验 |
| 2 | query_slots | {"channel": "douyin", "date": "2026-11-10", "from": "18:00", "to": "21:00", "reason": "查询首选时段附近可用空位"} | 18:00 occupied(M90)；19:00 available；20:00 available；21:00 available | save_schedule_draft {} | 查询首选时段附近可用空位 |
| 3 | save_schedule_draft | {"items": [{"material_id": "M02", "review_status": "approved", "risk_reasons": [], "slot": {"channel": "douyin", "start": "2026-11-10T20:00"}, "confirmation_status": "not_required", "confirmation_ids": []}], "reason": "保存 M02 草稿，首选时段可用"} | 草稿 created（v1，未发布） | submit_report {} | 保存 M02 草稿，首选时段可用 |
| 4 | submit_report | {"items": [{"material_id": "M02", "review_status": "approved", "risk_reasons": [], "suggested_slot": "2026-11-10T20:00 douyin", "confirmation_status": "not_required", "pending_items": []}], "overall_note": "M02 基础校验通过，抖音 2026-11-10 20:00 时段可用且在 not_after 21:00 内，草稿已保存（D-9896d94c8916，未发布）。", "reason": "提交逐项审核与排期报告"} | 报告已接收；保存状态以工具记录为准 | 结束：completed | 提交逐项审核与排期报告 |

Token 用量：{"prompt_tokens": 10324, "completion_tokens": 829}
