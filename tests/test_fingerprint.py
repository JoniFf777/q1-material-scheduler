import copy

from schedule_agent.domain.fingerprint import request_key
from conftest import requirement


def test_request_identity_ignores_note_confirmations_and_order():
    a = {"items": [requirement("M01"), requirement("M02")], "note": "首次"}
    b = copy.deepcopy(a)
    b.update(items=list(reversed(b["items"])), note="不同措辞", confirmations=[{"status": "confirmed"}])
    assert request_key(a) == request_key(b)
    b["items"][0]["preferred_time"] = "2026-11-10T21:00"
    assert request_key(a) != request_key(b)


def test_pending_defaults_are_part_of_request_identity():
    a = {"scope": "pending", "defaults": {"channel": "douyin", "preferred_time": "2026-11-10T20:00"}}
    b = copy.deepcopy(a)
    b["defaults"]["channel"] = "xiaohongshu"
    assert request_key(a) != request_key(b)
