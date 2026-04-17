from pathlib import Path

from app.loader import load_scenario
from app.models import Edge, Node, Scenario, Scoring
from app.validator import validate_scenario


def test_validator_rejects_malformed_scenario() -> None:
    scenario = Scenario(
        scenario_name="bad",
        description="",
        variables={"x": True},
        scoring=Scoring(),
        nodes=[
            Node(id="d1", label="D", type="decision"),
            Node(id="d1", label="Dup", type="decision"),
        ],
        edges=[
            Edge(
                id="e1",
                from_node="d1",
                to_node="missing",
                probability=1.5,
                transition_kind="fork",
            )
        ],
    )
    result = validate_scenario(scenario)
    assert not result.is_valid
    assert any("Duplicate node id" in e for e in result.errors)
    assert any("unknown target node" in e for e in result.errors)
    assert any("invalid probability" in e for e in result.errors)


def test_strict_validation_rejects_incomplete_edge() -> None:
    scenario = load_scenario(Path("scenarios/draft_example.json"))
    result = validate_scenario(scenario, mode="strict")
    assert any("Incomplete edge" in e for e in result.errors)


def test_draft_validation_warns_on_incomplete_edge() -> None:
    scenario = load_scenario(Path("scenarios/draft_example.json"))
    result = validate_scenario(scenario, mode="draft")
    assert result.is_valid
    assert any("Incomplete edge" in w for w in result.draft_warnings)
