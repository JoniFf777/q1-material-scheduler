"""Run scenarios from repository root; all model runs are explicitly mode-labelled."""
import argparse
import json
import uuid
from pathlib import Path

from schedule_agent.evaluation import evaluate
from schedule_agent.service import execute, load_input
from schedule_agent.store.draft_store import DraftStore
from schedule_agent.config import ModelConfig, ConfigurationError


ROOT = Path(__file__).resolve().parents[1]
ORDER = ["S01_normal", "S02_missing_info", "S03_rule_risk", "S04_slot_conflict",
         "S05_hard_conflict", "S06_duplicate", "S06b_slot_changed", "S07_save_failure",
         "S08_tool_retry", "S09_step_limit", "S10_confirm_round2"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="场景验证：Mock 仅证明流程；Live 需要真实 Key")
    parser.add_argument("--llm", choices=("mock", "live"), default="mock")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--only", nargs="+", choices=ORDER)
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--state-dir", default=str(ROOT / "runtime" / "scenarios"))
    parser.add_argument("--out-dir", default=str(ROOT / "examples"))
    args = parser.parse_args(argv)
    if args.repeat < 1:
        parser.error("--repeat 必须为正数")
    if args.llm == "live":
        try:
            ModelConfig.from_env()
        except ConfigurationError as exc:
            parser.error(str(exc))
    batch = "batch-" + uuid.uuid4().hex[:12]
    output_dir = Path(args.out_dir)
    selected = set(args.only or ORDER)
    plan = set(selected)
    if plan & {"S06_duplicate", "S06b_slot_changed"}:
        plan.add("S04_slot_conflict")
    if "S06b_slot_changed" in plan:
        plan.add("S06_duplicate")
    rows = []
    failed = False
    for iteration in range(1, args.repeat + 1):
        base = Path(args.state_dir) / args.llm / batch / f"repeat-{iteration}"
        reset = set()
        for name in ORDER:
            if name not in plan:
                continue
            scenario = load_input(ROOT / "examples" / "inputs" / (name + ".json"))
            state_name = "conflict-sequence" if name in ("S04_slot_conflict", "S06_duplicate", "S06b_slot_changed") else name
            state = base / state_name
            if state_name not in reset:
                DraftStore(state).reset()
                reset.add(state_name)
            suffix = ".mock" if args.llm == "mock" else ""
            prefix = output_dir / args.llm / (name + suffix) if iteration == 1 else None
            try:
                if name == "S10_confirm_round2":
                    initial = load_input(ROOT / "examples/inputs/S04_slot_conflict.json")
                    seed_result, _, _ = execute(initial, args.llm, state, args.data_dir,
                        mock_script=ROOT / "tests/fixtures/mock_scripts/S04_slot_conflict.json",
                        out=base / "S10_precondition" if iteration == 1 else None)
                    if seed_result["draft_save"]["status"] != "created":
                        raise ValueError("S10 前置 S04 未成功创建草稿")
                before = DraftStore(state).read()
                result, trace, ctx = execute(scenario, args.llm, state, args.data_dir,
                    out=prefix, input_file=ROOT / "examples/inputs" / (name + ".json"),
                    mock_script=ROOT / "tests/fixtures/mock_scripts" / (name + ".json"))
                errors = evaluate(scenario, result, trace, ctx)
                if name == "S07_save_failure" and ctx.store.read() != before:
                    errors.append("保存失败改变了草稿文件")
                if name in ("S06_duplicate", "S06b_slot_changed"):
                    after = ctx.store.read()["drafts"]
                    if not before["drafts"] or not after or before["drafts"][0]["draft_id"] != after[0]["draft_id"]:
                        errors.append("重复提交更换了 draft_id")
                row = {"scenario": name, "iteration": iteration, "passed": not errors,
                       "prerequisite": name not in selected, "errors": errors,
                       "steps": len(trace["model_calls"]), "tool_calls": len(trace["steps"]),
                       "tokens": sum(trace["usage"].values()), "mode": args.llm,
                       "state_dir": str(state), "draft_id": result["draft_save"].get("draft_id"),
                       "draft_result": result["draft_save"]["status"]}
            except (OSError, ValueError, KeyError, TypeError) as exc:
                row = {"scenario": name, "iteration": iteration, "passed": False,
                       "prerequisite": name not in selected, "errors": ["执行失败：" + type(exc).__name__],
                       "steps": 0, "tool_calls": 0, "tokens": 0, "mode": args.llm}
            rows.append(row)
            failed |= not row["passed"]
            print(f"{name} #{iteration}: {'PASS' if row['passed'] else 'FAIL'}" +
                  (" — " + "; ".join(row["errors"]) if row["errors"] else ""), flush=True)
    results = output_dir / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{args.llm}_summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# {args.llm} 场景结果", ""]
    if args.llm == "mock":
        lines += ["固定脚本离线验证，不能证明真实模型决策能力或稳定性。", ""]
    lines += ["| 场景 | 第几次 | 通过 | 失败原因 | 步数 | 工具次数 | tokens |", "|---|---|---|---|---|---|---|"]
    for row in rows:
        reason = "; ".join(row["errors"]).replace("|", "\\|").replace("\n", " ") or "—"
        name = row["scenario"] + ("（前置）" if row["prerequisite"] else "")
        lines.append(f"| {name} | {row['iteration']} | {'PASS' if row['passed'] else 'FAIL'} | {reason} | {row['steps']} | {row['tool_calls']} | {row['tokens']} |")
    (results / f"{args.llm}_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
