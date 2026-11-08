# 方案与实现决策

使用 Python 3.10+、CLI、原生工具调用循环。模型选择动作，工具与保存校验维护业务边界。细节见 `spec/02-architecture.md` 到 `spec/05-prompt-and-policy.md`。

## 实现中的决策

- 场景数量以 `spec/06` 的逐项清单为准：S01–S10 加 S06b，共 11 项，保留全部验收标准。
- M08 不存在时，工具记录可信的 `NOT_FOUND` 事实；仅允许以 `need_info`、空时段保存，不将缺失素材视作审核通过。
- 对幂等内容按业务语义归一化：确认项 ID 由素材、确认类型和提议时段派生；模型措辞和检查顺序不造成无意义的版本变化。
- 固定时间保持原值或空值（I4）。放宽约束应提交新的明确请求；第二轮确认支持 flexible 替代时段的用户确认。

- 种子表格补齐为最小合成 JSON，有效授权默认到 2027-12-31；M04/M07 使用指定授权库数据。词库使用明确标为合成的违禁词。
- 结构化输入校验格式、策略、约束和确认记录，拒绝重复素材。time_policy 默认 flexible，constraints 默认空对象，日期和渠道默认固定。
- scope=pending 使用 defaults 明确默认渠道和时间，并将 defaults 纳入指纹，防止不同要求覆盖同一请求。
- 保存时风险原因来自审核 finding；确认 ID 基于素材、类型与提议时段生成。条目及确认引用排序，确认问题/选项的措辞不触发业务版本更新。
- S04/S06/S06b 共用状态；S10 单独先跑 S04，避免先前占用变化造成版本串扰。每轮 repeat 使用独立目录。
- --out 是文件前缀。完成退出码 0，运行失败或限额终止为 1，输入/配置错误为 2。
- 每次评估使用新的批次目录，不清空其他批次的状态；`--out-dir` 可指定评估材料目录。
- 保存后如果补查发现新风险，`submit_report` 会要求重新保存有效草稿，不能用旧快照直接结束。
- Live 评估还校验 API 返回的模型名和正数 token 用量，缺失时不能当作有效决策证据。

## 红线的代码位置

| 边界 | 实现 |
|---|---|
| 不发布 | tools/registry.py 只注册 7 个工具；domain/models.py 无发布状态；trace.py 屏蔽发布成功表述，render.py 模板生成总结 |
| 不虚报保存 | registry 记录真实保存返回，result.py 的 save_result/finalize 只从记录组装 draft_save，模型说法不符则 warning |
| 不改硬要求 | 独立 domain/guards.py 校验 fixed、日期、渠道、时间范围、禁发期、整点网格 |
| 不自行确认 | tools/confirm.py 仅匹配用户输入；guards 校验确认类型、具体时段、引用 ID 与用户状态 |
| 不重复草稿 | domain/fingerprint.py 代码计算键；store/draft_store.py 同键 created/duplicate/updated，ID 不变 |
| 不跳过审核 | guards 校验本次 checked 账本；NOT_FOUND 只允许 need_info 空时段 |
| 不绕过硬风险 | guards 对照规则结论，block/need_info/unknown 不允许带时段 |

## 循环与事实账本

agent.py 默认最多 15 轮、30 个工具调用；相同业务调用最多执行 3 次，reason 改写不能绕过。按序执行同轮调用，将观察回传给模型。纯文本回复被提示继续；错误返回给模型修正。SDK 超时 60 秒，传输错误最多重试 2 次。

RunContext 保存工作视图、审核、查询、确认和保存尝试/成功快照。full 补查采用合并，不会丢失已查授权信息；深查重新评估全部已知事实。结束报告不能覆盖成功保存快照，没有成功保存时不安全的建议也会被移除并记 warning。

## 存储与生产升级

请求素材排序后规范化并计算 sha256，代码派生请求键和草稿 ID；note 与用户确认不影响身份。保存先校验再故障注入，写临时文件、flush/fsync 后 os.replace；duplicate 不写文件，updated 版本加一并保留 history。

占用来自已有排期与其他请求草稿，本请求旧草稿视为可用。与外部占用重叠时 occupied 优先，请求内部争抢同一时段同样拒绝。

JSON 适用于单进程 CLI，没有跨进程锁。生产环境需要数据库事务、幂等键唯一约束、渠道时段唯一约束，并接入真实授权、身份与审计服务。当前用户确认信任本机结构化输入，不提供身份认证。

工具调用格式参考 [OpenAI 官方 function calling 文档](https://developers.openai.com/api/docs/guides/function-calling)：逐个执行 tool_calls，并使用 tool_call_id 回传结构化工具结果。接口协议已用本地 SDK + HTTP MockTransport 验证，尚未验证第三方真实模型。
