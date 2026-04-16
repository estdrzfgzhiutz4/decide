"""Command-line interface for risk graph app."""

from __future__ import annotations

import argparse
from pathlib import Path

from .evaluator import evaluate_scenario
from .loader import load_scenario
from .reports import create_report_text, summarize_evaluation, write_report
from .validator import validate_scenario


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI parser."""
    parser = argparse.ArgumentParser(description="Risk Graph App CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("validate", "evaluate", "report"):
        p = sub.add_parser(name)
        p.add_argument("scenario")

    r = sub.add_parser("render")
    r.add_argument("scenario")
    r.add_argument("--format", choices=["svg", "png"], default="svg")
    r.add_argument("--output-dir", default="output")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = build_parser().parse_args(argv)
    scenario = load_scenario(args.scenario)
    validation = validate_scenario(scenario)

    if args.command == "validate":
        if validation.errors:
            print("Validation errors:")
            for e in validation.errors:
                print(f"- {e}")
            return 1
        print("Scenario is valid.")
        if validation.warnings:
            print("Warnings:")
            for w in validation.warnings:
                print(f"- {w}")
        return 0

    if validation.errors:
        print("Cannot continue; scenario validation failed:")
        for e in validation.errors:
            print(f"- {e}")
        return 1

    if args.command == "evaluate":
        summary = evaluate_scenario(scenario)
        print(summarize_evaluation(summary))
        return 0

    if args.command == "render":
        from .renderer import render_scenario

        summary = evaluate_scenario(scenario)
        rendered = render_scenario(
            scenario,
            output_dir=args.output_dir,
            fmt=args.format,
            evaluation=summary,
        )
        print(f"Rendered: {rendered}")
        return 0

    if args.command == "report":
        summary = evaluate_scenario(scenario)
        text = create_report_text(scenario, summary, validation)
        out = write_report(Path("output") / "report.txt", text)
        print(summarize_evaluation(summary))
        print(f"Report written to: {out}")
        return 0

    return 1
