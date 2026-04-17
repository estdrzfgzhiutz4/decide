"""Utility helpers."""

from __future__ import annotations

import re
from itertools import product
from typing import Iterable, List, Sequence, Tuple, TypeVar

from .models import Edge, Node

T = TypeVar("T")


def powerset_including_empty(items: Sequence[T]) -> List[Tuple[T, ...]]:
    """Generate all subset combinations for independent branch events."""
    choices = []
    for selectors in product([False, True], repeat=len(items)):
        selected = tuple(item for item, take in zip(items, selectors) if take)
        choices.append(selected)
    return choices


def format_probability(value: float) -> str:
    """Render probability as fixed precision percentage."""
    return f"{value * 100:.2f}%"


def top_n(items: Iterable[T], n: int, key):
    """Return top-n items sorted descending by key."""
    return sorted(items, key=key, reverse=True)[:n]


def slugify_identifier(text: str, fallback: str = "item") -> str:
    """Create a simple identifier from free text."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return cleaned or fallback


def is_complete_node(node: Node) -> bool:
    """Check if a node has required fields for strict mode."""
    return bool(node.id and node.label and node.type)


def is_complete_edge(edge: Edge) -> bool:
    """Check if an edge has required fields for strict mode/evaluation."""
    return bool(
        edge.id
        and edge.from_node
        and edge.to_node
        and edge.transition_kind
        and edge.probability is not None
    )
