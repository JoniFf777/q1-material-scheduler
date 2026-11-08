import argparse
import sys

from .render import render_result
from .service import execute, load_input
from .store.draft_store import DraftStore
from .tools.registry import DEFINITIONS
from .config import ConfigurationError


def main():
    parser = argparse.ArgumentParser(description="素材审核与排期草稿（未执行发布）")
    commands = parser.add_subparsers(dest="command", required=True)
    runner = commands.add_parser("run", help="生成排期草稿")
    runner.add_argument("--input", required=True)
    runner.add_argument("--llm", choices=("mock", "live"), default="mock")
    runner.add_argument("--state-dir", default="runtime/default")
    runner.add_argument("--data-dir", default="data")
    runner.add_argument("--out", help="输出文件前缀")
    runner.add_argument("--mock-script", help="显式指定固定 Mock 脚本")
    runner.add_argument("--max-steps", type=int)
    runner.add_argument("--max-tool-calls", type=int)
    runner.add_argument("--fault", action="append", default=[], metavar="TOOL=once|always")
    drafts = commands.add_parser("drafts", help="检查本地草稿")
    draft_commands = drafts.add_subparsers(dest="draft_command", required=True)
    listing = draft_commands.add_parser("list")
    listing.add_argument("--state-dir", default="runtime/default")
    show = draft_commands.add_parser("show")
    show.add_argument("draft_id")
    show.add_argument("--state-dir", default="runtime/default")
    reset = commands.add_parser("reset", help="仅删除指定状态目录的 drafts.json")
    reset.add_argument("--state-dir", default="runtime/default")
    args = parser.parse_args()
    try:
        if args.command in ("drafts", "reset"):
            import json
            store = DraftStore(args.state_dir)
            if args.command == "reset":
                store.reset()
                print("已清空指定状态目录的草稿文件")
                return 0
            records = store.read()["drafts"]
            if args.draft_command == "show":
                record = next((d for d in records if d["draft_id"] == args.draft_id), None)
                if record is None:
                    print("未找到草稿", file=sys.stderr)
                    return 1
                print(json.dumps(record, ensure_ascii=False, indent=2))
            else:
                for draft in records:
                    print(f"{draft['draft_id']} | v{draft['version']} | 条目 {len(draft['items'])} | 待确认 {len(draft['pending_confirmations'])}")
                print(f"草稿总数：{len(records)}")
            return 0
        faults = {}
        for value in args.fault:
            name, separator, mode = value.partition("=")
            if not separator or name not in DEFINITIONS or mode not in ("once", "always"):
                raise ValueError("故障必须为已知工具=once|always")
            faults[name] = mode
        scenario = load_input(args.input)
        suffix = ".mock" if args.llm == "mock" else ""
        prefix = args.out or f"runtime/outputs/{scenario['name']}{suffix}"
        result, trace, ctx = execute(scenario, args.llm, args.state_dir, args.data_dir,
            out=prefix, input_file=args.input, mock_script=args.mock_script,
            limits={"max_steps": args.max_steps, "max_tool_calls": args.max_tool_calls}, faults=faults)
        print(render_result(result))
        print(f"结果与 Trace：{prefix}.*")
        if result["invariant_errors"]:
            return 1
        return 0 if result["status"] in ("completed", "completed_with_pending") else 1
    except ConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"输入、配置或本地数据不可用：{type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
