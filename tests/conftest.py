from pathlib import Path

import pytest

from schedule_agent.context import RunContext
from schedule_agent.store.seed_repo import SeedRepo
from schedule_agent.store.draft_store import DraftStore
from schedule_agent.tools.registry import ToolRegistry


ROOT = Path(__file__).resolve().parents[1]


def requirement(mid="M02", time="2026-11-10T20:00", policy="flexible"):
    return {"material_id": mid, "channel": "douyin", "preferred_time": time,
            "time_policy": policy, "constraints": {"date_fixed": True, "channel_fixed": True, "not_after": "21:00"}}


def draft_item(mid="M02", start="2026-11-10T20:00", review="approved", confirmation="not_required", ids=None):
    return {"material_id": mid, "review_status": review, "risk_reasons": [],
            "slot": {"channel": "douyin", "start": start} if start else None,
            "confirmation_status": confirmation, "confirmation_ids": ids or []}


@pytest.fixture
def ctx(tmp_path):
    return RunContext({"items": [requirement()]}, SeedRepo(ROOT / "data"), DraftStore(tmp_path))


@pytest.fixture
def registry():
    return ToolRegistry()


def call(registry, ctx, name, **args):
    return registry.execute(name, dict(args, reason="验证工具事实"), ctx)


def checked(registry, ctx, mid="M02"):
    call(registry, ctx, "get_material", material_id=mid)
    return call(registry, ctx, "check_rules", material_id=mid, scope="basic")


def confirmation(registry, ctx, mid, kind, proposed=None):
    args = dict(material_id=mid, type=kind, question="是否同意此项处理？", options=["同意", "不同意"])
    if proposed:
        args["proposed_slot"] = proposed
    return call(registry, ctx, "request_confirmation", **args)["data"]["confirmation_id"]
