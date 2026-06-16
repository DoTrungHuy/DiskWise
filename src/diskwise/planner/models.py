"""Organization plan data structures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanSuggestion:
    file_id: int
    action: str
    source_path: str
    target_path: str
    suggested_name: str | None
    category: str | None
    reason: str
