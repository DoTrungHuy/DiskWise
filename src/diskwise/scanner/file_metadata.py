"""Metadata collected during read-only scans."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileMetadata:
    path: Path
    name: str
    extension: str
    size: int
    modified_at: float
    created_at: float | None
    category: str | None = None
