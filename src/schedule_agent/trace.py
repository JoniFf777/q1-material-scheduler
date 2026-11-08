import copy
import json
from pathlib import Path


FORBIDDEN_CLAIMS = ("已发布", "发布成功", "已上线")


def safe_text(value):
    if isinstance(value, str):
        for claim in FORBIDDEN_CLAIMS:
            value = value.replace(claim, "[发布表述已屏蔽]")
        return value
    if isinstance(value, list):
        return [safe_text(v) for v in value]
    if isinstance(value, dict):
        return {safe_text(k): safe_text(v) for k, v in value.items()}
    return value


class Trace:
    def __init__(self, ctx, llm, limits, input_file=None):
        self.data = {"run_id": ctx.run_id, "llm": copy.deepcopy(llm.metadata),
            "input_file": str(input_file) if input_file else None,
            "limits": vars(limits), "steps": [], "model_calls": [],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0}}

    def model_call(self, step, response):
        self.data["model_calls"].append({"step": step, "model": response.model,
            "usage": response.usage, "tool_calls": len(response.tool_calls)})
        for key in self.data["usage"]:
            self.data["usage"][key] += response.usage.get(key, 0) or 0
        if response.model:
            self.data["llm"]["response_model"] = response.model

    def record(self, step, call, args, obs):
        self.data["steps"].append(safe_text({"step": step, "tool_call_id": call.id,
            "tool": call.name, "args": copy.deepcopy(args),
            "reason": args.get("reason", "") if isinstance(args, dict) else "",
            "ok": obs["ok"], "observation": copy.deepcopy(obs),
            "result_summary": obs.get("summary", obs.get("message", "")), "next_action": None}))

    def finish(self, result):
        self.data.update(status=result["status"], incomplete_reason=result.get("incomplete_reason"),
                         termination_reason=result.get("failure_reason"))
        steps = self.data["steps"]
        for current, following in zip(steps, steps[1:]):
            args = following["args"]
            key = {k: v for k, v in args.items() if k in ("material_id", "scope", "proposed_slot", "date")}
            current["next_action"] = following["tool"] + " " + json.dumps(key, ensure_ascii=False)
        if steps:
            steps[-1]["next_action"] = "结束：" + result["status"]
        self.data = safe_text(self.data)
        return self.data


def write_artifacts(prefix, result, trace):
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for suffix, value in (("result.json", result), ("trace.json", trace)):
        Path(str(prefix) + "." + suffix).write_text(json.dumps(safe_text(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def cell(value):
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        return text.replace("|", "\\|").replace("\n", "<br>")
    lines = ["# 运行 Trace", "", f"模式：{trace['llm']['mode']}；模型：{trace['llm']['model']}；状态：{result['status']}", ""]
    if trace["llm"]["mode"] == "mock":
        lines += ["离线固定脚本，只验证流程；不证明真实模型决策效果。", ""]
    lines += ["| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |", "|---|---|---|---|---|---|"]
    for s in trace["steps"]:
        lines.append("| " + " | ".join(cell(v) for v in (s["step"], s["tool"], s["args"], s["result_summary"], s["next_action"], s["reason"])) + " |")
    lines += ["", f"Token 用量：{json.dumps(trace['usage'])}", ""]
    Path(str(prefix) + ".trace.md").write_text("\n".join(lines), encoding="utf-8")
