# 验证材料

- `inputs/`：11 个合成场景，包括 `setup` 和 `expect`。这两个字段不会发给模型。
- `mock/`：真正执行本地工具后产生的结果和 Trace；模型动作来自固定脚本，token 为 0，**不证明真实模型决策效果**。
- `results/mock_summary.md`：离线场景逐项结果。
- `results/pytest.txt`：实际测试输出。
- `live/`：DeepSeek `deepseek-flash` 真实 API 输出与 Trace，11 个场景各跑 3 次，最终 33/33 通过。
- `results/live_summary.*`：最终真实模型汇总；`live_baseline_summary.*` 保留修正前的 30/33 原始结果。
- `live/manual-*`、`baseline-*`、`fresh-clone-*`：候选人手动运行、修正前 S09 和独立新克隆验证的额外证据，不混入最终 33 次的统计。

S04、S06、S06b 共用一次评估中的状态：created v1 → duplicate v1 → updated v2。
S10 从独立的 S04 v1 开始验证用户确认，因此也应是 updated v2。
每次评估创建新的批次目录，不复用其他批次的草稿。
