# 02 架构与 ReAct 循环

## 1. 总体结构

```
CLI (run / drafts / reset / scenarios)
   │
   ▼
Agent 循环 (agent.py) ──── LLMClient ── OpenAICompatClient (DeepSeek / Qwen)
   │                              └─── ScriptedMockLLM (离线，仅验证流程)
   ▼
ToolRegistry：参数校验 → 故障注入 → 执行 → 结构化观察结果
   │
   ├── materials / rules / slots / confirm / report  (读 data/ 下的种子 JSON)
   └── drafts ── Guards(红线校验) ── DraftStore(state 目录下的 drafts.json)
   │
   ▼
RunContext（本次运行的事实账本）→ Trace（JSON + Markdown）→ 最终结果组装
```

## 2. 目录结构（src）

```
src/schedule_agent/
  cli.py              # argparse 入口
  config.py           # 读取 .env、限额默认值
  agent.py            # ReAct 主循环
  context.py          # RunContext：已检查素材、时段查询、确认、保存记录
  llm/
    base.py           # LLMClient 协议、LLMResponse、ToolCall
    openai_compat.py  # 真实模型
    mock.py           # ScriptedMockLLM：按脚本依次返回 tool_calls
  tools/
    registry.py       # 工具 schema、分发、参数校验、故障注入
    materials.py  rules.py  slots.py  drafts.py  confirm.py  report.py
  domain/
    models.py         # 枚举和 dataclass（见 05 第 3 节）
    guards.py         # 保存校验和最终结果校验
    fingerprint.py    # 规范化 JSON + sha256
  store/
    seed_repo.py      # 读取 materials / rules / schedule
    draft_store.py    # JSON 草稿存储（见 04）
  trace.py            # 记录步骤，渲染 trace.json / trace.md
  render.py           # 最终结果 → 终端文本 / result.json
```

文件多可以合并，但 `guards.py` 必须独立成文件。评审重点看它。

## 3. 主循环（伪代码）

```python
def run(request, llm, limits, ctx) -> RunResult:
    messages = [system_prompt(), user_message(request, ctx.confirmations)]
    for step in range(1, limits.max_steps + 1):
        resp = llm.chat(messages, tools=registry.schemas())       # 网络错误重试 2 次，仍失败 → status=failed
        messages.append(resp.assistant_message)
        if not resp.tool_calls:                                   # 模型只回了文本
            ctx.trace.note(step, "no_tool_call")
            messages.append(user("请调用工具继续，或调用 submit_report 结束"))
            continue
        for call in resp.tool_calls:                              # 一次可能返回多个调用，按顺序执行
            if ctx.tool_calls_used >= limits.max_tool_calls:
                return ctx.incomplete("MAX_TOOL_CALLS_REACHED")
            if ctx.repeat_count(call) >= limits.max_same_call:    # 同工具、同参数反复调用
                obs = error("REPEATED_CALL", "相同调用已达上限，请换策略或结束")
            else:
                obs = registry.execute(call, ctx)                 # 异常一律转成 {ok:false, error_code}
            ctx.trace.record(step, call, obs)
            messages.append(tool_message(call.id, obs))
            if call.name == "submit_report" and obs.ok:
                return ctx.finalize(call.args)                    # 见第 6 节
    return ctx.incomplete("MAX_STEPS_REACHED")
```

要点：

- **循环本身不含业务分支**。查什么、换不换时段、阻不阻断，都由模型看了观察结果后决定。代码只做执行、校验和记账。
- 工具报错不会终止循环，而是作为观察结果交给模型。模型决定重试、换方案，还是如实结束。
- `submit_report` 校验不通过（比如漏了素材）时，会把错误返回给模型修正，这次修正同样计入步数。

## 4. 限额

| 项 | 默认 | CLI 参数 |
|---|---|---|
| `max_steps`（LLM 调用轮数） | 15 | `--max-steps` |
| `max_tool_calls` | 30 | `--max-tool-calls` |
| `max_same_call`（同工具同参数） | 3 | 不开放 |
| LLM 请求超时 / 重试 | 60s / 2 次 | 不开放 |

达到上限时返回：

```json
{ "status": "incomplete", "incomplete_reason": "MAX_STEPS_REACHED",
  "items": [ ... 已完成的照常输出，未处理的 review_status = "unknown" ... ],
  "draft_save": { "status": "not_saved" 或实际结果 } }
```

## 5. Trace 规范

每次运行写两个文件：`<name>.trace.json`（机器可读）和 `<name>.trace.md`（评审看的表格）。

```json
{
  "run_id": "run-20261110-153012-a1b2",
  "llm": { "mode": "live", "provider": "deepseek", "model": "deepseek-chat", "temperature": 0 },
  "input_file": "examples/inputs/04_slot_conflict.json",
  "limits": { "max_steps": 15, "max_tool_calls": 30 },
  "steps": [
    { "step": 3, "tool": "query_slots",
      "args": { "channel": "douyin", "date": "2026-11-10", "from": "17:00", "to": "21:00" },
      "reason": "M01 无风险，查询 18:00 附近可用时段",
      "ok": true,
      "result_summary": "18:00 被 M90 占用；19:00、20:00 可用",
      "next_action": "request_confirmation(M01: 18:00→19:00)" }
  ],
  "status": "completed_with_pending",
  "usage": { "prompt_tokens": 0, "completion_tokens": 0 }
}
```

- `reason`：每个工具都有一个必填参数 `reason`（30 字以内），由模型填写，作为"简要决策依据"。不记录思维链。
- `result_summary`：由各工具自己生成的一句话摘要（代码生成，不是模型写的）。
- `next_action`：渲染时取下一步的工具和关键参数自动填入。
- Markdown 版是一张表：步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据。

## 6. 最终结果组装（防虚报的关键）

`ctx.finalize(report_args)` 的处理：

1. 以 RunContext 里的**事实**为准：最后一次 `save_schedule_draft` 的真实返回、哪些素材跑过检查、哪些确认项已登记。
2. 模型在 `submit_report` 里提供的是逐个素材的结论和风险原因，代码负责合并：
   - `draft_save` 字段**只**从事实里取。如果模型说"已保存"而事实是失败，按失败输出，并加一条 `consistency_warnings`。
   - 模型标成 `approved` 但规则检查结果是 block，同样以规则结果为准，并加 warning。
3. 面向人看的总结文本由 `render.py` 用模板生成，不直接用模型的自由文本，从根上杜绝"已发布"这类措辞。
4. 输出里固定带一个字段：`"publish_action": "none"`，并附一句说明"本系统仅生成排期草稿，未执行任何发布"。

## 7. LLM 客户端

- `OpenAICompatClient`：使用 `openai` SDK，配置 `base_url`、`api_key`、`model`，设 `temperature=0`。把 SDK 返回的结果转换成统一的 `LLMResponse(tool_calls, content, usage)`。
- 参数 JSON 解析失败时，不抛异常，而是给模型回一条错误观察 `INVALID_ARGUMENTS`。
- `ScriptedMockLLM`：构造时传入一个响应脚本（每一轮返回哪些 tool_calls）。脚本放在 `tests/fixtures/mock_scripts/`。它**不看**观察结果，所以只能证明流程能跑通，README 和 03-evaluation 都要写明这一点。
