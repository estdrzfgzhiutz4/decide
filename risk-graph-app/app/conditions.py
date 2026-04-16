"""Condition evaluation helpers."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from .models import Condition


def evaluate_condition(condition: Condition, variables: Dict[str, Any]) -> bool:
    """Evaluate a single condition against a variable dictionary."""
    value = variables.get(condition.var)
    op = condition.op

    if op == "equals":
        return value == condition.value
    if op == "not_equals":
        return value != condition.value
    if op == "is_true":
        return bool(value) is True
    if op == "is_false":
        return bool(value) is False
    if op == "greater_than":
        return value > condition.value
    if op == "greater_or_equal":
        return value >= condition.value
    if op == "less_than":
        return value < condition.value
    if op == "less_or_equal":
        return value <= condition.value
    raise ValueError(f"Unsupported condition op: {op}")


def conditions_match(conditions: Iterable[Condition], variables: Dict[str, Any]) -> bool:
    """Return True when all conditions are satisfied."""
    return all(evaluate_condition(c, variables) for c in conditions)
