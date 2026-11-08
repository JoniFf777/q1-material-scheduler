import copy
import json

import pytest

from schedule_agent.store.draft_store import DraftStore
from conftest import draft_item


def test_created_duplicate_update_and_history(tmp_path):
    store = DraftStore(tmp_path)
    items = [draft_item()]
    first = store.save("RQ-demo", items, [], "run-1")
    before = store.path.read_bytes()
    second = store.save("RQ-demo", items, [], "run-2")
    assert first["result"] == "created" and second["result"] == "duplicate"
    assert first["draft_id"] == second["draft_id"]
    assert store.path.read_bytes() == before
    items[0]["slot"]["start"] = "2026-11-10T21:00"
    third = store.save("RQ-demo", items, [], "run-3")
    assert third["result"] == "updated" and third["version"] == 2
    assert len(store.read()["drafts"]) == 1
    assert len(store.read()["drafts"][0]["history"]) == 2


def test_atomic_replace_failure_keeps_original_file(tmp_path, monkeypatch):
    store = DraftStore(tmp_path)
    store.save("RQ-demo", [draft_item()], [], "run-1")
    before = store.path.read_bytes()
    def fail(*args):
        raise OSError("injected disk failure")
    monkeypatch.setattr("schedule_agent.store.draft_store.os.replace", fail)
    with pytest.raises(OSError):
        store.save("RQ-other", [draft_item()], [], "run-2")
    assert store.path.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


def test_semantic_duplicate_survives_wording_and_confirmation_order(tmp_path):
    store = DraftStore(tmp_path)
    items = [draft_item(ids=["C-b", "C-a"])]
    pending = [{"id": "C-a", "material_id": "M02", "type": "risk_ack", "question": "请确认风险", "options": ["是", "否"]}]
    store.save("RQ-demo", items, pending, "run-1")
    other = copy.deepcopy(items)
    other[0]["confirmation_ids"].reverse()
    pending[0]["question"] = "是否接受该风险？"
    assert store.save("RQ-demo", other, pending, "run-2")["result"] == "duplicate"


def test_corrupt_store_is_never_silently_overwritten(tmp_path):
    store = DraftStore(tmp_path)
    store.path.write_text("{broken", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        store.save("RQ-demo", [], [], "run-1")
    assert store.path.read_text(encoding="utf-8") == "{broken"
