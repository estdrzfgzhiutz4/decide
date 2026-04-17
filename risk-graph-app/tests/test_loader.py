from pathlib import Path

from app.loader import load_scenario


def test_loader_loads_valid_scenario() -> None:
    scenario = load_scenario(Path("scenarios/example_scenario.json"))
    assert scenario.scenario_name == "example_scenario"
    assert scenario.mode == "strict"
    assert len(scenario.nodes) >= 2
    assert len(scenario.edges) >= 2


def test_loader_backward_compat_old_strict_json() -> None:
    scenario = load_scenario(Path("scenarios/example_parallel_fork_scenario.json"))
    assert scenario.mode == "strict"
    assert all(hasattr(n, "draft_status") for n in scenario.nodes)
