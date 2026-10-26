"""命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from linalg_agent.agent import LinalgAgent
from linalg_agent.config import ConfigError
from linalg_agent.llm import LinalgAgentError
from linalg_agent.method import parse_method
from linalg_agent.pipelines import PipelineResult


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (ConfigError, LinalgAgentError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linalg-agent",
        description="线性代数 agent：按指定写法求解，或把一种解法翻译成另一种并沿用原取法。",
    )
    parser.add_argument("--reasoning", action="store_true", help="在答案后附上模型的思考过程")
    parser.add_argument("--usage", action="store_true", help="在标准错误中打印 token 用量")
    sub = parser.add_subparsers(dest="command", required=True)

    solve = sub.add_parser("solve", help="只根据题目求解")
    solve.add_argument("problem", nargs="?", help="题目文本")
    solve.add_argument("-f", "--file", help="从文件读取题目，- 表示标准输入")
    solve.add_argument(
        "--method",
        default="free",
        choices=["free", "matrix", "space"],
        help="free 自选一种写法；matrix 或 space 指定写法",
    )
    solve.set_defaults(handler=run_solve)

    alternate = sub.add_parser("alternate", help="把已有解法翻译成另一种")
    alternate.add_argument(
        "--given",
        required=True,
        choices=["matrix", "space"],
        help="已有解法是矩阵解法 matrix，或线性空间解法 space",
    )
    alternate.add_argument("-p", "--problem", help="题目文本")
    alternate.add_argument("--problem-file", help="从文件读取题目")
    alternate.add_argument("-s", "--solution", help="已有解法文本")
    alternate.add_argument(
        "-f",
        "--file",
        help="从文件读取已有解法，- 表示标准输入",
    )
    alternate.set_defaults(handler=run_alternate)
    return parser


def run_solve(args: argparse.Namespace) -> int:
    problem = _one_of(
        args.problem,
        _read_optional(args.file),
        label="题目",
    )
    agent = LinalgAgent.from_env()
    print(_solve_status(args.method), file=sys.stderr, flush=True)
    result = agent.solve(problem, method=args.method)
    _emit(result, args)
    return 0


def run_alternate(args: argparse.Namespace) -> int:
    problem = args.problem
    if args.problem_file:
        if problem:
            raise ValueError("题目请只通过 --problem 或 --problem-file 提供一次。")
        problem = _read_text(args.problem_file)
    solution = _one_of(
        args.solution,
        _read_optional(args.file),
        label="已有解法",
    )
    given = parse_method(args.given)
    if given is None:
        raise ValueError("翻译时必须用 --given 标明 matrix 或 space。")
    if not problem:
        raise ValueError("翻译时必须用 --problem 或 --problem-file 提供题目。")
    agent = LinalgAgent.from_env()
    target = "线性空间解法" if args.given == "matrix" else "矩阵解法"
    print(f"正在把已有解法翻译成{target}…", file=sys.stderr, flush=True)
    result = agent.alternate(
        solution,
        problem=problem,
        given_method=given,
    )
    _emit(result, args)
    return 0


def _solve_status(method: str) -> str:
    if method == "matrix":
        return "正在按矩阵解法求解…"
    if method == "space":
        return "正在按线性空间解法求解…"
    return "正在求解，写法由模型自选…"


def _emit(result: PipelineResult, args: argparse.Namespace) -> None:
    print(result.content)
    if args.reasoning and result.reasoning:
        print("\n## 思考过程\n")
        print(result.reasoning)
    if args.usage and result.usage:
        usage = result.usage
        print(
            "tokens："
            f"输入 {usage['prompt_tokens']}，"
            f"输出 {usage['completion_tokens']}，"
            f"合计 {usage['total_tokens']}（{result.model}）",
            file=sys.stderr,
        )


def _one_of(text: str | None, from_file: str | None, *, label: str) -> str:
    if text and from_file:
        raise ValueError(f"{label}请只通过参数或文件提供一次。")
    value = (text or from_file or "").strip()
    if not value:
        raise ValueError(f"请提供{label}。")
    return value


def _read_optional(path: str | None) -> str | None:
    if path is None:
        return None
    return _read_text(path)


def _read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8-sig")


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
