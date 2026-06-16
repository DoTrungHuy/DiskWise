"""Resolve destination filename conflicts."""

from __future__ import annotations

from pathlib import Path


def next_available_path(destination: Path) -> Path:
    """Return destination or a suffixed sibling that does not exist."""
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    index = 1
    while True:
        candidate = parent / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1
