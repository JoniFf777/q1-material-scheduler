import copy
import json
import sys

import pytest

from schedule_agent.cli import main
from schedule_agent.input import validate_scenario
from schedule_agent.service import load_input
from schedule_agent.domain.models import Limits
from conftest import ROOT


def invoke(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["schedule-agent", *map(str, args)])
    return main()


def test_cli_run_inspect_and_reset_preserves_other_files(tmp_path, monkeypatch, capsys):
    state, out = tmp_path / "state", tmp_path / "result"
    assert invoke(monkeypatch, "run", "--input", ROOT / "examples/inputs/S01_normal.json", "--state-dir", state,
        "--data-dir", ROOT / "data", "--mock-script", ROOT / "tests/fixtures/mock_scripts/S01_normal.json", "--out", out) == 0
    stored = json.loads((state / "drafts.json").read_text(encoding="utf-8"))
    did = stored["drafts"][0]["draft_id"]
    assert invoke(monkeypatch, "drafts", "list", "--state-dir", state) == 0
    assert invoke(monkeypatch, "drafts", "show", did, "--state-dir", state) == 0
    assert did in capsys.readouterr().out
    sentinel = state / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    assert invoke(monkeypatch, "reset", "--state-dir", state) == 0
    assert sentinel.exists() and not (state / "drafts.json").exists()


def test_cli_limit_override_and_invalid_fault(tmp_path, monkeypatch):
    base = ("run", "--input", ROOT / "examples/inputs/S01_normal.json", "--state-dir", tmp_path / "state", "--out", tmp_path / "limit")
    assert invoke(monkeypatch, *base, "--max-steps", "1") == 1
    result = json.loads((tmp_path / "limit.result.json").read_text(encoding="utf-8"))
    assert result["incomplete_reason"] == "MAX_STEPS_REACHED"
    assert invoke(monkeypatch, *base, "--fault", "query_slots=unsupported") == 2


@pytest.mark.parametrize("change", [
    lambda s: s.update(name="../../outside"),
    lambda s: s["request"]["items"].append(copy.deepcopy(s["request"]["items"][0])),
    lambda s: s["request"]["items"][0].update(preferred_time="2026-02-30T20:00"),
    lambda s: s["request"]["items"][0].update(time_policy="whatever"),
    lambda s: s["request"]["items"][0].update(constraints={"date_fixed": "false"}),
    lambda s: s["request"].update(scope="unsupported"),
    lambda s: s.update(confirmations=[{"material_id":"M02", "type":"time_change", "status":"confirmed"}]),
])
def test_invalid_input_rejected_before_execution(change):
    scenario = load_input(ROOT / "examples/inputs/S01_normal.json")
    change(scenario)
    with pytest.raises((ValueError, TypeError)):
        validate_scenario(scenario)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "4"])
def test_limits_require_positive_integers(value):
    with pytest.raises(ValueError):
        Limits(max_steps=value)
