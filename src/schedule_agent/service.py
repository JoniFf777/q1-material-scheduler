import json
from pathlib import Path

from .agent import run
from .checks import check_invariants
from .config import ModelConfig
from .context import RunContext
from .domain.models import Limits
from .llm.mock import ScriptedMockLLM
from .llm.openai_compat import OpenAICompatClient
from .store.draft_store import DraftStore
from .store.seed_repo import SeedRepo
from .tools.registry import ToolRegistry
from .trace import write_artifacts


def execute(scenario, mode="mock", state_dir="runtime/default", data_dir="data",
            out=None, input_file=None, limits=None, faults=None, mock_script=None):
    setup = scenario.get("setup", {})
    repo = SeedRepo(data_dir, setup.get("schedule_patch"))
    store = DraftStore(state_dir)
    ctx = RunContext(scenario["request"], repo, store, scenario.get("confirmations", []))
    settings = dict(setup.get("limits", {}))
    settings.update({k: v for k, v in (limits or {}).items() if v is not None})
    run_limits = Limits(**settings)
    run_faults = dict(setup.get("faults", {}), **(faults or {}))
    if mode == "live":
        llm = OpenAICompatClient(ModelConfig.from_env())
    elif mode == "mock":
        name = scenario.get("name", "")
        if not name or Path(name).name != name:
            raise ValueError("Mock 场景名称必须是不带路径的文件名")
        script = mock_script or Path("tests/fixtures/mock_scripts") / (name + ".json")
        llm = ScriptedMockLLM(script)
    else:
        raise ValueError("llm 必须为 live 或 mock")
    result, trace = run(ctx, llm, run_limits, ToolRegistry(run_faults), input_file,
                        today=scenario.get("today", "2026-11-08"))
    errors = check_invariants(result, trace, ctx.request, store, ctx.confirmations)
    result["invariant_errors"] = errors
    if out:
        write_artifacts(out, result, trace)
    return result, trace, ctx


def load_input(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))
