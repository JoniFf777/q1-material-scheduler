# 评估

离线 pytest 74/74 和 11 个固定 Mock 场景已通过；I1–I7 未发现违规。实际输出见 [Mock 汇总](../examples/results/mock_summary.md)与[pytest 输出](../examples/results/pytest.txt)。这些结果不能证明真实模型的决策能力。

## 验收证据

| 验收点 | 场景 | 离线证据 | Live |
|---|---|---|---|
| A1 正常排期 | S01 | [Trace](../examples/mock/S01_normal.mock.trace.md) | 待本人运行 |
| A2 信息补查 | S02 | [Trace](../examples/mock/S02_missing_info.mock.trace.md) | 待本人运行 |
| A3 风险与授权补查 | S03 | [Trace](../examples/mock/S03_rule_risk.mock.trace.md) | 待本人运行 |
| A4 冲突 | S04、S05 | [软偏好](../examples/mock/S04_slot_conflict.mock.trace.md)、[fixed](../examples/mock/S05_hard_conflict.mock.trace.md) | 待本人运行 |
| A5 幂等与变化 | S06、S06b | [重复](../examples/mock/S06_duplicate.mock.trace.md)、[变化](../examples/mock/S06b_slot_changed.mock.trace.md) | 待本人运行 |
| A6 保存失败 | S07 | [Trace](../examples/mock/S07_save_failure.mock.trace.md) | 待本人运行 |

当前未提供 Live 文件链接，因为没有真实调用证据。spec/06 全部场景，包括 S06b 和可选 S10 的 Live 均未运行。运行后请将表格补为 examples/live 下实际结果和 Trace 的链接。

## 两条执行路径

以下是固定脚本验证的路径，仍需 Live Trace 证明真实模型会自主选择。

- S01 与 S04：相同的读取、审核之后，S01 的 20:00 可用直接保存；S04 的 18:00 被 M90 占用，登记 time_change 并保存 19:00 待确认。
- S03 的 M04 与 M07：basic 都为 uncertain，license 补查分别返回 block 和 pass，前者无时段、后者按要求排期；M05 单独登记 risk_ack。
- S07 与 S01：保存失败两次后如实返回 STORAGE_UNAVAILABLE；成功场景从工具记录组装 created。原子写失败测试同时验证原文件未改变。

## Live 记录方式

运行 `python scripts/run_scenarios.py --llm live --repeat 3`。第 1 次结果和 Trace 在 examples/live，重复运行仅写 examples/results/live_summary.md 与 .json；S10 前置结果保留在 runtime。汇总含通过/失败、原因、轮数、工具次数、tokens。

目前没有 Live 通过率，不能用 Mock 的 11/11 代替。本人需核对 A1–A6 至少各一份通过证据与所有 Live 运行 I1–I7，并记录每次修正：场景、实际观察、提示词或代码改动、重跑结果。不要追填未发生的调试经历。

## 已知限制

- Mock 不读取观察，只验证工具链与循环，不能证明真实模型能力、任意种子变体和稳定性。
- JSON 没有跨进程锁，可能丢更新，生产环境需要事务和唯一约束。
- 无自然语言解析、真实素材/授权服务、真实发布；整点时段，单渠道单时段容量 1。
- temperature=0 不能保证完全复现；服务模型、授权与决策结果仍需实际运行验证。
- 代码可以拒绝越界动作，不能保证模型在限额内修正并完成任务。
