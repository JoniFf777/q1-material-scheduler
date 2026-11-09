# 运行 Trace

模式：live；模型：deepseek-flash；状态：incomplete

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | list_pending_materials | {"reason": "确认待处理素材范围", "channel": "douyin"} | 找到 7 个待审核素材 | get_material {"material_id": "M01"} | 确认待处理素材范围 |
| 2 | get_material | {"material_id": "M01", "detail": "basic", "reason": "读取素材基础信息"} | 读取 M01（basic） | get_material {"material_id": "M02"} | 读取素材基础信息 |
| 2 | get_material | {"material_id": "M02", "detail": "basic", "reason": "读取素材基础信息"} | 读取 M02（basic） | get_material {"material_id": "M04"} | 读取素材基础信息 |
| 2 | get_material | {"material_id": "M04", "detail": "basic", "reason": "读取素材基础信息"} | 读取 M04（basic） | get_material {"material_id": "M07"} | 读取素材基础信息 |
| 2 | get_material | {"material_id": "M07", "detail": "basic", "reason": "读取素材基础信息"} | 读取 M07（basic） | check_rules {"material_id": "M01", "scope": "basic"} | 读取素材基础信息 |
| 3 | check_rules | {"material_id": "M01", "scope": "basic", "reason": "基础规则校验", "publish_date": "2026-11-10"} | M01 审核 pass：未发现风险 | check_rules {"material_id": "M02", "scope": "basic"} | 基础规则校验 |
| 3 | check_rules | {"material_id": "M02", "scope": "basic", "reason": "基础规则校验", "publish_date": "2026-11-10"} | M02 审核 pass：未发现风险 | check_rules {"material_id": "M04", "scope": "basic"} | 基础规则校验 |
| 3 | check_rules | {"material_id": "M04", "scope": "basic", "reason": "基础规则校验", "publish_date": "2026-11-10"} | M04 审核 uncertain：music 授权状态未知 | check_rules {"material_id": "M07", "scope": "basic"} | 基础规则校验 |
| 3 | check_rules | {"material_id": "M07", "scope": "basic", "reason": "基础规则校验", "publish_date": "2026-11-10"} | M07 审核 uncertain：music 授权状态未知 | check_rules {"material_id": "M04", "scope": "license"} | 基础规则校验 |
| 4 | check_rules | {"material_id": "M04", "publish_date": "2026-11-10", "reason": "深查音乐授权状态", "scope": "license"} | M04 审核 block：music 授权已过期（2026-10-31） | check_rules {"material_id": "M07", "scope": "license"} | 深查音乐授权状态 |
| 4 | check_rules | {"material_id": "M07", "publish_date": "2026-11-10", "reason": "深查音乐授权状态", "scope": "license"} | M07 审核 pass：未发现风险 | 结束：incomplete | 深查音乐授权状态 |

Token 用量：{"prompt_tokens": 12062, "completion_tokens": 1005}
