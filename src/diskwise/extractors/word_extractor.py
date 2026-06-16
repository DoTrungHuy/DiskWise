"""Word document extraction with optional python-docx support."""

from __future__ import annotations

from pathlib import Path

from diskwise.extractors.base import BaseExtractor, ExtractionResult, truncate_preview


class WordExtractor(BaseExtractor):
    name = "word"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            import docx  # type: ignore[import-not-found]
        except ImportError:
            return ExtractionResult("word", "", self.name, "未安装 python-docx，暂不能提取 Word")

        try:
            document = docx.Document(str(path))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:
            return ExtractionResult("word", "", self.name, str(exc))
        return ExtractionResult("word", truncate_preview(text), self.name)
