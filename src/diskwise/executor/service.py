"""Disabled file executor for the initial skeleton."""

from __future__ import annotations

from pathlib import Path


class FeatureDisabledError(RuntimeError):
    """Raised when an intentionally unavailable feature is called."""


class FileExecutor:
    """Placeholder that guarantees version 0.1 cannot modify user files."""

    def move(self, source: Path, destination: Path) -> None:
        raise FeatureDisabledError("0.1 骨架版本未启用文件移动")

    def rename(self, source: Path, new_name: str) -> None:
        raise FeatureDisabledError("0.1 骨架版本未启用文件重命名")

    def delete(self, target: Path) -> None:
        raise FeatureDisabledError("0.1 骨架版本未启用文件删除")

