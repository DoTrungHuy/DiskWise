"""Image metadata extraction and OCR placeholder."""

from __future__ import annotations

from pathlib import Path

from diskwise.extractors.base import BaseExtractor, ExtractionResult


class ImageExtractor(BaseExtractor):
    name = "image"

    def extract(self, path: Path) -> ExtractionResult:
        try:
            from PIL import Image  # type: ignore[import-not-found]
        except ImportError:
            return ExtractionResult("image", "", self.name, "未安装 Pillow，暂不能读取图片信息")

        try:
            with Image.open(path) as image:
                preview = f"图片尺寸：{image.width}x{image.height}，格式：{image.format or path.suffix}"
        except Exception as exc:
            return ExtractionResult("image", "", self.name, str(exc))
        return ExtractionResult("image", preview, self.name)
