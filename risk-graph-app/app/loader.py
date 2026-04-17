"""Scenario loading from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .models import Condition, Edge, Effect, Node, Scenario, Scoring


def load_scenario(path: str | Path) -> Scenario:
    """Load a scenario JSON file into strongly typed dataclasses."""
    raw: Dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return load_scenario_data(raw)


def load_scenario_data(raw: Dict[str, Any]) -> Scenario:
    """Load a scenario from in-memory JSON-like dict data."""

    nodes = [
        Node(
            id=n.get("id", ""),
            label=n.get("label", ""),
            type=n.get("type", ""),
            harm=float(n.get("harm", 0.0)),
            terminal=bool(n.get("terminal", False)),
            positive=bool(n.get("positive", False)),
            failure=bool(n.get("failure", False)),
            notes=n.get("notes"),
            tags=list(n.get("tags", [])),
            draft_status=n.get("draft_status", "complete"),
            draft_note=n.get("draft_note"),
        )
        for n in raw.get("nodes", [])
    ]

    edges = []
    for e in raw.get("edges", []):
        conditions = [Condition(**c) for c in e.get("active_if", [])]
        effects = [Effect(**fx) for fx in e.get("effects", [])]
        edges.append(
            Edge(
                id=e.get("id", ""),
                from_node=e.get("from", ""),
                to_node=e.get("to", ""),
                probability=float(e["probability"]) if e.get("probability") is not None else None,
                transition_kind=e.get("transition_kind", ""),
                active_if=conditions,
                effects=effects,
                uncertainty=float(e.get("uncertainty", 0.0)),
                reversibility_cost=float(e.get("reversibility_cost", 0.0)),
                notes=e.get("notes"),
                draft_status=e.get("draft_status", "complete"),
                draft_note=e.get("draft_note"),
            )
        )

    scoring_raw = raw.get("scoring", {})
    scoring = Scoring(
        catastrophic_weight=float(scoring_raw.get("catastrophic_weight", Scoring.catastrophic_weight)),
        positive_weight=float(scoring_raw.get("positive_weight", Scoring.positive_weight)),
        harm_weight=float(scoring_raw.get("harm_weight", Scoring.harm_weight)),
        uncertainty_weight=float(scoring_raw.get("uncertainty_weight", Scoring.uncertainty_weight)),
        reversibility_weight=float(scoring_raw.get("reversibility_weight", Scoring.reversibility_weight)),
    )

    return Scenario(
        scenario_name=raw["scenario_name"],
        description=raw.get("description", ""),
        variables=dict(raw.get("variables", {})),
        scoring=scoring,
        nodes=nodes,
        edges=edges,
        mode=raw.get("mode", "strict"),
        metadata=dict(raw.get("metadata", {})),
        editor=dict(raw.get("editor", {})),
    )


def scenario_to_dict(scenario: Scenario) -> Dict[str, Any]:
    """Serialize scenario dataclass into JSON-compatible dict."""
    return {
        "scenario_name": scenario.scenario_name,
        "description": scenario.description,
        "mode": scenario.mode,
        "metadata": scenario.metadata,
        "editor": scenario.editor,
        "variables": scenario.variables,
        "scoring": {
            "catastrophic_weight": scenario.scoring.catastrophic_weight,
            "positive_weight": scenario.scoring.positive_weight,
            "harm_weight": scenario.scoring.harm_weight,
            "uncertainty_weight": scenario.scoring.uncertainty_weight,
            "reversibility_weight": scenario.scoring.reversibility_weight,
        },
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "type": n.type,
                "harm": n.harm,
                "terminal": n.terminal,
                "positive": n.positive,
                "failure": n.failure,
                "notes": n.notes,
                "tags": n.tags,
                "draft_status": n.draft_status,
                "draft_note": n.draft_note,
            }
            for n in scenario.nodes
        ],
        "edges": [
            {
                "id": e.id,
                "from": e.from_node,
                "to": e.to_node,
                "probability": e.probability,
                "transition_kind": e.transition_kind,
                "active_if": [{"var": c.var, "op": c.op, "value": c.value} for c in e.active_if],
                "effects": [{"var": fx.var, "op": fx.op, "value": fx.value} for fx in e.effects],
                "uncertainty": e.uncertainty,
                "reversibility_cost": e.reversibility_cost,
                "notes": e.notes,
                "draft_status": e.draft_status,
                "draft_note": e.draft_note,
            }
            for e in scenario.edges
        ],
    }


def save_scenario(path: str | Path, scenario: Scenario) -> Path:
    """Write scenario to disk as formatted JSON."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scenario_to_dict(scenario), indent=2), encoding="utf-8")
    return out
