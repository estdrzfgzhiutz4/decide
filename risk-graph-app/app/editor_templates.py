"""Editor template helpers (reserved for future server-side templating)."""

from __future__ import annotations

from pathlib import Path


def editor_static_dir() -> Path:
    """Return static directory path used by editor server."""
    return Path(__file__).resolve().parent / "static"
