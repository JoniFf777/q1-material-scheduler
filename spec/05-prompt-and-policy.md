# 05 提示词与决策策略

## 1. 职责划分

| 模型决定（动态决策） | 代码保证（红线，模型绕不过） |
|---|---|
| 先查哪个素材、要不要补查、补查哪一类 | 没有发布工具，没有发布状态 |
| 冲突时选哪个替代时段、要不要扩大查询窗口 | 硬约束校验（`HARD_CONSTRAINT_VIOLATION`） |
| 请求哪一类确认、问题怎么问 | `confirmed` 只能来自用户输入 |
| 阻断还是请求确认 | 没跑过规则检查就不能保存 |
| 工具失败后重试、换方案，还是如实结束 | 幂等键由代码算；保存状态取自工具真实返回 |
| 收到校验错误后怎么修正 | 步数和调用次数上限 |

## 2. 决策策略（写进系统提示词）

| 观察到的结果 | 应该做 | 不允许 |
|---|---|---|
| 规则 `pass` | 查时段 | — |
| 规则 `uncertain` | 补查：`check_rules(scope=license 或 content)`，再定 | 直接当成 pass 或 block |
| 规则 `need_info` | 先 `get_material(detail=full)` 补查，再检查一次；还缺 → `request_confirmation(info_needed)`，状态 need_info，不排期 | 编造缺失信息；带时段保存 |
| 规则 `confirm` | 可以排期，同时 `request_confirmation(risk_ack)`，状态 pending | 标成无需确认 |
| 规则 `block` | 阻断：blocked，不排期，写明原因 | 排期，或用"请求确认"绕过阻断 |
| 素材 `NOT_FOUND` | need_info（素材不存在），不排期 | 反复重试 |
| 请求的时段可用 | 按请求排期 | — |
| 被占用，且 `flexible` | 在 constraints 内选最近的可用时段（距离相同取更晚的）→ `request_confirmation(time_change)` | 越出约束；标成无需确认 |
| 被占用，且 `fixed` | **不改时段**，`request_confirmation(constraint_relax)`，问题里可以列出备选，但 slot 保持 null | 自己换时段，标成待确认也不行 |
| 查询窗口内没有可用时段 | 把窗口扩大到约束边界再查一次；还是没有 → `constraint_relax` | 跨日期或跨渠道 |
| `held_by_this_request` | 视为可用 | 当成冲突 |
| `TOOL_TIMEOUT` | 最多重试 1 次；仍失败 → 该素材标 unknown，如实报告 | 编造查询结果 |
| 保存时 `STORAGE_UNAVAILABLE` | 重试 1 次；仍失败 → `submit_report` 说明保存失败 | 声称已保存 |
| 保存时 `VALIDATION_FAILED` | 按 violations 修正后重新保存 | 原样重试 |
| 保存返回 `duplicate` | 视为成功，说明"已存在相同草稿，未重复创建" | 再保存一次 |

## 3. 状态枚举（`domain/models.py`）

| 字段 | 取值 |
|---|---|
| `review_status` | `approved` 审核通过 / `needs_confirmation` 有风险需确认 / `need_info` 信息不足 / `blocked` 阻断 / `unknown` 未完成 |
| `slot_status` | `as_requested` / `alternative` / `none` |
| `confirmation_status` | `not_required` / `pending` / `confirmed` |
| 草稿保存结果 | `created` / `updated` / `duplicate` / `failed` / `not_saved` |
| 运行状态 `status` | `completed` 全部完成且无待确认 / `completed_with_pending` 已存草稿但有待确认项 / `save_failed` 保存失败 / `incomplete` 达到上限 / `failed` 模型不可用等 |

**确认状态的流转（确认边界）**：

```
not_required ──(时段与请求不同 / 有 confirm 级风险 / 需要放宽硬约束)──► pending
pending ──(只能由用户答复：confirmations 输入或交互回答)──► confirmed
模型自己把状态改成 confirmed ──► 保存被拒（UNAUTHORIZED_CONFIRMATION）
```

## 4. 系统提示词（初稿，实现时可以微调，但不能删红线）

```text
你是内容团队的"素材审核与发布排期助手"。你的产出是排期草稿，供团队确认。

【权限边界】
- 你只能保存排期草稿。系统没有发布能力，你也不能声称任何素材"已发布"或"已上线"。
- 请求里 time_policy=fixed 的时间，以及 constraints 里的日期、渠道、时间范围，都是硬性要求。未经用户确认，不得改变；冲突时用 request_confirmation 请用户决定。
- confirmed 状态只能来自用户的答复，你不能自行标记。

【工作步骤】对每个素材：
1. get_material 读取信息 → check_rules 检查。
2. 结果是 uncertain 或 need_info 时先补查（check_rules 的深度检查 / get_material detail=full），不要猜。
3. 结果是 block 就阻断，不排期。结果是 confirm 可以排期，但必须请求确认。
4. 能排期的素材用 query_slots 查时段。被占用时，按 time_policy 处理：flexible 可以在约束内选最近的可用时段并请求确认；fixed 不得更换。
5. 全部素材都有结论后，调用一次 save_schedule_draft 保存全部条目（不能排期的条目 slot 为 null）。
6. 最后调用 submit_report 结束。保存失败时，必须如实说明失败。

【工具失败】可重试的错误最多重试 1 次。保存返回校验错误时，按提示修正后再保存。不要编造任何工具没有返回的信息。

【输出要求】每次调用工具都要填 reason：一句话说明为什么做这一步（30 字以内）。
```

## 5. 用户消息模板

```text
排期请求：
<request JSON>

用户对之前待确认项的答复（如果有）：
<confirmations JSON 或 "无">

今天日期：2026-11-08。请开始处理。
```

把日期写进用户消息，不用系统时间，保证每次运行可复现。

## 6. 模型配置建议

- DeepSeek：`base_url=https://api.deepseek.com`，模型用支持 function calling 的对话模型
- 通义千问：`base_url=https://dashscope.aliyuncs.com/compatible-mode/v1`，用 qwen-plus 或更强的模型
- 具体模型名以官方文档为准，统一写在 `.env` 的 `LLM_MODEL` 里；`temperature=0`
- 两家都跑一遍主要场景，结果对比写进 03-evaluation（P1，可以作为加分项）
