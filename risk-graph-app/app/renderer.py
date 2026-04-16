"""Graphviz rendering for scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from graphviz import Digraph

from .models import EvaluationSummary, Scenario


NODE_SHAPES = {
    "decision": "box",
    "event": "ellipse",
    "actor": "hexagon",
    "outcome": "oval",
    "terminal_positive": "doublecircle",
    "terminal_failure": "octagon",
}


def render_scenario(
    scenario: Scenario,
    output_dir: str | Path,
    fmt: str = "svg",
    evaluation: Optional[EvaluationSummary] = None,
) -> Path:
    """Render scenario graph to output directory in SVG or PNG format."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    safest = None
    if evaluation and evaluation.decision_results:
        safest = evaluation.decision_results[0].decision_node_id

    dot = Digraph(comment=scenario.scenario_name, format=fmt)
    dot.attr(rankdir="LR")

    for node in scenario.nodes:
        shape = NODE_SHAPES[node.type]
        color = "black"
        fill = "white"
        penwidth = "1"
        if node.type == "terminal_failure" or node.failure:
            color = "firebrick"
            fill = "mistyrose"
        elif node.type == "terminal_positive" or node.positive:
            color = "darkgreen"
            fill = "honeydew"
        if safest and node.id == safest:
            color = "blue"
            penwidth = "3"

        label = f"{node.label}\\n({node.id})\\nHarm={node.harm}"
        dot.node(
            node.id,
            label=label,
            shape=shape,
            style="filled",
            color=color,
            fillcolor=fill,
            penwidth=penwidth,
        )

    for edge in scenario.edges:
        cond_text = ""
        if edge.active_if:
            parts = [f"{c.var} {c.op} {c.value}" for c in edge.active_if]
            cond_text = f"\\nif {' & '.join(parts)}"
        uncertainty = f"\\nu={edge.uncertainty}" if edge.uncertainty else ""
        label = f"p={edge.probability}\\n{edge.transition_kind}{uncertainty}{cond_text}"
        edge_color = "firebrick" if edge.transition_kind == "escalate" else "gray20"
        dot.edge(edge.from_node, edge.to_node, label=label, color=edge_color)

    outfile = output_path / f"{scenario.scenario_name}_graph"
    rendered = Path(dot.render(filename=outfile.name, directory=outfile.parent, cleanup=True))
    return rendered
