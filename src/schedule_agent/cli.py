import argparse
import sys

from .render import render_result
from .service import execute, load_input


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
    args = parser.parse_args()
    try:
        scenario = load_input(args.input)
        suffix = ".mock" if args.llm == "mock" else ""
        prefix = args.out or f"runtime/outputs/{scenario['name']}{suffix}"
        result, trace, ctx = execute(scenario, args.llm, args.state_dir, args.data_dir,
            out=prefix, input_file=args.input, mock_script=args.mock_script)
        print(render_result(result))
        print(f"结果与 Trace：{prefix}.*")
        if result["invariant_errors"]:
            return 1
        return 0 if result["status"] in ("completed", "completed_with_pending") else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"输入、配置或本地数据不可用：{type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
