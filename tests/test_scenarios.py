import json
from pathlib import Path
import subprocess
import sys

import pytest

from schedule_agent.evaluation import evaluate
from schedule_agent.service import execute, load_input
from conftest import ROOT


NAMES = [p.stem for p in sorted((ROOT / "examples/inputs").glob("S*.json"))]


@pytest.mark.parametrize("name", NAMES)
def test_each_scenario_matches_expectations_and_invariants(name, tmp_path):
    def execute_name(selected):
        scenario = load_input(ROOT / "examples/inputs" / (selected + ".json"))
        result, trace, ctx = execute(scenario, "mock", tmp_path / "state", ROOT / "data",
            mock_script=ROOT / "tests/fixtures/mock_scripts" / (selected + ".json"))
        return scenario, result, trace, ctx
    if name in ("S06_duplicate", "S06b_slot_changed", "S10_confirm_round2"):
        _, first, _, _ = execute_name("S04_slot_conflict")
        assert first["draft_save"]["status"] == "created"
    if name == "S06b_slot_changed":
        _, second, _, _ = execute_name("S06_duplicate")
        assert second["draft_save"]["status"] == "duplicate"
    scenario, result, trace, ctx = execute_name(name)
    assert not evaluate(scenario, result, trace, ctx)
    if name in ("S06_duplicate", "S06b_slot_changed", "S10_confirm_round2"):
        assert first["draft_save"]["draft_id"] == result["draft_save"]["draft_id"]


def test_runner_prepares_chain_and_keeps_repeated_outputs_in_summary(tmp_path):
    out = tmp_path / "outputs"
    process = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/run_scenarios.py"),
        "--llm", "mock", "--only", "S06b_slot_changed", "--repeat", "2", "--state-dir", str(tmp_path / "states"),
        "--out-dir", str(out)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert process.returncode == 0, process.stdout + process.stderr
    rows = json.loads((out / "results/mock_summary.json").read_text(encoding="utf-8"))
    assert len(rows) == 6 and all(row["passed"] for row in rows)
    assert len(list((out / "mock").glob("*.result.json"))) == 3
    ids = [row["draft_id"] for row in rows]
    assert len(set(ids)) == 1
