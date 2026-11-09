# 07 任务清单

按阶段实现。每个阶段的"完成标准"都满足后，再进入下一阶段。时间是参考值（总共约 3 小时），实际用时记进 docs/04。

## 阶段 0：脚手架（15 分钟）

- [x] `pyproject.toml`（包名 `schedule_agent`，命令行入口 `schedule-agent`），同时给一份 `requirements.txt`：`openai`、`python-dotenv`、`pytest`
- [x] `.env.example`：`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`，并附 DeepSeek 和千问的示例值（Key 留空）
- [x] `.gitignore`：`.env`、`runtime/`、`__pycache__/`、`.pytest_cache/`
- [x] 建好目录骨架（见 02 第 2 节）、`docs/` 下 5 个空文档、README 骨架
- **完成标准**：`pip install -e .` 成功，`schedule-agent --help` 能输出帮助

## 阶段 1：数据、工具、存储、红线（45 分钟）

- [x] `data/` 下的种子文件，内容完全按 04 第 2 节
- [x] `domain/models.py` 枚举、`domain/fingerprint.py`
- [x] 6 个业务工具和 `submit_report`，统一返回结构，生成 `summary`
- [x] `store/draft_store.py`：created / duplicate / updated，原子写入
- [x] `domain/guards.py`：03 第 6 节的 9 个违规码
- [x] `tools/registry.py`：schema、参数校验、故障注入、把异常转换成错误结构
- [x] 单元测试：06 第 3 节列出的红线测试全部写上
- **完成标准**：`pytest tests/test_tools.py tests/test_guards.py tests/test_draft_store.py tests/test_fingerprint.py` 全部通过

## 阶段 2：LLM 与主循环（45 分钟）

- [x] `llm/openai_compat.py`、`llm/mock.py`（ScriptedMockLLM）
- [x] `context.py`、`agent.py`（02 第 3 节）、限额、重复调用检测
- [x] `trace.py`：输出 trace.json 和 trace.md，带 reason、summary、next_action
- [x] 最终结果组装（02 第 6 节）、`render.py` 用模板渲染文本
- [x] `checks.py`：不变式 I1–I7
- [x] `tests/test_agent_loop.py`，mock 脚本放在 `tests/fixtures/mock_scripts/`
- **完成标准**：离线 `pytest` 全部通过；`schedule-agent run --llm mock --input examples/inputs/S04_slot_conflict.json` 能输出结果和 Trace

## 阶段 3：CLI 与场景（30 分钟）

- [x] CLI：`run`（`--input --llm --state-dir --data-dir --max-steps --max-tool-calls --fault --out`）、`drafts list/show`、`reset`
- [x] 10 个场景文件，每个都带 `expect`
- [x] `scripts/run_scenarios.py`：执行组合场景、`--repeat`、`--only`，生成 summary
- **完成标准**：`python scripts/run_scenarios.py --llm mock` 能把全部场景跑完（mock 下断言可能不全通过，但流程不能报错）

## 阶段 4：真实模型跑通（30 分钟，这一步你要亲自参与）

- [x] 填好 `.env`，先单独跑 S04，核对是不是 19:00、待确认、没有"已发布"
- [x] `run_scenarios.py --llm live --repeat 3`
- [x] 失败的用例：先判断是提示词问题还是代码问题，修正后重跑。**每一次修正都记下来**，这是 03 和 05 最好的素材
- [x] 把 live 结果和 Trace 存进 `examples/live/`，pytest 输出存进 `examples/results/pytest.txt`
- **完成标准**：A1–A6 在 live 下都有至少 1 次通过的 Trace；I1–I7 的不变式在所有 live 运行中都没有被违反

## 阶段 5：文档（25 分钟）

| 文档 | 来源 |
|---|---|
| README.md | 环境、安装、配置、离线快速验证、live 运行、**评审入口**（验收点 → 命令 → 结果文件）、"更换占用时段并重复提交"的操作步骤 |
| docs/01-requirements.md | spec/01 精简 |
| docs/02-solution.md | spec/02–05 精简，加上"实现中的决策" |
| docs/03-evaluation.md | spec/06 第 6 节，填上真实结果 |
| docs/04-ai-usage.md | **你自己写**：规格是 AI 起草的，代码是哪个 AI 生成的，你改了什么，怎么验证的，实际用时 |
| docs/05-retrospective.md | **你自己写**：最难的问题、学到了什么、下一步打算 |

05 里"最难的问题"可以写的候选（看实际遇到的情况挑）：重复提交时自己的旧草稿被当成冲突；模型想自行标记 confirmed；模型对 fixed 时间也想换时段；保存失败后模型的措辞仍然像成功了。

## P1（时间够再做）

- [ ] S10 第二轮确认；`--interactive` 在终端里当场确认
- [ ] M09 禁发期（素材侧的硬约束）
- [ ] DeepSeek 和千问的对比（通过率、步数、tokens）
- [ ] HTTP API 外壳（不是必需的，CLI 已经满足要求）

## 提交前检查

- [x] 新克隆一份仓库，按 README 从零执行一遍：安装 → pytest → mock 运行 → live 运行
- [x] `git grep -n "sk-"`，以及搜一遍 Key 的常见前缀，确认没有提交密钥；`.env` 没有进仓库
- [x] 03-evaluation 里引用的每个文件路径都真实存在
- [x] 06 第 1 节的所有场景都有对应的 live 文件，或者在文档里说明了为什么没有
- [x] 提交信息里写上：题号（第一题）、GitHub URL、最终 commit SHA
