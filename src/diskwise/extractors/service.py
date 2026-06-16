"""Choose and run the right content extractor for a file."""

from __future__ import annotations

from pathlib import Path

from diskwise.extractors.base import ExtractionResult
from diskwise.extractors.excel_extractor import ExcelExtractor
from diskwise.extractors.image_extractor import ImageExtractor
from diskwise.extractors.pdf_extractor import PdfExtractor
from diskwise.extractors.text_extractor import TextExtractor
from diskwise.extractors.word_extractor import WordExtractor
from diskwise.rules.category_rules import IMAGE_EXTENSIONS, TEXT_LIKE_EXTENSIONS


class ExtractionService:
    """Extract short previews only, never full private documents."""

    def extract(self, path: Path | str) -> ExtractionResult:
        candidate = Path(path)
        extension = candidate.suffix.lower()
        if extension in TEXT_LIKE_EXTENSIONS:
            return TextExtractor().extract(candidate)
        if extension == ".pdf":
            return PdfExtractor().extract(candidate)
        if extension in {".doc", ".docx"}:
            return WordExtractor().extract(candidate)
        if extension in {".xls", ".xlsx"}:
            return ExcelExtractor().extract(candidate)
        if extension in IMAGE_EXTENSIONS:
            return ImageExtractor().extract(candidate)
        return ExtractionResult("unknown", "", "none", "此文件类型暂不提取内容")
