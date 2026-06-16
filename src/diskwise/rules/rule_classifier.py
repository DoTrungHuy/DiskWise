"""Simple extension-based classification."""

from __future__ import annotations

from pathlib import Path

from diskwise.rules.category_rules import CATEGORY_RULES


def classify_by_extension(path: Path | str) -> str | None:
    """Return a deterministic category for known extensions."""
    extension = Path(path).suffix.lower()
    return CATEGORY_RULES.get(extension)
