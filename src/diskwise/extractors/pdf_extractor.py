"""PDF text extraction with optional PyMuPDF support."""

from __future__ import annotations

from pathlib import Path

from diskwise.extractors.base import BaseExtractor, ExtractionResult, truncate_preview


class PdfExtractor(BaseExtractor):
    name = "pdf"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            import fitz  # type: ignore[import-not-found]
        except ImportError:
            return ExtractionResult("pdf", "", self.name, "未安装 PyMuPDF，暂不能提取 PDF")

        try:
            with fitz.open(path) as document:
                pages = [page.get_text("text") for page in document[:5]]
        except Exception as exc:
            return ExtractionResult("pdf", "", self.name, str(exc))
        return ExtractionResult("pdf", truncate_preview("\n".join(pages)), self.name)
