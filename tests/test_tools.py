import copy

from schedule_agent.context import RunContext
from schedule_agent.tools.registry import ToolRegistry
from conftest import call, checked, confirmation, draft_item, requirement


def test_seven_tools_have_reason_and_invalid_calls_return_observation(ctx, registry):
    assert len(registry.schemas()) == 7
    assert all("reason" in s["function"]["parameters"]["required"] for s in registry.schemas())
    assert registry.execute("get_material", '{broken', ctx)["error_code"] == "INVALID_ARGUMENTS"
    assert registry.execute("get_material", {"material_id": "M02"}, ctx)["error_code"] == "INVALID_ARGUMENTS"
    assert call(registry, ctx, "publish")["error_code"] == "INVALID_ARGUMENTS"
    assert call(registry, ctx, "get_material", material_id="M02", reason_extra="x")["error_code"] == "INVALID_ARGUMENTS"


def test_missing_info_full_view_and_recheck(ctx, registry):
    ctx.request["items"] = [requirement("M03")]
    first = checked(registry, ctx, "M03")["data"]
    assert first["verdict"] == "need_info" and len(first["findings"]) == 3
    call(registry, ctx, "get_material", material_id="M03", detail="full")
    final = call(registry, ctx, "check_rules", material_id="M03", scope="basic")["data"]
    assert final["verdict"] == "need_info" and len(final["findings"]) == 2


def test_license_lookup_diverges_and_full_read_keeps_evidence(ctx, registry):
    ctx.request["items"] = [requirement("M04"), requirement("M07")]
    for mid, verdict in (("M04", "block"), ("M07", "pass")):
        assert checked(registry, ctx, mid)["data"]["verdict"] == "uncertain"
        assert call(registry, ctx, "check_rules", material_id=mid, scope="license")["data"]["verdict"] == verdict
        call(registry, ctx, "get_material", material_id=mid, detail="full")
        assert call(registry, ctx, "check_rules", material_id=mid, scope="basic")["data"]["verdict"] == verdict


def test_own_hold_available_but_schedule_occupancy_takes_priority(ctx, registry):
    checked(registry, ctx)
    assert call(registry, ctx, "save_schedule_draft", items=[draft_item()])["data"]["result"] == "created"
    query = dict(channel="douyin", date="2026-11-10", **{"from": "20:00", "to": "20:00"})
    assert call(registry, ctx, "query_slots", **query)["data"]["slots"][0]["status"] == "held_by_this_request"
    assert call(registry, ctx, "save_schedule_draft", items=[draft_item()])["data"]["result"] == "duplicate"
    ctx.repo.schedule.append({"channel": "douyin", "start": "2026-11-10T20:00", "material_id": "M90"})
    assert call(registry, ctx, "query_slots", **query)["data"]["slots"][0]["status"] == "occupied"
    assert call(registry, ctx, "save_schedule_draft", items=[draft_item()])["error_code"] == "VALIDATION_FAILED"


def test_other_requests_drafts_are_conflicts(ctx, registry):
    checked(registry, ctx)
    call(registry, ctx, "save_schedule_draft", items=[draft_item()])
    other = RunContext({"items": [requirement("M01")]}, ctx.repo, ctx.store)
    checked(registry, other, "M01")
    obs = call(registry, other, "save_schedule_draft", items=[draft_item("M01")])
    assert any(v["code"] == "SLOT_CONFLICT" for v in obs["violations"])


def test_fault_once_recovers_and_save_failure_leaves_file_unchanged(ctx, registry):
    checked(registry, ctx)
    call(registry, ctx, "save_schedule_draft", items=[draft_item()])
    before = ctx.store.path.read_bytes()
    failing = ToolRegistry({"save_schedule_draft": "always", "query_slots": "once"})
    obs = call(failing, ctx, "save_schedule_draft", items=[draft_item()])
    assert obs["error_code"] == "STORAGE_UNAVAILABLE" and ctx.save_observation == obs
    assert ctx.store.path.read_bytes() == before
    args = dict(channel="douyin", date="2026-11-10", **{"from": "19:00", "to": "21:00"})
    assert call(failing, ctx, "query_slots", **args)["error_code"] == "TOOL_TIMEOUT"
    assert call(failing, ctx, "query_slots", **args)["ok"]


def test_deep_content_checks_do_not_erase_other_findings(ctx, registry):
    ctx.repo.materials["M02"]["subtitles"] = "这里出现合成违禁词"
    assert checked(registry, ctx)["data"]["verdict"] == "pass"
    assert call(registry, ctx, "check_rules", material_id="M02", scope="content")["data"]["verdict"] == "block"
    assert call(registry, ctx, "check_rules", material_id="M02", scope="basic")["data"]["verdict"] == "block"
