# 04 数据与持久化

## 1. 目录约定

```
data/                    # 种子数据，只读，评审可以直接改（比如改 schedule.json 来"更换占用时段"）
  materials.json  rules.json  schedule.json  slot_config.json
  license_db.json        # check_rules(scope=license) 查的授权库
  terms.json             # 极限用语 / 违禁词
runtime/<state-name>/    # 运行状态，已加入 .gitignore
  drafts.json            # 草稿库
examples/                # 输入、输出、Trace（提交到仓库）
```

CLI 参数 `--data-dir`（默认 `data/`）和 `--state-dir`（默认 `runtime/default/`）。每个示例场景用各自的 state 目录，互不影响；S06 有意复用同一个目录。

## 2. 合成数据

### 2.1 时段配置（slot_config.json）

渠道 `douyin`、`xiaohongshu`；整点时段 08:00–23:00；每个时段容量为 1。

### 2.2 已有排期（schedule.json）

| 渠道 | 时间 | 占用素材 | 作用 |
|---|---|---|---|
| douyin | 2026-11-10 17:00 | M92 | 让 18:00 往前也被占，保证"最近可用"唯一是 19:00 |
| douyin | 2026-11-10 18:00 | M90 | 参考实例：18:00 已被占用 |
| douyin | 2026-11-11 20:00 | M91 | S05：硬性 20:00 被占 |

### 2.3 素材（materials.json）

| ID | 摘要 | 触发的路径 | 场景 |
|---|---|---|---|
| M01 | 秋季穿搭，45s，元数据完整、无风险 | 时段冲突 → 换到 19:00，待确认 | S04、S06 |
| M02 | 周末露营 vlog，无风险 | 正常排期 | S01、S07、S08 |
| M03 | 新品开箱；basic 缺时长、版权方、授权状态；full 能补出时长，补不出版权 | 补查后仍缺 → need_info | S02 |
| M04 | 城市夜跑；背景音乐授权状态为 unknown；授权库显示已于 2026-10-31 过期 | 补查 → block | S03 |
| M05 | 标题"全网第一的剪辑技巧" | 极限用语 → confirm | S03 |
| M06 | 双 11 直播预告，无风险；请求为 fixed 20:00 | 硬性时段被占 → 不改，请求确认 | S05 |
| M07 | 咖啡拉花；音乐授权 unknown；授权库显示有效期到 2027-03-31 | 补查 → pass → 排期 | S03 |
| M08 | （不存在） | NOT_FOUND | S02 |
| M09 | 禁发期到 2026-11-10 20:00，请求 19:00（P1，可选） | 素材侧的硬约束 | S09 |

M04 和 M07 是一对对照：同一种不确定的风险，补查结果不同，模型走的路线也不同。这就是题目要求的"两条执行路径"之一。

### 2.4 规则（rules.json）

| ID | 规则 | basic 下的判定 | 深度检查 |
|---|---|---|---|
| R01 | 必填字段：title、type、duration_sec（视频）、copyright.owner、copyright.license_status | 缺字段 → need_info，并列出缺了哪些 | — |
| R02 | 版权授权有效，且到期日不早于发布日 | expired → block；unknown → uncertain | `scope=license` 查 license_db |
| R03 | 背景音乐授权 | 同 R02 | 同 R02 |
| R04 | 用语：违禁词 → block；极限用语（第一、最、绝对……）→ confirm | 扫描 title 和 description | `scope=content` 再扫描字幕文本 |

**补查的信息口径**：RunContext 为每个素材维护一个"工作视图"。默认是 basic 记录；模型调用过 `get_material(detail="full")` 之后，用 `extended` 补上空字段。`check_rules` 评估的是这个视图，意思是"基于目前已经查到的信息做检查"。所以 M03 的流程是：检查（缺 3 项）→ 补查 full → 再检查（还缺 2 项）→ 请求补充信息。

## 3. 输入文件格式（场景文件）

