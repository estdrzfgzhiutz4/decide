"""Validation rules for scenario integrity and modeling quality."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Dict, List, Set

from .models import (
    VALID_CONDITION_OPS,
    VALID_DRAFT_STATUS,
    VALID_EFFECT_OPS,
    VALID_NODE_TYPES,
    VALID_SCENARIO_MODES,
    VALID_TRANSITION_KINDS,
    Scenario,
    ValidationResult,
)
from .utils import is_complete_edge, is_complete_node


def validate_scenario(scenario: Scenario, mode: str | None = None) -> ValidationResult:
    """Validate the scenario and return errors plus warnings."""
    validation_mode = mode or scenario.mode or "strict"
    result = ValidationResult()
    node_ids = [n.id for n in scenario.nodes]
    edge_ids = [e.id for e in scenario.edges]

    if validation_mode not in VALID_SCENARIO_MODES:
        result.errors.append(f"Invalid validation mode: {validation_mode}")
        return result

    for item, count in Counter(node_ids).items():
        if item and count > 1:
            result.errors.append(f"Duplicate node id: {item}")
    for item, count in Counter(edge_ids).items():
        if item and count > 1:
            result.errors.append(f"Duplicate edge id: {item}")

    node_set = set(node_ids)
    outgoing: Dict[str, List] = defaultdict(list)

    for node in scenario.nodes:
        if node.draft_status not in VALID_DRAFT_STATUS:
            result.errors.append(f"Node {node.id or '<missing-id>'} has invalid draft_status")
        if not is_complete_node(node):
            msg = f"Incomplete node: {node.id or '<missing-id>'}"
            if validation_mode == "strict":
                result.errors.append(msg)
            else:
                result.draft_warnings.append(msg)
                result.incomplete_items.append(msg)
                continue
        if node.type not in VALID_NODE_TYPES:
            result.errors.append(f"Node {node.id} has invalid type: {node.type}")

    for edge in scenario.edges:
        if edge.draft_status not in VALID_DRAFT_STATUS:
            result.errors.append(f"Edge {edge.id or '<missing-id>'} has invalid draft_status")
        if not is_complete_edge(edge):
            msg = f"Incomplete edge: {edge.id or '<missing-id>'}"
            if validation_mode == "strict":
                result.errors.append(msg)
                continue
            result.draft_warnings.append(msg)
            result.incomplete_items.append(msg)
            continue

        outgoing[edge.from_node].append(edge)
        if edge.from_node not in node_set:
            result.errors.append(f"Edge {edge.id} references unknown source node: {edge.from_node}")
        if edge.to_node not in node_set:
            result.errors.append(f"Edge {edge.id} references unknown target node: {edge.to_node}")
        if edge.probability is None or not (0.0 <= edge.probability <= 1.0):
            result.errors.append(f"Edge {edge.id} has invalid probability {edge.probability}")
        if not (0.0 <= edge.uncertainty <= 1.0):
            result.errors.append(f"Edge {edge.id} has invalid uncertainty {edge.uncertainty}")
        if edge.transition_kind not in VALID_TRANSITION_KINDS:
            result.errors.append(
                f"Edge {edge.id} has invalid transition_kind: {edge.transition_kind}"
            )
        for cond in edge.active_if:
            if cond.op not in VALID_CONDITION_OPS:
                result.errors.append(f"Edge {edge.id} has invalid condition op: {cond.op}")
            if cond.var not in scenario.variables:
                result.errors.append(
                    f"Edge {edge.id} condition references unknown variable: {cond.var}"
                )
        for effect in edge.effects:
            if effect.op not in VALID_EFFECT_OPS:
                result.errors.append(f"Edge {edge.id} has invalid effect op: {effect.op}")
            # v1 rule: unknown effect variables are rejected to prevent accidental typos.
            if effect.var not in scenario.variables:
                result.errors.append(
                    f"Edge {edge.id} effect references unknown variable: {effect.var}"
                )

    for node in scenario.nodes:
        outs = outgoing.get(node.id, [])
        if node.terminal and outs:
            result.errors.append(f"Terminal node {node.id} must not have outgoing edges")
        if node.type == "decision" and not outs:
            if validation_mode == "strict":
                result.errors.append(f"Decision node {node.id} has no outgoing edges")
            else:
                msg = f"Decision node {node.id} currently has no complete outgoing edges"
                result.draft_warnings.append(msg)
                result.incomplete_items.append(msg)

    by_source_and_kind: Dict[str, Dict[str, List]] = defaultdict(lambda: defaultdict(list))
    for edge in scenario.edges:
        by_source_and_kind[edge.from_node][edge.transition_kind].append(edge)
    for src, kinds in by_source_and_kind.items():
        fork_sum = sum(e.probability for e in kinds.get("fork", []))
        if kinds.get("fork") and abs(fork_sum - 1.0) > 0.05:
            result.warnings.append(
                f"Fork edges from node {src} sum to {fork_sum:.3f}; expected near 1.0 for exclusive alternatives"
            )

    result.warnings.extend(_find_unreachable_nodes(scenario))
    return result


def _find_unreachable_nodes(scenario: Scenario) -> List[str]:
    node_set: Set[str] = {n.id for n in scenario.nodes}
    adjacency = defaultdict(list)
    for edge in scenario.edges:
        adjacency[edge.from_node].append(edge.to_node)

    starts = [n.id for n in scenario.nodes if n.type == "decision"]
    visited: Set[str] = set(starts)
    queue = deque(starts)

    while queue:
        cur = queue.popleft()
        for nxt in adjacency.get(cur, []):
            if nxt in node_set and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    warnings = []
    for node in scenario.nodes:
        if node.id not in visited:
            warnings.append(f"Unreachable node: {node.id}")
    return warnings
