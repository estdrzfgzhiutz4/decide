"""Stateful full-future evaluator for risk graph decisions."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .conditions import conditions_match
from .models import DecisionEvaluation, EvaluationSummary, PathSummary, Scenario
from .state import apply_effects
from .utils import is_complete_edge, powerset_including_empty, top_n


@dataclass(slots=True)
class TraversalConfig:
    max_depth: int = 12
    max_visits_per_node: int = 2
    probability_cutoff: float = 0.01


@dataclass(slots=True)
class _PathState:
    pending_nodes: Tuple[str, ...]
    variables: Dict[str, Any]
    cumulative_probability: float
    cumulative_harm: float
    cumulative_uncertainty: float
    cumulative_reversibility: float
    path_nodes: List[str]
    visit_counts: Dict[str, int]
    depth: int
    hit_failure: bool
    hit_positive: bool


def evaluate_scenario(
    scenario: Scenario,
    config: TraversalConfig | None = None,
) -> EvaluationSummary:
    """Evaluate all decision nodes across full reachable futures."""
    cfg = config or TraversalConfig()
    node_by_id = {n.id: n for n in scenario.nodes}
    outgoing = defaultdict(list)
    for edge in scenario.edges:
        outgoing[edge.from_node].append(edge)

    results: List[DecisionEvaluation] = []
    skipped_edges: set[str] = set()
    skipped_decisions: List[str] = []
    for node in scenario.nodes:
        if node.type != "decision":
            continue
        node_result, decision_skipped, edge_skips = _evaluate_decision(
            node.id, scenario, node_by_id, outgoing, cfg
        )
        skipped_edges.update(edge_skips)
        if decision_skipped:
            skipped_decisions.append(node.id)
            continue
        results.append(node_result)

    results.sort(key=lambda r: r.composite_score)
    return EvaluationSummary(
        scenario_name=scenario.scenario_name,
        decision_results=results,
        skipped_incomplete_edges=sorted(skipped_edges),
        skipped_decisions=skipped_decisions,
        assumptions=[
            "Incomplete edges are skipped during traversal.",
            "Decisions without traversable complete edges are excluded from ranking.",
        ],
    )


def _evaluate_decision(decision_id, scenario, node_by_id, outgoing, cfg):
    terminal_paths: List[PathSummary] = []
    skipped_edges: set[str] = set()
    initial_complete = [e for e in outgoing.get(decision_id, []) if is_complete_edge(e)]
    if not initial_complete:
        for edge in outgoing.get(decision_id, []):
            if not is_complete_edge(edge):
                skipped_edges.add(edge.id or "<missing-id>")
        return None, True, skipped_edges
    queue: List[_PathState] = [
        _PathState(
            pending_nodes=(decision_id,),
            variables=dict(scenario.variables),
            cumulative_probability=1.0,
            cumulative_harm=0.0,
            cumulative_uncertainty=0.0,
            cumulative_reversibility=0.0,
            path_nodes=[],
            visit_counts={},
            depth=0,
            hit_failure=False,
            hit_positive=False,
        )
    ]

    while queue:
        state = queue.pop()
        if state.cumulative_probability < cfg.probability_cutoff:
            continue
        if state.depth > cfg.max_depth or not state.pending_nodes:
            terminal_paths.append(
                PathSummary(
                    nodes=state.path_nodes,
                    probability=state.cumulative_probability,
                    total_harm=state.cumulative_harm,
                    total_uncertainty_penalty=state.cumulative_uncertainty,
                    total_reversibility_penalty=state.cumulative_reversibility,
                    ends_in_failure=state.hit_failure,
                    ends_in_positive=(state.hit_positive and not state.hit_failure),
                )
            )
            continue

        current = state.pending_nodes[0]
        rest = state.pending_nodes[1:]
        node = node_by_id[current]

        visits = dict(state.visit_counts)
        visits[current] = visits.get(current, 0) + 1
        if visits[current] > cfg.max_visits_per_node:
            terminal_paths.append(
                PathSummary(
                    nodes=state.path_nodes + [current],
                    probability=state.cumulative_probability,
                    total_harm=state.cumulative_harm,
                    total_uncertainty_penalty=state.cumulative_uncertainty,
                    total_reversibility_penalty=state.cumulative_reversibility,
                    ends_in_failure=state.hit_failure,
                    ends_in_positive=(state.hit_positive and not state.hit_failure),
                )
            )
            continue

        new_harm = state.cumulative_harm + node.harm
        new_path = state.path_nodes + [current]
        hit_failure = state.hit_failure or node.failure or node.type == "terminal_failure"
        hit_positive = state.hit_positive or node.positive or node.type == "terminal_positive"

        active_edges = []
        for edge in outgoing.get(current, []):
            if not is_complete_edge(edge):
                skipped_edges.add(edge.id or "<missing-id>")
                continue
            if conditions_match(edge.active_if, state.variables):
                active_edges.append(edge)
        if node.terminal or not active_edges:
            queue.append(
                _PathState(
                    pending_nodes=rest,
                    variables=state.variables,
                    cumulative_probability=state.cumulative_probability,
                    cumulative_harm=new_harm,
                    cumulative_uncertainty=state.cumulative_uncertainty,
                    cumulative_reversibility=state.cumulative_reversibility,
                    path_nodes=new_path,
                    visit_counts=visits,
                    depth=state.depth + 1,
                    hit_failure=hit_failure,
                    hit_positive=hit_positive,
                )
            )
            continue

        fork_edges = [e for e in active_edges if e.transition_kind == "fork"]
        non_fork_edges = [e for e in active_edges if e.transition_kind != "fork"]

        fork_options: List[Tuple[List, float]] = [([], 1.0)]
        if fork_edges:
            fork_options = [([edge], edge.probability) for edge in fork_edges]
            no_fork_prob = max(0.0, 1.0 - sum(e.probability for e in fork_edges))
            if no_fork_prob > 0:
                fork_options.append(([], no_fork_prob))

        branch_subsets = powerset_including_empty(non_fork_edges)
        for fork_choice, fork_prob in fork_options:
            for subset in branch_subsets:
                probability_factor = fork_prob
                for edge in non_fork_edges:
                    if edge in subset:
                        probability_factor *= edge.probability
                    else:
                        probability_factor *= (1.0 - edge.probability)
                if probability_factor <= 0:
                    continue

                selected = list(fork_choice) + list(subset)
                next_vars = dict(state.variables)
                next_pending = list(rest)
                next_uncertainty = state.cumulative_uncertainty
                next_reversibility = state.cumulative_reversibility
                for edge in sorted(selected, key=lambda x: x.id):
                    next_vars = apply_effects(next_vars, edge.effects)
                    next_pending.append(edge.to_node)
                    next_uncertainty += edge.uncertainty
                    next_reversibility += edge.reversibility_cost

                queue.append(
                    _PathState(
                        pending_nodes=tuple(next_pending),
                        variables=next_vars,
                        cumulative_probability=state.cumulative_probability * probability_factor,
                        cumulative_harm=new_harm,
                        cumulative_uncertainty=next_uncertainty,
                        cumulative_reversibility=next_reversibility,
                        path_nodes=new_path,
                        visit_counts=visits,
                        depth=state.depth + 1,
                        hit_failure=hit_failure,
                        hit_positive=hit_positive,
                    )
                )

    if not terminal_paths:
        return None, True, skipped_edges

    catastrophic_probability = sum(p.probability for p in terminal_paths if p.ends_in_failure)
    positive_probability = sum(p.probability for p in terminal_paths if p.ends_in_positive)
    expected_harm = sum(p.probability * p.total_harm for p in terminal_paths)
    expected_uncertainty = sum(p.probability * p.total_uncertainty_penalty for p in terminal_paths)
    expected_reversibility = sum(p.probability * p.total_reversibility_penalty for p in terminal_paths)

    scoring = scenario.scoring
    composite = (
        scoring.catastrophic_weight * catastrophic_probability
        - scoring.positive_weight * positive_probability
        + scoring.harm_weight * expected_harm
        + scoring.uncertainty_weight * expected_uncertainty
        + scoring.reversibility_weight * expected_reversibility
    )

    dangerous = top_n(
        terminal_paths,
        5,
        key=lambda p: (1 if p.ends_in_failure else 0, p.path_risk),
    )
    positive = top_n(
        [p for p in terminal_paths if p.ends_in_positive],
        5,
        key=lambda p: p.probability,
    )

    interpretation = (
        f"Downstream catastrophic probability is {catastrophic_probability:.3f}; "
        f"positive-end probability is {positive_probability:.3f}; "
        f"expected harm contribution is {expected_harm:.3f}."
    )

    node = node_by_id[decision_id]
    return DecisionEvaluation(
        decision_node_id=decision_id,
        decision_label=node.label,
        catastrophic_probability=catastrophic_probability,
        positive_end_probability=positive_probability,
        expected_harm=expected_harm,
        expected_uncertainty_penalty=expected_uncertainty,
        expected_reversibility_penalty=expected_reversibility,
        composite_score=composite,
        dangerous_paths=dangerous,
        positive_paths=positive,
        interpretation=interpretation,
    ), False, skipped_edges
