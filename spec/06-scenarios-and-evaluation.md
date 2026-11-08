# 06 场景、测试与评估

## 1. 场景清单（`examples/inputs/`）

| 场景 | 覆盖 | 输入要点 | 期望结果 |
|---|---|---|---|
| S01_normal | A1 | M02，douyin 11-10 20:00，flexible | approved，as_requested，not_required，`created`，status=completed |
| S02_missing_info | A2 | M03（douyin 11-10 15:00）+ M08（douyin 11-10 16:00），都是 flexible | M03：检查 → 补查 full → 再检查 → info_needed，need_info，不排期；M08：NOT_FOUND → need_info；`created`，completed_with_pending |
| S03_rule_risk | A3、两条路径 | M04（douyin 11-10 19:00）+ M05（xiaohongshu 11-10 12:00）+ M07（douyin 11-10 21:00），都是 flexible | M04：uncertain → 授权库 → blocked；M05：confirm → 排在请求的时段并请求 risk_ack；M07：uncertain → 授权库 → pass → 按请求排期 |
| S04_slot_conflict | A4、参考实例 | M01，18:00，flexible | 19:00，alternative，pending（time_change），`created`，不出现"已发布" |
| S05_hard_conflict | A4、确认边界 | M06，11-11 20:00，**fixed** | review approved，slot=null，pending（constraint_relax），问题里可以给出备选；**草稿里没有任何替代时段** |
| S06_duplicate | A5 | 用同一个 state 目录把 S04 跑两次 | 第二次 `duplicate`，同一个 draft_id，drafts.json 里只有 1 份草稿 |
| S06b_slot_changed | A5、更换占用时段 | 接着 S06，用 `schedule_patch` 把 M90 从 18:00 移到 19:00 | 18:00 as_requested，not_required，`updated` v2，草稿数仍为 1 |
| S07_save_failure | A6、工具失败 | M02 + `faults.save_schedule_draft=always` | 最多重试 1 次 → status=save_failed，草稿结果 `failed` 并带错误码，drafts.json 不存在或没有变化 |
| S08_tool_retry | 工具失败（可恢复） | M02 + `faults.query_slots=once` | 重试后成功，`created`，Trace 里能看到失败和重试两步 |
| S09_step_limit | 步数上限 | M01、M02、M04、M07，`limits.max_steps=4` | status=incomplete，MAX_STEPS_REACHED，未处理的素材为 unknown，草稿 `not_saved` |
| S10_confirm_round2（P1） | 确认边界 | 接着 S04 的 state，带上 confirmations：M01 同意 19:00 | confirmed，`updated` v2，status=completed |

**两条执行路径的证据**（写进 03-evaluation，并引用 Trace 文件）：

1. S01 对 S04：前两步一样（读取、检查），查时段的结果不同，模型分别走"直接保存"和"换时段 → 请求确认 → 保存"
2. S03 里 M04 对 M07：都是 uncertain，补查结果不同，分别走"阻断"和"排期"
3. S07 对 S01：保存失败和保存成功，最终报告分别如实反映

## 2. 全局不变式（每次运行都自动检查，live 和 mock 都检查）

| # | 不变式 |
|---|---|
| I1 | 输出和 Trace 的文本里没有"已发布 / 发布成功 / 已上线" |
| I2 | 结果里的 `draft_save` 和 Trace 里最后一次保存工具的返回一致 |
| I3 | 时段与请求不同的条目，确认状态是 pending，或者是有用户记录支持的 confirmed |
| I4 | fixed 条目的时段要么等于请求的时间，要么为 null |
| I5 | blocked 和 need_info 条目没有时段 |
| I6 | drafts.json 里每个幂等键最多只有 1 份草稿 |
| I7 | 只有达到上限时 status 才是 incomplete |

实现成 `src/schedule_agent/checks.py` 里的函数。场景执行器和 pytest 都调用它。

## 3. 测试分层

| 层 | 文件 | 需要 Key | 证明什么 |
|---|---|---|---|
| 单元测试 | `tests/test_tools.py`、`test_guards.py`、`test_draft_store.py`、`test_fingerprint.py` | 否 | 工具、红线、幂等逻辑本身是对的 |
| 流程测试 | `tests/test_agent_loop.py`（ScriptedMockLLM） | 否 | 循环机制：正常结束、错误回传、校验后修正、步数上限、参数 JSON 错误、模型虚报保存时被代码纠正 |
| Live 测试 | `scripts/run_scenarios.py --llm live --repeat 3` | 是 | 真实模型在各场景下的决策是否符合期望，以及稳定性 |

必须有的单元测试（红线相关，一条都不能少）：

- 时段与请求不同但标成 not_required → `CONFIRMATION_REQUIRED`
- fixed 条目换了时段 → `HARD_CONSTRAINT_VIOLATION`
- 模型自己标 confirmed → `UNAUTHORIZED_CONFIRMATION`
- blocked 条目带时段 → `BLOCKED_ITEM_HAS_SLOT`
- 没检查过就保存 → `RULE_CHECK_REQUIRED`
- 同一请求保存两次 → 第二次 `duplicate`，文件里只有 1 份
- 内容变化后保存 → `updated`，version=2，仍然只有 1 份
- 存储故障 → 返回失败，文件内容没有变化
- 本请求自己的旧草稿在 `query_slots` 里显示为 `held_by_this_request`，保存时不算冲突
- 模型的 submit_report 说已保存但实际失败 → 最终结果是 failed，并带 consistency warning

## 4. 场景执行器

```bash
python scripts/run_scenarios.py --llm live --repeat 3     # 真实模型，每个场景跑 3 次
python scripts/run_scenarios.py --llm mock                # 离线，仅验证流程
python scripts/run_scenarios.py --llm live --only S04_slot_conflict
```

- 每个场景：准备 state 目录 → 运行 → 对照 `expect` 断言，并检查 I1–I7 → 写出结果文件
- S06、S06b、S10 是有顺序的组合场景，执行器按顺序在同一个 state 目录里跑
- 汇总写到 `examples/results/live_summary.md`：场景 | 第几次 | 通过/失败 | 失败原因 | 步数 | tokens

## 5. examples/ 的组织

```
examples/
  inputs/      S01_normal.json …
  live/        S01_normal.result.json  S01_normal.trace.json  S01_normal.trace.md …
  mock/        同上的 mock 版本，文件名带 .mock，README 写明只验证流程
  results/     live_summary.md  pytest.txt（pytest 的完整输出）
```

只把**第 1 次** live 运行的结果和 Trace 放进 `live/`。重复运行的结果只进 summary，避免文件太多。

## 6. 03-evaluation.md 要写的内容

1. 验收点 → 场景 → 文件路径的对照表（每一行都要链接到 `examples/live/` 下的文件）
2. 两条执行路径的说明，附上 Trace 的关键几步
3. live 通过率表（来自 live_summary.md），以及失败用例的分析：模型在哪一步、做了什么，是靠提示词修好的还是靠代码防线兜住的
4. 已知限制：Mock 不能证明决策效果；JSON 存储没有并发锁；没有自然语言解析；时段只有整点粒度；模型输出有波动（temperature=0 也不能完全复现）
