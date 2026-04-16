"""State mutation helpers used during traversal."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from .models import Effect


def apply_effects(variables: Dict[str, Any], effects: Iterable[Effect]) -> Dict[str, Any]:
    """Return a copied variable dictionary with edge effects applied."""
    new_vars = dict(variables)
    for effect in effects:
        if effect.op == "set":
            new_vars[effect.var] = effect.value
        elif effect.op == "increment":
            new_vars[effect.var] = new_vars[effect.var] + effect.value
        elif effect.op == "decrement":
            new_vars[effect.var] = new_vars[effect.var] - effect.value
        else:
            raise ValueError(f"Unsupported effect op: {effect.op}")
    return new_vars
