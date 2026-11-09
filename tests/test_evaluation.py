from schedule_agent.agent import run
from schedule_agent.checks import check_invariants
from schedule_agent.context import RunContext
from schedule_agent.domain.models import Limits
from schedule_agent.evaluation import evaluate
from schedule_agent.llm.mock import ScriptedMockLLM
from schedule_agent.service import load_input
from schedule_agent.store.draft_store import DraftStore
from schedule_agent.store.seed_repo import SeedRepo
from conftest import ROOT


def action(name, **arguments):
    return {"name": name, "arguments": dict(arguments, reason="验证批量调用时的限额评估")}


def test_step_limit_keeps_reviews_completed_by_batched_model_calls(tmp_path):
    scenario = load_input(ROOT / "examples/inputs/S09_step_limit.json")
    ctx = RunContext(scenario["request"], SeedRepo(ROOT / "data"), DraftStore(tmp_path))
    mids = [item["material_id"] for item in ctx.items]
    script = [
        {"calls": [action("get_material", material_id=mid) for mid in mids]},
        {"calls": [action("check_rules", material_id=mid, scope="basic") for mid in mids]},
        {"calls": [action("check_rules", material_id=mid, scope="license") for mid in ("M04", "M07")]},
        {"calls": [action("query_slots", channel="douyin", date="2026-11-10", **{"from": "19:00", "to": "21:00"})]},
    ]
    result, trace = run(ctx, ScriptedMockLLM(script), Limits(max_steps=4))
    result["invariant_errors"] = check_invariants(result, trace, ctx.request, ctx.store)
    assert result["status"] == "incomplete" and result["draft_save"]["status"] == "not_saved"
    assert next(i for i in result["items"] if i["material_id"] == "M07")["review_status"] == "approved"
    assert not evaluate(scenario, result, trace, ctx)


def test_step_limit_evaluation_rejects_approval_without_a_rule_check(tmp_path):
    scenario = load_input(ROOT / "examples/inputs/S09_step_limit.json")
    ctx = RunContext(scenario["request"], SeedRepo(ROOT / "data"), DraftStore(tmp_path))
    script = [{"calls": [action("get_material", material_id=item["material_id"])]} for item in ctx.items]
    result, trace = run(ctx, ScriptedMockLLM(script), Limits(max_steps=4))
    result["invariant_errors"] = check_invariants(result, trace, ctx.request, ctx.store)
    next(i for i in result["items"] if i["material_id"] == "M07")["review_status"] = "approved"
    errors = evaluate(scenario, result, trace, ctx)
    assert any("M07" in message for message in errors)
