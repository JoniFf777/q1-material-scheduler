import json
from collections import Counter

from .domain.fingerprint import canonical
from .domain.models import Limits
from .llm.base import ModelUnavailable
from .prompt import initial_messages
from .result import finalize
from .tools.common import error
from .tools.registry import ToolRegistry
from .trace import Trace


def run(ctx, llm, limits=None, registry=None, input_file=None, today="2026-11-08"):
    limits = limits or Limits()
    registry = registry or ToolRegistry()
    messages = initial_messages(ctx.request, ctx.confirmations, today)
    trace = Trace(ctx, llm, limits, input_file)
    counts = Counter()

    def finish(report=None, termination=None):
        result = finalize(ctx, report, termination)
        return result, trace.finish(result)

    for step in range(1, limits.max_steps + 1):
        try:
            response = llm.chat(messages, registry.schemas())
        except ModelUnavailable as exc:
            # ModelUnavailable carries a sanitized error code, never raw API text.
            return finish(termination="MODEL_UNAVAILABLE:" + str(exc))
        trace.model_call(step, response)
        messages.append(response.message())
        if not response.tool_calls:
            trace.data.setdefault("events", []).append({"step": step, "event": "no_tool_call"})
            messages.append({"role": "user", "content": "请调用工具继续，或调用 submit_report 结束。"})
            continue
        for call in response.tool_calls:
            if ctx.tool_calls_used >= limits.max_tool_calls:
                return finish(termination="MAX_TOOL_CALLS_REACHED")
            try:
                args = json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
            except (ValueError, TypeError):
                args = {"invalid_arguments": call.arguments}
            signature = (call.name, canonical({k: v for k, v in args.items() if k != "reason"}) if isinstance(args, dict) else canonical(args))
            ctx.tool_calls_used += 1
            counts[signature] += 1
            if counts[signature] > limits.max_same_call:
                obs = error("REPEATED_CALL", "相同工具和参数已达上限，请换策略或结束")
                if call.name == "save_schedule_draft":
                    ctx.save_observation = obs
            else:
                obs = registry.execute(call.name, call.arguments, ctx)
            trace_args = args if isinstance(args, dict) else {"invalid_arguments": args}
            trace.record(step, call, trace_args, obs)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(obs, ensure_ascii=False)})
            if call.name == "submit_report" and obs["ok"]:
                return finish(args)
    return finish(termination="MAX_STEPS_REACHED")
