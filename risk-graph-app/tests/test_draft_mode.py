from pathlib import Path

from app.evaluator import evaluate_scenario
from app.loader import load_scenario
from app.reports import create_report_text
from app.validator import validate_scenario


def test_draft_json_with_incomplete_edges_loads() -> None:
    scenario = load_scenario(Path("scenarios/draft_example.json"))
    assert scenario.mode == "draft"
    assert any(e.probability is None for e in scenario.edges)


def test_report_mentions_skipped_and_incomplete_items() -> None:
    scenario = load_scenario(Path("scenarios/draft_example.json"))
    validation = validate_scenario(scenario, mode="draft")
    evaluation = evaluate_scenario(scenario)
    text = create_report_text(scenario, evaluation, validation)
    assert "Skipped incomplete edges" in text
    assert "Ranking is partial" in text
