from pathlib import Path

from app.loader import load_scenario


def test_loader_loads_valid_scenario() -> None:
    scenario = load_scenario(Path("scenarios/example_scenario.json"))
    assert scenario.scenario_name == "example_scenario"
    assert len(scenario.nodes) >= 2
    assert len(scenario.edges) >= 2
