"""Utility helpers."""

from __future__ import annotations

from itertools import product
from typing import Iterable, List, Sequence, Tuple, TypeVar

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
