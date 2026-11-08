# 验证材料

- `inputs/`：11 个合成场景，包括 `setup` 和 `expect`。这两个字段不会发给模型。
- `mock/`：真正执行本地工具后产生的结果和 Trace；模型动作来自固定脚本，token 为 0，**不证明真实模型决策效果**。
- `results/mock_summary.md`：离线场景逐项结果。
- `results/pytest.txt`：实际测试输出。
- `live/`：阶段 4 真实 API 验证后生成，目前没有真实模型验证材料。

S04、S06、S06b 共用一次评估中的状态：created v1 → duplicate v1 → updated v2。
S10 从独立的 S04 v1 开始验证用户确认，因此也应是 updated v2。
每次评估创建新的批次目录，不复用其他批次的草稿。
