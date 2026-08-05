"""MinuteFlow command-line interface."""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from minuteflow import __version__
from minuteflow.agents.backend import OpenAIAgentsBackend
from minuteflow.config import Settings
from minuteflow.exceptions import MinuteFlowError
from minuteflow.orchestration import MinuteFlowPipeline
from minuteflow.renderers import render_json, render_markdown


def _meeting_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("meeting date must use YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minuteflow",
        description="Recover decisions and actions from meeting notes with source evidence.",
    )
    parser.add_argument("input", help="Path to Markdown/text notes, or - for standard input.")
    parser.add_argument("--meeting-date", type=_meeting_date, help="Meeting date in YYYY-MM-DD.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path, help="Write the report to this path.")
    parser.add_argument("--model", help="Override MINUTEFLOW_MODEL for this run.")
    parser.add_argument(
        "--enable-tracing",
        action="store_true",
        help="Opt in to OpenAI Agents SDK trace export; traces may contain note content.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise MinuteFlowError(f"Could not read {path!r}: {exc}") from exc


async def _run(args: argparse.Namespace) -> tuple[str, int]:
    settings = Settings.from_env(
        model_override=args.model,
        enable_tracing_override=True if args.enable_tracing else None,
    )
    backend = OpenAIAgentsBackend(settings)
    pipeline = MinuteFlowPipeline(backend, max_input_chars=settings.max_input_chars)
    report = await pipeline.run(_read_input(args.input), meeting_date=args.meeting_date)
    rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
    return rendered, 2 if report.errors else 0


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        rendered, exit_code = asyncio.run(_run(args))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return exit_code
    except MinuteFlowError as exc:
        print(f"minuteflow: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("minuteflow: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
