"""Excel workbook extraction with optional openpyxl support."""

from __future__ import annotations

from pathlib import Path

from diskwise.extractors.base import BaseExtractor, ExtractionResult, truncate_preview


class ExcelExtractor(BaseExtractor):
    name = "excel"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            import openpyxl  # type: ignore[import-not-found]
        except ImportError:
            return ExtractionResult("excel", "", self.name, "未安装 openpyxl，暂不能提取 Excel")

        try:
            workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
            lines: list[str] = []
            for worksheet in workbook.worksheets[:3]:
                lines.append(f"[{worksheet.title}]")
                for row in worksheet.iter_rows(max_row=20, values_only=True):
                    values = [str(value) for value in row if value is not None]
                    if values:
                        lines.append(" | ".join(values))
            workbook.close()
        except Exception as exc:
            return ExtractionResult("excel", "", self.name, str(exc))
        return ExtractionResult("excel", truncate_preview("\n".join(lines)), self.name)
