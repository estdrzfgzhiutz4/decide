"""Core data models for risk graph scenarios and evaluation output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


VALID_NODE_TYPES = {
    "decision",
    "event",
    "actor",
    "outcome",
    "terminal_positive",
    "terminal_failure",
}

VALID_TRANSITION_KINDS = {"branch", "fork", "escalate", "resolve"}

VALID_CONDITION_OPS = {
    "equals",
    "not_equals",
    "is_true",
    "is_false",
    "greater_than",
    "greater_or_equal",
    "less_than",
    "less_or_equal",
}

VALID_EFFECT_OPS = {"set", "increment", "decrement"}
VALID_DRAFT_STATUS = {"complete", "incomplete", "guessed"}
VALID_SCENARIO_MODES = {"strict", "draft"}


@dataclass(slots=True)
class Condition:
    var: str
    op: str
    value: Any = None


@dataclass(slots=True)
class Effect:
    var: str
    op: str
    value: Any


@dataclass(slots=True)
class Node:
    id: str = ""
    label: str = ""
    type: str = ""
    harm: float = 0.0
    terminal: bool = False
    positive: bool = False
    failure: bool = False
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    draft_status: str = "complete"
    draft_note: Optional[str] = None


@dataclass(slots=True)
class Edge:
    id: str = ""
    from_node: str = ""
    to_node: str = ""
    probability: Optional[float] = None
    transition_kind: str = ""
    active_if: List[Condition] = field(default_factory=list)
    effects: List[Effect] = field(default_factory=list)
    uncertainty: float = 0.0
    reversibility_cost: float = 0.0
    notes: Optional[str] = None
    draft_status: str = "complete"
    draft_note: Optional[str] = None


@dataclass(slots=True)
class Scoring:
    catastrophic_weight: float = 1_000_000.0
    positive_weight: float = 10_000.0
    harm_weight: float = 1.0
    uncertainty_weight: float = 10.0
    reversibility_weight: float = 5.0


@dataclass(slots=True)
class Scenario:
    scenario_name: str
    description: str
    variables: Dict[str, Any]
    scoring: Scoring
    nodes: List[Node]
    edges: List[Edge]
    mode: str = "strict"
    metadata: Dict[str, Any] = field(default_factory=dict)
    editor: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    draft_warnings: List[str] = field(default_factory=list)
    incomplete_items: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(slots=True)
class PathSummary:
    nodes: List[str]
    probability: float
    total_harm: float
    total_uncertainty_penalty: float
    total_reversibility_penalty: float
    ends_in_failure: bool
    ends_in_positive: bool

    @property
    def path_risk(self) -> float:
        return self.probability * self.total_harm


@dataclass(slots=True)
class DecisionEvaluation:
    decision_node_id: str
    decision_label: str
    catastrophic_probability: float
    positive_end_probability: float
    expected_harm: float
    expected_uncertainty_penalty: float
    expected_reversibility_penalty: float
    composite_score: float
    dangerous_paths: List[PathSummary]
    positive_paths: List[PathSummary]
    interpretation: str


@dataclass(slots=True)
class EvaluationSummary:
    scenario_name: str
    decision_results: List[DecisionEvaluation]
    skipped_incomplete_edges: List[str] = field(default_factory=list)
    skipped_decisions: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
