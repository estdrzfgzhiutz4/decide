from pathlib import Path

from app.evaluator import TraversalConfig, evaluate_scenario
from app.loader import load_scenario


def test_evaluator_deterministic_small_graph_metrics() -> None:
    scenario = load_scenario(Path("scenarios/example_scenario.json"))
    summary = evaluate_scenario(scenario, TraversalConfig(max_depth=10, probability_cutoff=0.001))
    assert len(summary.decision_results) >= 2
    for result in summary.decision_results:
        assert 0.0 <= result.catastrophic_probability <= 1.0
        assert 0.0 <= result.positive_end_probability <= 1.0


def test_fork_exclusivity_and_sibling_visibility() -> None:
    scenario = load_scenario(Path("scenarios/example_parallel_fork_scenario.json"))
    summary = evaluate_scenario(scenario, TraversalConfig(max_depth=12, probability_cutoff=0.001))
    ids = [r.decision_node_id for r in summary.decision_results]
    assert "dec_direct" in ids
    assert "dec_buffered" in ids

    direct = next(r for r in summary.decision_results if r.decision_node_id == "dec_direct")
    joined_paths = "\n".join(" -> ".join(p.nodes) for p in direct.dangerous_paths + direct.positive_paths)
    assert "fork_media" in joined_paths or "fork_private" in joined_paths


def test_branch_shared_state_interaction_affects_outcomes() -> None:
    scenario = load_scenario(Path("scenarios/example_parallel_fork_scenario.json"))
    summary = evaluate_scenario(scenario, TraversalConfig(max_depth=12, probability_cutoff=0.001))
    direct = next(r for r in summary.decision_results if r.decision_node_id == "dec_direct")
    buffered = next(r for r in summary.decision_results if r.decision_node_id == "dec_buffered")
    assert direct.catastrophic_probability >= buffered.catastrophic_probability


def test_evaluation_skips_incomplete_edges_cleanly() -> None:
    scenario = load_scenario(Path("scenarios/draft_example.json"))
    summary = evaluate_scenario(scenario)
    assert "de3" in summary.skipped_incomplete_edges
