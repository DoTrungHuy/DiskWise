"""Plain text and source code extraction."""

from __future__ import annotations

from pathlib import Path

from diskwise.extractors.base import BaseExtractor, ExtractionResult, truncate_preview


class TextExtractor(BaseExtractor):
    name = "text"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            return ExtractionResult("text", "", self.name, str(exc))
        return ExtractionResult("text", truncate_preview(text), self.name)
