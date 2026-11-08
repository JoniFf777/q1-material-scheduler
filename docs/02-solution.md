# 方案与实现决策

使用 Python 3.10+、CLI、原生工具调用循环。模型选择动作，工具与保存校验维护业务边界。细节见 `spec/02-architecture.md` 到 `spec/05-prompt-and-policy.md`。

## 实现中的决策

- 场景数量以 `spec/06` 的逐项清单为准：S01–S10 加 S06b，共 11 项，保留全部验收标准。
- M08 不存在时，工具记录可信的 `NOT_FOUND` 事实；仅允许以 `need_info`、空时段保存，不将缺失素材视作审核通过。
- 对幂等内容按业务语义归一化：确认项 ID 由素材、确认类型和提议时段派生；模型措辞和检查顺序不造成无意义的版本变化。
- 固定时间保持原值或空值（I4）。放宽约束应提交新的明确请求；第二轮确认支持 flexible 替代时段的用户确认。

工具调用格式参考 [OpenAI 官方 function calling 文档](https://developers.openai.com/api/docs/guides/function-calling)：逐个执行 tool_calls，并使用 tool_call_id 回传结构化工具结果。接口协议已用本地 SDK + HTTP MockTransport 验证，尚未验证第三方真实模型。
