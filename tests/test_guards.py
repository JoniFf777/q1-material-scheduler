import pytest

from schedule_agent.domain.guards import validate
from conftest import requirement, draft_item, call, checked, confirmation


def codes(ctx, items):
    return {v["code"] for v in validate(ctx, items)}


def test_unchecked_and_missing_items(ctx):
    assert "RULE_CHECK_REQUIRED" in codes(ctx, [draft_item()])
    assert "MISSING_ITEMS" in codes(ctx, [])
    assert "MISSING_ITEMS" in codes(ctx, [draft_item(), draft_item()])


def test_changed_slot_requires_registered_pending_confirmation(ctx, registry):
    checked(registry, ctx)
    item = draft_item(start="2026-11-10T19:00")
    assert "CONFIRMATION_REQUIRED" in codes(ctx, [item])
    cid = confirmation(registry, ctx, "M02", "time_change", "2026-11-10T19:00")
    item.update(confirmation_status="pending", confirmation_ids=[cid])
    assert not validate(ctx, [item])


def test_fixed_time_cannot_change_even_if_marked_pending(ctx, registry):
    ctx.request["items"][0]["time_policy"] = "fixed"
    checked(registry, ctx)
    cid = confirmation(registry, ctx, "M02", "time_change", "2026-11-10T19:00")
    assert "HARD_CONSTRAINT_VIOLATION" in codes(ctx, [draft_item(start="2026-11-10T19:00", confirmation="pending", ids=[cid])])


def test_forged_confirmed_and_wrong_slot_user_reply_are_rejected(ctx, registry):
    checked(registry, ctx)
    ctx.confirmations = [{"material_id": "M02", "type": "time_change", "proposed_slot": "2026-11-10T21:00", "status": "confirmed"}]
    cid = confirmation(registry, ctx, "M02", "time_change", "2026-11-10T19:00")
    item = draft_item(start="2026-11-10T19:00", confirmation="confirmed", ids=[cid])
    assert "UNAUTHORIZED_CONFIRMATION" in codes(ctx, [item])


def test_exact_user_confirmation_is_accepted(ctx, registry):
    checked(registry, ctx)
    ctx.confirmations = [{"material_id": "M02", "type": "time_change", "proposed_slot": "2026-11-10T19:00", "status": "confirmed", "user_reply": "同意19点"}]
    cid = confirmation(registry, ctx, "M02", "time_change", "2026-11-10T19:00")
    assert not validate(ctx, [draft_item(start="2026-11-10T19:00", confirmation="confirmed", ids=[cid])])


@pytest.mark.parametrize("review", ["blocked", "need_info", "unknown"])
def test_unready_items_cannot_have_slot(ctx, registry, review):
    checked(registry, ctx)
    assert "BLOCKED_ITEM_HAS_SLOT" in codes(ctx, [draft_item(review=review)])


@pytest.mark.parametrize("start,channel,expected", [
    ("2026-11-10T20:30", "douyin", "INVALID_SLOT"),
    ("2026-11-10T07:00", "douyin", "INVALID_SLOT"),
    ("2026-11-10T22:00", "douyin", "HARD_CONSTRAINT_VIOLATION"),
    ("2026-11-11T20:00", "douyin", "HARD_CONSTRAINT_VIOLATION"),
    ("2026-11-10T20:00", "xiaohongshu", "HARD_CONSTRAINT_VIOLATION"),
    ("bad-time", "douyin", "INVALID_SLOT"),
    ("2026-11-10T18:00", "douyin", "SLOT_CONFLICT"),
])
def test_grid_hard_constraints_and_conflicts(ctx, registry, start, channel, expected):
    checked(registry, ctx)
    item = draft_item(start=start)
    item["slot"]["channel"] = channel
    assert expected in codes(ctx, [item])


def test_risk_cannot_be_bypassed_and_intra_request_slots_conflict(ctx, registry):
    ctx.request["items"].append(requirement("M01"))
    checked(registry, ctx)
    checked(registry, ctx, "M01")
    assert "SLOT_CONFLICT" in codes(ctx, [draft_item(), draft_item("M01")])
    ctx.checked["M02"] = "block"
    assert "RISK_STATUS_MISMATCH" in codes(ctx, [draft_item(), draft_item("M01")])


def test_missing_material_fact_allows_only_unscheduled_need_info(ctx, registry):
    ctx.request["items"] = [requirement("M08")]
    assert "RULE_CHECK_REQUIRED" in codes(ctx, [draft_item("M08", None, "need_info", "pending")])
    assert call(registry, ctx, "get_material", material_id="M08")["error_code"] == "NOT_FOUND"
    cid = confirmation(registry, ctx, "M08", "info_needed")
    assert not validate(ctx, [draft_item("M08", None, "need_info", "pending", [cid])])
    assert "RISK_STATUS_MISMATCH" in codes(ctx, [draft_item("M08")])
