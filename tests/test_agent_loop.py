import copy
import json

from schedule_agent.agent import run
from schedule_agent.domain.models import Limits
from schedule_agent.llm.mock import ScriptedMockLLM
from schedule_agent.tools.registry import ToolRegistry
from schedule_agent.checks import check_invariants
from conftest import draft_item, requirement


def tool(name, **args):
    return {"name": name, "arguments": dict(args, reason="验证循环与事实边界")}


def round_(*calls):
    return {"calls": list(calls)}


def report(mid="M02", review="approved", slot="2026-11-10T20:00", confirmation="not_required", note="仅生成草稿"):
    return tool("submit_report", items=[{"material_id": mid, "review_status": review,
        "risk_reasons": [], "suggested_slot": slot, "confirmation_status": confirmation,
        "pending_items": []}], overall_note=note)


def normal_script():
    return [round_(tool("get_material", material_id="M02")),
            round_(tool("check_rules", material_id="M02", scope="basic")),
            round_(tool("query_slots", channel="douyin", date="2026-11-10", **{"from": "19:00", "to": "21:00"})),
            round_(tool("save_schedule_draft", items=[draft_item()])), round_(report())]


def test_normal_ends_with_real_save_record(ctx):
    result, trace = run(ctx, ScriptedMockLLM(normal_script()))
    assert result["status"] == "completed"
    assert result["draft_save"]["status"] == "created"
    assert not check_invariants(result, trace, ctx.request, ctx.store)
    assert all(s["reason"] and s["next_action"] for s in trace["steps"])
    assert trace["usage"] == {"prompt_tokens": 0, "completion_tokens": 0}


def test_validation_error_is_observed_then_corrected(ctx):
    script = normal_script()
    script.insert(0, round_(tool("save_schedule_draft", items=[draft_item()])))
    result, trace = run(ctx, ScriptedMockLLM(script))
    assert result["status"] == "completed"
    assert trace["steps"][0]["observation"]["error_code"] == "VALIDATION_FAILED"


def test_invalid_json_and_missing_report_items_can_be_repaired(ctx):
    script = normal_script()
    script.insert(0, round_({"name": "get_material", "arguments": "{broken"}))
    script.insert(-1, round_(tool("submit_report", items=[], overall_note="报告不完整")))
    result, trace = run(ctx, ScriptedMockLLM(script))
    assert result["status"] == "completed"
    assert trace["steps"][0]["observation"]["error_code"] == "INVALID_ARGUMENTS"
    assert trace["steps"][-2]["observation"]["error_code"] == "VALIDATION_FAILED"


def test_false_save_claim_is_corrected_after_storage_failure(ctx):
    script = normal_script()
    script.insert(-1, copy.deepcopy(script[-2]))
    script[-1] = round_(report(note="草稿已保存，保存成功"))
    result, trace = run(ctx, ScriptedMockLLM(script), registry=ToolRegistry({"save_schedule_draft": "always"}))
    assert result["status"] == "save_failed" and result["draft_save"]["status"] == "failed"
    assert result["draft_save"]["error_code"] == "STORAGE_UNAVAILABLE"
    assert result["consistency_warnings"] and not ctx.store.path.exists()
    assert not check_invariants(result, trace, ctx.request, ctx.store)


def test_loop_does_not_end_on_plain_text_and_respects_steps(ctx):
    result, trace = run(ctx, ScriptedMockLLM([{"content": "结束"}] * 2), Limits(max_steps=2))
    assert result["status"] == "incomplete" and result["incomplete_reason"] == "MAX_STEPS_REACHED"
    assert result["items"][0]["review_status"] == "unknown"
    assert len(trace["events"]) == 2


def test_multicall_turn_respects_tool_budget(ctx):
    script = [round_(tool("get_material", material_id="M02"), tool("check_rules", material_id="M02", scope="basic"))]
    result, trace = run(ctx, ScriptedMockLLM(script), Limits(max_tool_calls=1))
    assert result["incomplete_reason"] == "MAX_TOOL_CALLS_REACHED" and len(trace["steps"]) == 1


def test_repetition_ignores_reason_wording(ctx):
    calls = [round_(tool("get_material", material_id="M02")) for _ in range(4)]
    calls[-1]["calls"][0]["arguments"]["reason"] = "试图用新措辞绕过重复限制"
    result, trace = run(ctx, ScriptedMockLLM(calls), Limits(max_steps=4))
    assert trace["steps"][-1]["observation"]["error_code"] == "REPEATED_CALL"


def test_mock_exhaustion_is_failed_not_incomplete(ctx):
    result, trace = run(ctx, ScriptedMockLLM([]))
    assert result["status"] == "failed" and "MOCK_SCRIPT_EXHAUSTED" in result["failure_reason"]
    assert not check_invariants(result, trace, ctx.request, ctx.store)


def test_report_cannot_forge_approval_or_slot_without_tool_facts(ctx):
    result, trace = run(ctx, ScriptedMockLLM([round_(report())]))
    assert result["status"] == "failed"
    assert result["items"][0]["review_status"] == "unknown" and result["items"][0]["suggested_slot"] is None
    assert result["consistency_warnings"]


def test_unsafe_report_cannot_override_saved_draft(ctx):
    script = normal_script()
    script[-1] = round_(report(slot="2026-11-10T19:00", confirmation="confirmed"))
    result, trace = run(ctx, ScriptedMockLLM(script))
    assert result["items"][0]["suggested_slot"] == "2026-11-10T20:00"
    assert result["items"][0]["confirmation_status"] == "not_required"
    assert result["consistency_warnings"]


def test_public_trace_filters_publication_claims(ctx):
    script = normal_script()
    script[0]["calls"][0]["arguments"]["reason"] = "已发布"
    script[-1] = round_(report(note="发布成功"))
    result, trace = run(ctx, ScriptedMockLLM(script))
    assert not check_invariants(result, trace, ctx.request, ctx.store)
    assert "已发布" not in json.dumps(trace, ensure_ascii=False)


def test_tool_error_reaches_next_model_turn(ctx):
    class ObservingMock(ScriptedMockLLM):
        def chat(self, messages, tools):
            if self.index == 3:
                obs = json.loads(messages[-1]["content"])
                assert obs["error_code"] == "TOOL_TIMEOUT"
                assert messages[-1]["role"] == "tool" and messages[-1]["tool_call_id"]
            return super().chat(messages, tools)
    script = normal_script()
    script.insert(3, copy.deepcopy(script[2]))
    result, trace = run(ctx, ObservingMock(script), registry=ToolRegistry({"query_slots": "once"}))
    assert result["status"] == "completed"


def test_saved_draft_must_be_updated_after_new_blocking_evidence(ctx):
    ctx.repo.materials["M02"]["subtitles"] = "合成违禁词"
    script = normal_script()
    script.insert(-1, round_(tool("check_rules", material_id="M02", scope="content")))
    script += [round_(tool("save_schedule_draft", items=[draft_item(start=None, review="blocked")])),
               round_(report(review="blocked", slot=None))]
    result, trace = run(ctx, ScriptedMockLLM(script))
    reports = [s for s in trace["steps"] if s["tool"] == "submit_report"]
    assert not reports[0]["ok"] and reports[-1]["ok"]
    draft = ctx.store.read()["drafts"][0]
    assert draft["version"] == 2 and draft["items"][0]["slot"] is None
    assert result["items"][0]["review_status"] == "blocked"
