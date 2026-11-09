# 评估

2026-11-09 使用 DeepSeek `deepseek-flash` 实际调用模型：11 个场景各运行 3 次，**33/33 通过**。各次运行均执行 I1–I7，未发现违反红线。离线测试为 **76/76**，固定 Mock 场景为 **11/11**。

证据：[真实汇总](../examples/results/live_summary.md)、[机器可读结果](../examples/results/live_summary.json)、[pytest 输出](../examples/results/pytest.txt)、[环境版本](../examples/results/environment.json)。Mock 只证明流程，真实决策结论来自 live 调用。

## 验收证据

| 验收点 | 场景 | 真实结果与 Trace |
|---|---|---|
| A1 正常排期 | S01 | [结果](../examples/live/S01_normal.result.json) / [Trace](../examples/live/S01_normal.trace.md) |
| A2 信息补查 | S02 | [结果](../examples/live/S02_missing_info.result.json) / [Trace](../examples/live/S02_missing_info.trace.md) |
| A3 规则风险 | S03 | [结果](../examples/live/S03_rule_risk.result.json) / [Trace](../examples/live/S03_rule_risk.trace.md) |
| A4 软冲突 | S04 | [结果](../examples/live/S04_slot_conflict.result.json) / [Trace](../examples/live/S04_slot_conflict.trace.md) |
| A4 fixed 冲突 | S05 | [结果](../examples/live/S05_hard_conflict.result.json) / [Trace](../examples/live/S05_hard_conflict.trace.md) |
| A5 重复提交 | S06 | [结果](../examples/live/S06_duplicate.result.json) / [Trace](../examples/live/S06_duplicate.trace.md) |
| A5 占用变化 | S06b | [结果](../examples/live/S06b_slot_changed.result.json) / [Trace](../examples/live/S06b_slot_changed.trace.md) |
| A6 保存失败 | S07 | [结果](../examples/live/S07_save_failure.result.json) / [Trace](../examples/live/S07_save_failure.trace.md) |
| 工具失败后恢复 | S08 | [结果](../examples/live/S08_tool_retry.result.json) / [Trace](../examples/live/S08_tool_retry.trace.md) |
| 限额终止 | S09 | [结果](../examples/live/S09_step_limit.result.json) / [Trace](../examples/live/S09_step_limit.trace.md) |
| 第二轮用户确认 | S10 | [结果](../examples/live/S10_confirm_round2.result.json) / [Trace](../examples/live/S10_confirm_round2.trace.md) |

## 三次真实运行

| 场景 | 通过 | 三次 LLM 轮数 | 三次合计 tokens |
|---|---|---|---|
| S01_normal | 3/3 | 4, 5, 5 | 38400 |
| S02_missing_info | 3/3 | 8, 7, 7 | 79577 |
| S03_rule_risk | 3/3 | 7, 7, 8 | 97048 |
| S04_slot_conflict | 3/3 | 6, 7, 7 | 67609 |
| S05_hard_conflict | 3/3 | 8, 7, 7 | 71410 |
| S06_duplicate | 3/3 | 7, 7, 6 | 65478 |
| S06b_slot_changed | 3/3 | 5, 5, 5 | 40159 |
| S07_save_failure | 3/3 | 6, 5, 6 | 47602 |
| S08_tool_retry | 3/3 | 6, 6, 6 | 52520 |
| S09_step_limit | 3/3 | 4, 4, 4 | 44772 |
| S10_confirm_round2 | 3/3 | 6, 6, 6 | 63109 |

33 次被评估运行合计 667,684 tokens；不包含 S10 前置准备、候选人手动 S04、修正前基线和新克隆验证。第 1 次结果与 JSON/Markdown Trace 在 examples/live，其余运行写入汇总。所有 Trace 标为 live，记录 API 返回的模型名与真实 token 用量。

## 模型根据观察调整动作

- S01 与 S04：规则均通过。S01 看到请求时段空闲后保存；S04 看到 18:00 被 M90 占用，选 19:00，调用 time_change 登记待确认后保存。fixed 的 S05 则保留空时段，请用户决定，不换到替代时段。
- S03：M04 与 M07 的基础检查均为 uncertain；模型补查 license，分别观察到授权过期的 block 和有效的 pass。M04 没有时段，M07 按请求排期；M05 的用语风险单独请求 risk_ack。
- S07 与 S08：保存故障持续发生时，模型重试一次后如实报告 save_failed；时段查询首次超时后，模型重试并取得结果，继续排期。
- 候选人手动 [S04 原始 Trace](../examples/live/manual-S04_slot_conflict.trace.md) 还记录了校验后的修正：模型先把“排期待确认”混成审核 needs_confirmation，保存工具返回 RISK_STATUS_MISMATCH 后，模型改成 approved 再保存。报告把渠道前缀写入时间字段时，最终组装采用真实保存快照并保留 consistency warning。

## 失败与修正记录

1. 修正前基线为 **30/33**。3 次失败均为 S09 的评估器错误：[原始汇总](../examples/results/live_baseline_summary.md)、[原始 S09 Trace](../examples/live/baseline-S09_step_limit.trace.md)。生成场景曾固定断言 M07=unknown，真实模型却在前 4 轮中批量完成了 M07 审核。系统实际均按限额返回 incomplete / MAX_STEPS_REACHED / not_saved，没有越界行为。
2. [spec/06](../spec/06-scenarios-and-evaluation.md) 要求“未处理的素材为 unknown”，没有要求固定某个 ID 未处理。修正生成场景及评估器，从工具事实检查所有未审核条目；保留步数、运行状态和未保存要求，未修改规格或业务循环。新增批量调用回归测试修正前 1 failed / 1 passed，修正后 2/2 通过；随后重新真实调用得到本页的 33/33。
3. 执行环境使用 SOCKS 代理而缺少 socksio，最初在客户端初始化时失败，尚未发起模型请求。显式声明 httpx[socks] 后恢复；Key 和代理地址没有写入材料。
4. 新克隆首次执行 README 的 pytest 命令时，runtime 父目录不存在，产生 17 passed / 59 setup errors：[首次日志](../examples/results/fresh-clone-initial.txt)。README 已增加创建 runtime 的步骤，独立环境重新验证全部通过。

## 新克隆验证

源码提交 `3071a86` 新克隆、全新虚拟环境：editable 安装、CLI --help、pip check、76 项测试及 11 个 Mock 场景通过，见 [完整日志](../examples/results/fresh-clone.txt)。随后真实运行 S04 得到 19:00 / pending / created：[结果](../examples/live/fresh-clone-S04_slot_conflict.result.json)、[Trace](../examples/live/fresh-clone-S04_slot_conflict.trace.md)、[终端输出](../examples/results/fresh-clone-live.txt)。该克隆未复制 .env，仅通过子进程内存环境传入本机配置。之后的交付提交补充文档与验证材料。

## 已知限制

- 只验证一个真实模型，每场景 3 次是有限样本，不能保证任意输入都成功；temperature=0 也不能保证完全复现。未做千问对比。
- Mock 不读取观察，只验证执行器和防线，不能替代真实模型效果。
- JSON 原子替换没有跨进程锁，生产环境需要事务与唯一约束；本机 confirmations 输入被视为可信用户输入，没有身份认证。
- 无自然语言解析、真实素材/授权服务、发布能力或终端交互确认；时段是整点，每个渠道时段容量为 1。固定要求需要变更时应提交明确的新请求。
- 代码可拒绝越界动作，不能保证模型总能在限额内完成；报告与事实不一致时保留 warning 并采用工具记录。