```json
{
  "name": "04_slot_conflict",
  "description": "参考实例：M01 要 18:00，已被占用",
  "setup": { "faults": {}, "schedule_patch": { "add": [], "remove": [] }, "limits": {} },
  "request": {
    "items": [ { "material_id": "M01", "channel": "douyin",
                 "preferred_time": "2026-11-10T18:00", "time_policy": "flexible",
                 "constraints": { "date_fixed": true, "not_after": "21:00" } } ],
    "note": "晚间流量高峰优先"
  },
  "confirmations": [],
  "expect": { "M01": { "suggested_slot": "2026-11-10T19:00", "confirmation_status": "pending" },
              "draft_result": "created" }
}
```

- **只有 `request` 和 `confirmations` 会发给模型**。`setup`（故障、排期补丁、限额）和 `expect`（断言）模型看不到。
- `schedule_patch` 只在内存里改已有排期，不改种子文件。这样"更换占用时段"可以复现（S06b）。
- 请求里也可以不写 `items`，改写 `"scope": "pending"`，由模型调用 `list_pending_materials` 自己找。

## 4. 草稿存储（drafts.json）

```json
{ "schema_version": 1,
  "drafts": [ {
    "draft_id": "D-1a2b3c4d",
    "idempotency_key": "RQ-1a2b3c4d5e6f",
    "status": "draft",
    "version": 1,
    "content_hash": "sha256:…",
    "items": [ … ],
    "pending_confirmations": [ { "id": "C1", "material_id": "M01", "type": "time_change", "question": "…" } ],
    "created_at": "…", "updated_at": "…",
    "history": [ { "version": 1, "content_hash": "…", "run_id": "…", "saved_at": "…" } ]
  } ] }
```

`status` 只有 `draft` 一个取值。**整个系统里不存在发布状态。**

## 5. 幂等与防重复

**幂等键**：`RQ-` + sha256(规范化请求) 的前 12 位。
规范化的做法：取 `items`（按 material_id 排序，只保留 material_id、channel、preferred_time、time_policy、constraints）和 `scope`，JSON 序列化时排序 key、去掉空格。`note`、`confirmations` 不参与计算。
`draft_id` 由幂等键派生，同一请求每次运行得到的 draft_id 都一样。

**保存流程**（`save_schedule_draft`）：

1. `guards.validate` 不通过 → `VALIDATION_FAILED`，不写数据
2. 命中故障注入 → `STORAGE_UNAVAILABLE`，不写数据
3. 读取 drafts.json，按幂等键查找
4. 计算 `content_hash`（items 加待确认项，不含时间戳和 run_id）
5. 找不到 → 新建 v1，返回 `created`
6. 找到且 hash 相同 → **不写数据**，返回 `duplicate` 和已有的 draft_id
7. 找到但 hash 不同（时段数据变了，或用户确认了）→ version+1，旧版本记入 history，返回 `updated`
8. 写入用原子方式：先写 `drafts.json.tmp`，再 `os.replace` 覆盖。中途失败也不会留下写了一半的文件

**冲突检查的占用来源** = 已有排期（加上 patch）+ **其他**幂等键的草稿条目。本请求自己的旧草稿不算冲突，在 `query_slots` 里显示为 `held_by_this_request`。

**"更换占用时段并重复提交"的预期**：

| 操作 | 结果 |
|---|---|
| S04 第一次 | 19:00 待确认，`created` v1 |
| S04 原样再跑一次 | 结论相同，`duplicate`，草稿数仍为 1 |
| 把 M90 从 18:00 移到 19:00 后再跑 | 18:00 空出来了，按原要求排 18:00、无需确认，`updated` v2，草稿数仍为 1 |
| 改成 19:00 也被占用后再跑 | 换成 20:00 待确认，`updated`，草稿数仍为 1 |

## 6. 为什么用 JSON 而不用 SQLite

- 评审要"核对保存结果"，直接打开 drafts.json 就能看到只有一份草稿，不需要额外工具
- 单进程 CLI，原子替换已经保证不会写坏文件
- 已知限制（写进 03-evaluation）：没有跨进程锁，两个进程同时写可能丢更新。生产方案是用数据库，给幂等键和（渠道, 时段）各加一个唯一约束，并在事务里完成"检查 + 写入"

## 7. 其他 CLI 命令

```bash
schedule-agent drafts list --state-dir runtime/s04      # 列出草稿：id、版本、条目数、待确认数
schedule-agent drafts show D-1a2b3c4d --state-dir runtime/s04
schedule-agent reset --state-dir runtime/s04            # 清空该目录下的草稿
```
