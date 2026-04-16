"""Reporting helpers for terminal output and report files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .models import DecisionEvaluation, EvaluationSummary, Scenario, ValidationResult
from .utils import format_probability


def create_report_text(
    scenario: Scenario,
    evaluation: EvaluationSummary,
    validation: ValidationResult,
) -> str:
    """Build a human-readable scenario report."""
    lines: List[str] = []
    lines.append(f"Scenario: {scenario.scenario_name}")
    lines.append(f"Description: {scenario.description}")
    lines.append(f"Variables: {scenario.variables}")
    lines.append("")
    lines.append("Top 3 safest starting decisions:")

    for idx, result in enumerate(evaluation.decision_results[:3], start=1):
        lines.extend(_decision_block(idx, result))

    lines.append("")
    lines.append("Validation warnings:")
    if validation.warnings:
        lines.extend([f"- {w}" for w in validation.warnings])
    else:
        lines.append("- None")

    return "\n".join(lines)


def write_report(path: str | Path, report_text: str) -> Path:
    """Write report text to disk."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")
    return report_path


def summarize_evaluation(evaluation: EvaluationSummary) -> str:
    """Return compact console summary."""
    lines = ["Ranked decisions (safest first):"]
    for idx, result in enumerate(evaluation.decision_results, start=1):
        lines.append(
            f"{idx}. {result.decision_label} ({result.decision_node_id}) | "
            f"catastrophic={format_probability(result.catastrophic_probability)} | "
            f"positive={format_probability(result.positive_end_probability)} | "
            f"harm={result.expected_harm:.3f} | score={result.composite_score:.3f}"
        )
    return "\n".join(lines)


def _decision_block(rank: int, result: DecisionEvaluation) -> Iterable[str]:
    lines = [
        f"{rank}. {result.decision_label} ({result.decision_node_id})",
        f"   catastrophic_probability: {result.catastrophic_probability:.4f}",
        f"   positive_end_probability: {result.positive_end_probability:.4f}",
        f"   expected_harm: {result.expected_harm:.4f}",
        f"   uncertainty_penalty: {result.expected_uncertainty_penalty:.4f}",
        f"   reversibility_penalty: {result.expected_reversibility_penalty:.4f}",
        f"   composite_score: {result.composite_score:.4f}",
        f"   interpretation: {result.interpretation}",
        "   top dangerous paths:",
    ]

    for p in result.dangerous_paths[:5]:
        lines.append(
            "   - "
            f"{' -> '.join(p.nodes)} | prob={p.probability:.4f} | "
            f"harm={p.total_harm:.2f} | failure={p.ends_in_failure}"
        )

    lines.append("   top positive paths:")
    for p in result.positive_paths[:5]:
        lines.append(
            "   - "
            f"{' -> '.join(p.nodes)} | prob={p.probability:.4f} | "
            f"harm={p.total_harm:.2f}"
        )
    return lines
