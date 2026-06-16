"""Content extractor interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MAX_PREVIEW_CHARS = 6000


@dataclass(frozen=True)
class ExtractionResult:
    content_type: str
    content_preview: str
    extractor: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseExtractor:
    """Base class for optional content extractors."""

    name = "base"

    def extract(self, path: Path) -> ExtractionResult:
        raise NotImplementedError


def truncate_preview(text: str, limit: int = MAX_PREVIEW_CHARS) -> str:
    cleaned = " ".join(text.replace("\x00", " ").split())
    return cleaned[:limit]
