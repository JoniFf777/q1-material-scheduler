# 03 工具定义

共 7 个工具：6 个业务工具，加 1 个结束工具 `submit_report`。**每个工具都有必填参数 `reason`**（30 字以内的决策依据），下文不再重复列出。

## 0. 统一返回结构

```json
{ "ok": true,  "data": { ... }, "summary": "一句话摘要（代码生成，写入 Trace）" }
{ "ok": false, "error_code": "TOOL_TIMEOUT", "message": "时段服务超时", "retryable": true }
```

| error_code | 含义 | retryable |
|---|---|---|
| `INVALID_ARGUMENTS` | 参数缺失、类型错误或 JSON 解析失败 | false |
| `NOT_FOUND` | 素材不存在 | false |
| `TOOL_TIMEOUT` | 注入的超时 | true |
| `STORAGE_UNAVAILABLE` | 注入的存储故障 | true |
| `VALIDATION_FAILED` | 保存校验不通过，`violations` 里给出明细 | false |
| `REPEATED_CALL` | 同工具同参数调用已达上限 | false |

## 1. `list_pending_materials`

参数：`channel?: string`
返回：`{ "materials": [ { "material_id": "M01", "title": "...", "status": "pending_review" } ] }`
用途：请求里写了 `scope: "pending"` 而不是具体 ID 时使用。

## 2. `get_material`

参数：`material_id: string`，`detail: "basic" | "full"`（默认 basic）
返回：素材元数据，缺失的字段显式返回 `null`。`full` 会额外带上 `extended` 段（来自"素材库"的补充信息），用于**补查**。

```json
{ "material_id": "M03", "title": "...", "type": "video", "duration_sec": null,
  "copyright": { "owner": null, "license_status": null, "license_expiry": null },
  "extended": { "duration_sec": 62, "copyright_owner": null } }
```

## 3. `check_rules`

参数：`material_id`，`scope: "basic" | "license" | "content"`，`publish_date?: "YYYY-MM-DD"`
返回：

```json
{ "material_id": "M04", "scope": "basic", "verdict": "uncertain",
  "findings": [ { "rule_id": "R03", "severity": "uncertain", "message": "背景音乐授权状态未登记" } ] }
```

- `severity` 和 `verdict` 的取值：`pass` / `confirm`（需人工确认）/ `uncertain`（需补查）/ `need_info` / `block`
- `verdict` 取所有 finding 中最严重的一级，优先级：block > need_info > uncertain > confirm > pass
- `scope=license` 查授权库，`scope=content` 查敏感词库（深度检查）。basic 只看元数据。
- 工具**不给**"下一步该做什么"的提示，由模型按策略自己决定（见 05）。
- 调用后 RunContext 记下 `checked[material_id] = 最终 verdict`，保存时会校验。

## 4. `query_slots`

参数：`channel`，`date`，`from: "HH:MM"`，`to: "HH:MM"`
返回：

```json
{ "channel": "douyin", "date": "2026-11-10",
  "slots": [
    { "start": "18:00", "status": "occupied", "occupied_by": { "material_id": "M90", "source": "schedule" } },
    { "start": "19:00", "status": "available" },
    { "start": "20:00", "status": "held_by_this_request", "occupied_by": { "material_id": "M01", "source": "draft", "draft_id": "D-..." } }
  ] }
```

- 时段网格是整点，08:00–23:00，每个渠道每个时段容量为 1（配置在 `data/slot_config.json`）
- 占用来源有两种：已有排期 `schedule.json`，以及**其他请求**的有效草稿
- `held_by_this_request`：被本请求自己之前的草稿占着（重复提交时会出现），对本请求视为可用。**这一条是"重复提交"不出错的关键**，否则第二次运行会把自己当成冲突，把时段越推越后。
- 同一时段既被已有排期或他人草稿占用、又被本请求的旧草稿占着时，显示 `occupied`（S06b 会出现这种情况）。

## 5. `request_confirmation`

参数：`material_id`，`type: "time_change" | "constraint_relax" | "risk_ack" | "info_needed"`，`question`，`options: string[]`，`proposed_slot?: "YYYY-MM-DDTHH:MM"`
行为：

1. 如果请求的 `confirmations` 输入里已经有匹配的用户答复（material_id + type 匹配，若给了 proposed_slot 也要一致），返回 `{ "status": "confirmed" | "rejected", "user_reply": "..." }`
2. 如果开了 `--interactive`，在终端提问并返回用户的选择（P1）
3. 其余情况登记为待确认，返回 `{ "confirmation_id": "C1", "status": "pending" }`

**`confirmed` 只能由用户输入产生**。模型自己填的 `confirmed`，保存时会被拒绝。

## 6. `save_schedule_draft`

参数：

```json
{ "items": [ {
    "material_id": "M01",
    "review_status": "approved | needs_confirmation | need_info | blocked",
    "risk_reasons": ["..."],
    "slot": { "channel": "douyin", "start": "2026-11-10T19:00" },
    "confirmation_status": "not_required | pending | confirmed",
    "confirmation_ids": ["C1"]
} ] }
```

- 幂等键**不在参数里**，由代码根据请求计算（见 04）
- `items` 必须覆盖请求里的全部素材；不能排期的素材 `slot = null`

校验（`guards.py`，任一不通过就返回 `VALIDATION_FAILED`，不写任何数据）：

| 违规码 | 条件 |
|---|---|
| `MISSING_ITEMS` | 漏了请求里的素材 |
| `RULE_CHECK_REQUIRED` | 该素材本次运行没跑过 `check_rules` |
| `BLOCKED_ITEM_HAS_SLOT` | `blocked` 或 `need_info` 的条目带了时段 |
| `RISK_STATUS_MISMATCH` | 规则结论是 block 却标成了 approved 等不一致的情况 |
| `HARD_CONSTRAINT_VIOLATION` | 时段违反 fixed 时间、日期、渠道、not_before/not_after 或素材禁发期，且没有用户的放宽确认 |
| `CONFIRMATION_REQUIRED` | 时段与 preferred_time 不同，或存在 confirm 级风险，但 `confirmation_status` 不是 pending/confirmed |
| `UNAUTHORIZED_CONFIRMATION` | 标了 `confirmed`，但找不到对应的用户确认记录 |
| `SLOT_CONFLICT` | 与已有排期或其他请求的草稿冲突，或本请求内两个条目抢同一个时段 |
| `INVALID_SLOT` | 不在时段网格上 |

成功返回：

```json
{ "ok": true, "data": { "draft_id": "D-7f3a9c", "version": 1, "result": "created | updated | duplicate",
  "store_file": "runtime/s04/drafts.json" }, "summary": "草稿已创建（v1，未发布）" }
```

## 7. `submit_report`（结束工具）

参数：`items[]`（material_id、review_status、risk_reasons、suggested_slot、confirmation_status、pending_items[]），`overall_note`
校验：必须覆盖全部素材，枚举值合法。不通过就把错误返回给模型修正。
通过后循环结束，进入最终结果组装（02 第 6 节）。**保存状态不在参数里**，由代码从事实里填。

## 8. 故障注入

- 来源：CLI `--fault <tool>=<mode>`（可写多个），或场景文件里的 `"faults": { "save_schedule_draft": "always" }`
- 模式：`once`（第一次调用失败，之后正常）、`always`（每次都失败）
- 失败时返回的错误码：`query_slots` 返回 `TOOL_TIMEOUT`，`save_schedule_draft` 返回 `STORAGE_UNAVAILABLE`，其他工具返回 `TOOL_TIMEOUT`
- 在 `registry.execute` 里统一处理，业务函数本身不知道注入的存在
