# 实现记录

当前状态：阶段 0–5 与公开 GitHub 交付已完成，真实模型 33/33、离线测试 76/76、新克隆验证通过。个人文档经候选人授权由 Codex 按实际记录协助整理，以下保留各阶段的历史结果。

- 最终离线校验：pytest 74/74，通过输出保存于 examples/results/pytest.txt；11 场景逐一通过，额外验证了 repeat=3 和 --only 的前置状态。文档本地链接检查 30 项，无失效链接；常见密钥模式扫描无匹配，.env/runtime/.venv 的忽略规则生效。此处不代表新克隆或 Live 验收已经完成。

- 2026-11-09（Asia/Shanghai）：整合本地代码后，阶段 2 验证 45 项测试与 S04 离线运行通过；阶段 3 补齐 CLI、输入校验、场景执行器、文档与场景回归，64 项测试通过，11 个 Mock 场景通过。真实 API 尚未调用，docs/04、docs/05 保留本人填写。

- 开始：2026-11-08 23:42（Asia/Shanghai）。本记录是 AI 的执行事实，不代写候选人的个人贡献和复盘。
- 授权范围：按阶段 0–3 实现并验证离线链路；真实模型调用留到阶段 4。
- 初始状态：8 份规格、最小 CLI、1 个帮助测试，尚未初始化 Git。
- 环境：系统 `python` 是 3.8.10；项目已有 `.venv` 是 3.10.9，后续统一使用项目虚拟环境。
- 阶段 0：editable 安装成功，CLI --help 正常，pytest 1/1 通过。
- 阶段 1：工具/校验/存储/指纹专项测试 30/30；全量 pytest 31/31。沙箱下指定 --basetemp=runtime/pytest-phase1-all，避免系统临时目录的替换权限限制。阶段 0 首次提交同时收录了检查期间出现的基础业务代码，本阶段已审查、修正并验证。
- 阶段 2：pytest 45/45；CLI S04 Mock 实跑为 19:00 / pending / created，写出 result.json 和 JSON/Markdown Trace。SDK 的 HTTP MockTransport 测试不连接网络、不作为 live 证据。
- 阶段 3：pytest 74/74；11 个 Mock 场景全部通过，实际结果与 JSON/Markdown Trace 已保存到 examples/mock。CLI 手动串行运行 S04→S06→S06b，得到 created v1→duplicate v1→updated v2，最终只有一份草稿。
- 收尾检查：pip check 无依赖冲突；本地文档链接有效；未发现密钥模式；.env 与 runtime 被 Git 忽略。live API 未调用，docs/04 与 docs/05 保留给本人填写。
- 本轮离线实现与验证时段：2026-11-08 23:42 至 2026-11-09 00:08（Asia/Shanghai，约 26 分钟；不是候选人的个人实际用时）。阶段 4、完整交付文档与 GitHub 提交仍待完成。
- 阶段 4 开始：2026-11-09 14:10（Asia/Shanghai）。候选人在本机配置 Key 并手动运行 S04；实际返回 deepseek-flash，26,535 tokens，19:00 / pending / created；原始证据保留为 examples/live/manual-S04_slot_conflict.*。
- 手动 S04 中，模型把时间调整待确认混成审核 needs_confirmation；guards 拒绝后模型修正 approved。报告的时间字段另带 douyin 前缀，结果组装采用已保存的标准时间并保留 warning。
- 批量运行前发现执行环境使用 SOCKS 代理，缺少 socksio 导致客户端初始化失败，尚未调用模型。补齐并显式声明 httpx[socks]，不记录代理地址和 Key。
- 修正前真实模型评估为 30/33；3 次失败均为 S09 评估器硬编码 M07=unknown，而模型通过批量调用已经完成其审核。真实行为均为 4 轮后 incomplete / MAX_STEPS_REACHED / not_saved。原始汇总和 S09 Trace 已保留，没有覆盖原始失败记录。
- 根据 spec/06“未处理素材为 unknown”，移除生成场景中对特定 M07 的错误断言，改为从本次工具事实核验所有未审核素材。没有修改 spec/ 或业务循环。新增回归测试修正前为 1 failed / 1 passed；修正后将重新运行完整评估。
- 修正后全量离线测试 76/76。新克隆使用独立虚拟环境安装声明依赖成功；首次执行 README 测试命令时发现 runtime 父目录尚不存在，17 passed / 59 setup errors。补充显式创建 runtime 的安装步骤，再重跑新克隆验证；业务代码不受此问题影响。
- 阶段 4 复测完成：2026-11-09 14:32（Asia/Shanghai），deepseek-flash 33/33，I1–I7 均通过。33 次统计合计 667,684 tokens，不含基线、前置准备和单独验证。
- 新克隆源码提交 3071a86，独立环境安装 / CLI --help / pip check / 76 项测试 / 11 个 Mock 场景通过；真实 S04 也得到 19:00 / pending / created，API 返回 deepseek-flash，17,517 tokens。
- 技术文档已回填实际结果、路径对照与失败修正，.env.example 使用实际验证模型名。候选人的两份个人文档仍未代写；GitHub 仓库地址尚未配置。
- 阶段 5：候选人后续授权由 Codex 协助总结个人文档。已按实际记录区分候选人操作和 AI 工作，补齐 AI 使用说明与工程复盘，未将自动执行的工作归为个人手写代码贡献。
- GitHub：候选人明确选择公开，使用当前登录账号 JoniFf777，新建并推送到 https://github.com/JoniFf777/q1-material-scheduler。发布前检查了工作文件和完整 Git 对象历史，没有发现真实 Key；.env、.venv、runtime 与 IDE 配置均未纳入交付。
