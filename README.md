# 素材审核与排期草稿 Agent

Python 3.10+，CLI，模型负责决策，代码校验红线。实现规格见 [spec/README.md](spec/README.md)。

安装（Windows PowerShell）：

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\schedule-agent.exe --help
.\.venv\Scripts\python.exe -m pytest --basetemp runtime/pytest
.\.venv\Scripts\python.exe scripts/run_scenarios.py --llm mock
```

离线 Mock 仅验证流程，不证明真实模型决策效果。真实模型验证尚未执行。
任务进度见 [spec/07-tasks.md](spec/07-tasks.md)。

## 快速运行

以下命令均在仓库根目录执行。系统没有发布工具，只保存草稿。

```powershell
.\.venv\Scripts\schedule-agent.exe run --llm mock --input examples/inputs/S04_slot_conflict.json --state-dir runtime/manual-s04 --out runtime/outputs/S04.mock
.\.venv\Scripts\schedule-agent.exe drafts list --state-dir runtime/manual-s04
```

预期 M01 建议 `2026-11-10T19:00`、`alternative`、`pending`，显示“草稿已保存（待确认，未发布）”。输出前缀生成 `.result.json`、`.trace.json`、`.trace.md`；草稿在状态目录的 `drafts.json`。

macOS/Linux 可使用 `python3 -m venv .venv`，将可执行路径换为 `.venv/bin/python` 和 `.venv/bin/schedule-agent`。Windows 沙箱使用仓库内 pytest 临时目录可避开系统临时目录的替换权限限制。

## 真实模型

复制 `.env.example` 为本机 `.env`，填写 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`，使用支持 function calling 的 OpenAI 兼容服务。示例提供 DeepSeek 和千问配置，实际模型名以服务方支持为准。Key 不要写入命令行或示例 JSON，`.env` 已忽略。

```powershell
Copy-Item .env.example .env
# 编辑本机 .env 后执行
.\.venv\Scripts\schedule-agent.exe run --llm live --input examples/inputs/S04_slot_conflict.json --state-dir runtime/live-s04 --out examples/live/S04_slot_conflict
.\.venv\Scripts\python.exe scripts/run_scenarios.py --llm live --repeat 3
```

调用会使用配置的真实 API。请本人核对结果：第 1 次结果与 Trace 写入 `examples/live/`，重复运行只汇总到 `examples/results/live_summary.md` 与 `.json`。当前没有真实模型 Trace，也没有 Live 通过率。

## 评审入口

统一命令：`python scripts/run_scenarios.py --llm mock --only <场景>`；切换为 `--llm live --repeat 3` 即为真实模型验证。以下证据均为固定脚本离线结果。

| 验收点 | `--only` 场景 | 离线 Trace |
|---|---|---|
| A1 正常排期 | S01_normal | [S01](examples/mock/S01_normal.mock.trace.md) |
| A2 信息补查 | S02_missing_info | [S02](examples/mock/S02_missing_info.mock.trace.md) |
| A3 规则风险 | S03_rule_risk | [S03](examples/mock/S03_rule_risk.mock.trace.md) |
| A4 软冲突 / fixed 冲突 | S04_slot_conflict S05_hard_conflict | [S04](examples/mock/S04_slot_conflict.mock.trace.md)、[S05](examples/mock/S05_hard_conflict.mock.trace.md) |
| A5 重复与占用变化 | S06_duplicate S06b_slot_changed | [S06](examples/mock/S06_duplicate.mock.trace.md)、[S06b](examples/mock/S06b_slot_changed.mock.trace.md) |
| A6 保存失败 | S07_save_failure | [S07](examples/mock/S07_save_failure.mock.trace.md) |

[全量 Mock 汇总](examples/results/mock_summary.md)；[pytest 输出](examples/results/pytest.txt)。共 11 项场景，包括 S06b 与文件形式的第二轮确认 S10。`--only` 可指定多个场景，自动准备 S06/S06b/S10 前置状态；每次运行使用新的批次目录，每轮使用独立状态。

## 更换占用时段并重复提交

以下命令使用同一个状态目录。reset 只删除该目录下的 drafts.json。

```powershell
.\.venv\Scripts\schedule-agent.exe reset --state-dir runtime/repeat-demo
.\.venv\Scripts\schedule-agent.exe run --llm mock --input examples/inputs/S04_slot_conflict.json --state-dir runtime/repeat-demo
.\.venv\Scripts\schedule-agent.exe run --llm mock --input examples/inputs/S06_duplicate.json --state-dir runtime/repeat-demo
.\.venv\Scripts\schedule-agent.exe run --llm mock --input examples/inputs/S06b_slot_changed.json --state-dir runtime/repeat-demo
.\.venv\Scripts\schedule-agent.exe drafts list --state-dir runtime/repeat-demo
```

依次得到 created v1、duplicate v1、updated v2，始终只有 1 份草稿。S06b 的内存补丁把 M90 从 18:00 移到 19:00，最终回到原要求的 18:00，种子文件不改变。查询中自身旧草稿显示 held_by_this_request，视为可用；与外部占用重叠时 occupied 优先。

也可手动编辑 `data/schedule.json`，使用 Live 重跑原 S04。固定 Mock 脚本不会因任意数据变化自动选择新策略，临时变体需用 Live 验证。

## CLI、输入与限制

run 支持 `--input --llm --state-dir --data-dir --max-steps --max-tool-calls --fault --out` 和 `--mock-script`。故障示例：`--fault query_slots=once --fault save_schedule_draft=always`。`--out` 是文件前缀。`drafts show <draft_id> --state-dir ...` 查看原始草稿。完成退出码 0，运行失败/达到限额为 1，输入或配置错误为 2。

输入见 [S04](examples/inputs/S04_slot_conflict.json)，只有 request、confirmations 和用于复现的日期传给模型，setup 与 expect 留在执行侧。scope=pending 需要 defaults 明确给出 channel、preferred_time 等要求。第二轮时间确认须包含具体 proposed_slot，见 [S10](examples/inputs/S10_confirm_round2.json)。

实现说明见[需求](docs/01-requirements.md)、[方案与代码防线](docs/02-solution.md)、[评估](docs/03-evaluation.md)、[执行记录](docs/implementation-log.md)。JSON 存储没有跨进程锁，生产环境需要事务和唯一约束。当前没有自然语言解析、真实发布、HTTP 服务或终端交互确认；时段粒度为整点。

[AI 使用说明](docs/04-ai-usage.md)与[个人复盘](docs/05-retrospective.md)保留给本人填写。真实模型验证完成前，不应宣称 A1–A6 已通过 Live 验收。
