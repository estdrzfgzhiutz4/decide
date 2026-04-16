"""Scenario loading from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .models import Condition, Edge, Effect, Node, Scenario, Scoring


def load_scenario(path: str | Path) -> Scenario:
    """Load a scenario JSON file into strongly typed dataclasses."""
    raw: Dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))

    nodes = [
        Node(
            id=n["id"],
            label=n["label"],
            type=n["type"],
            harm=float(n.get("harm", 0.0)),
            terminal=bool(n.get("terminal", False)),
            positive=bool(n.get("positive", False)),
            failure=bool(n.get("failure", False)),
            notes=n.get("notes"),
            tags=list(n.get("tags", [])),
        )
        for n in raw.get("nodes", [])
    ]

    edges = []
    for e in raw.get("edges", []):
        conditions = [Condition(**c) for c in e.get("active_if", [])]
        effects = [Effect(**fx) for fx in e.get("effects", [])]
        edges.append(
            Edge(
                id=e["id"],
                from_node=e["from"],
                to_node=e["to"],
                probability=float(e["probability"]),
                transition_kind=e["transition_kind"],
                active_if=conditions,
                effects=effects,
                uncertainty=float(e.get("uncertainty", 0.0)),
                reversibility_cost=float(e.get("reversibility_cost", 0.0)),
                notes=e.get("notes"),
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
    )
