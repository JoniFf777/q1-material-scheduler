# 第一题实现规格：素材审核与发布排期 Agent

本目录是**实现前的规格**，给实现者（你自己或另一个 AI 窗口）用。
`q1-material-scheduler/` 将来就是这道题单独提交的 GitHub 仓库根目录；其他题目放在 `xiaoying/` 下的同级文件夹（如 `q2-xxx/`）。

## 阅读顺序

| 文件 | 内容 |
|---|---|
| [01-problem-analysis.md](01-problem-analysis.md) | 题目拆解、验收点、关键缺陷红线、范围 |
| [02-architecture.md](02-architecture.md) | 架构、ReAct 循环、限额、Trace、最终结果组装 |
| [03-tools.md](03-tools.md) | 7 个工具（6 个业务工具加结束工具）的参数、返回、错误码、故障注入 |
| [04-data-and-persistence.md](04-data-and-persistence.md) | 合成数据、草稿存储、幂等防重、冲突校验 |
| [05-prompt-and-policy.md](05-prompt-and-policy.md) | 系统提示词、决策策略、状态枚举、确认边界 |
| [06-scenarios-and-evaluation.md](06-scenarios-and-evaluation.md) | 10 个场景（Given/When/Then）、测试与评估方案 |
| [07-tasks.md](07-tasks.md) | 分阶段任务清单、时间分配、提交前检查 |

## 已定的关键决策

1. **Python 3.10+ / CLI / 自己写 ReAct 循环**（不用框架）。核心循环约 150 行，好讲清楚；评审明确说框架名不加分。
2. **模型**：OpenAI 兼容接口 + function calling，DeepSeek 和通义千问二选一，`.env` 切换。另带一个离线 Scripted Mock，只验证流程。
3. **模型做决策，代码守红线**。补查、换时段、请求确认、阻断都由模型通过调用工具来决定；"不发布、不虚报保存、不擅改硬性要求、不重复建草稿"写死在代码里，提示词写错也守得住。
4. **系统里根本没有发布工具**，草稿状态枚举里也没有 `published`。
5. **幂等键由代码算，不让模型传**：把请求规范化后取 sha256。同一请求重复提交，命中同一份草稿（内容相同返回 `duplicate`，内容变了就升版本 `updated`）。
6. **最终结果里的保存状态取自工具执行记录**，不采信模型自己的说法。
7. 存储用 JSON 文件加原子写（先写临时文件再 rename）。评审可以直接打开文件核对"只有一份草稿"。生产环境的升级方案写进文档。

## 关于 OpenSpec

不必用。这套规格已经有了 OpenSpec 的核心要素：需求、设计、带 Given/When/Then 的验收场景、任务清单。3 小时的单体项目再引入 OpenSpec 的 CLI 和 change/archive 流程，收益不大。
如果你想用，对应关系是：`07-tasks.md` → `tasks.md`，`06` 里的场景 → `specs/*/spec.md` 的 Scenario，`02~05` → `design.md`。

## 交给实现 AI 的启动提示词（可直接复制）

```text
你在 q1-material-scheduler/ 目录下工作。先完整阅读 spec/ 下的全部文件，再按 spec/07-tasks.md 的阶段顺序实现。
要求：
1. 不得修改 spec/ 中的验收标准；遇到规格未覆盖的决策，自行做最简单的合理选择，并记录到 docs/02-solution.md 的"实现中的决策"一节。
2. 每完成一个阶段就运行 pytest，全部通过后再进入下一阶段，并在 spec/07-tasks.md 里勾选完成项。
3. 红线（违反即严重缺陷）：不得实现任何发布能力；最终输出的保存状态必须来自工具真实返回；硬性发布要求未经用户确认不得改变；同一请求只能有一份草稿。
4. 真实模型的 Trace 必须用真实 API 跑出来，不得手写或用 Mock 冒充。
5. 不要提交 .env 和任何真实密钥。
```

## 你自己要做的（AI 替代不了）

- 用真实 Key 跑出 `examples/` 下的 live Trace，并逐条核对是否符合预期。
- 在 `docs/04-ai-usage.md` 如实写明：规格由 AI 起草、实现由 AI 生成、你改了哪些地方、怎么验证的、实际用了多长时间。
- 能讲清楚每条红线是在哪一行代码里守住的。面试大概率会问。
