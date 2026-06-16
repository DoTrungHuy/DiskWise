"""Read-only file tree scanner."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from pathlib import Path

from diskwise.rules.rule_classifier import classify_by_extension
from diskwise.safety.path_policy import (
    assert_scan_root_allowed,
    is_protected_path,
    is_symlink_or_reparse_point,
)
from diskwise.scanner.file_metadata import FileMetadata

DEFAULT_IGNORED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "node_modules",
        "venv",
    }
)

DEFAULT_IGNORED_DATA_DIR_NAMES = frozenset({"cache", "logs", "vectors"})
DEFAULT_MAX_SCAN_FILES = 50_000


class ScanLimitExceededError(RuntimeError):
    """Raised when a scan reaches its configured file limit."""


def _metadata_from_direntry(entry: os.DirEntry[str]) -> FileMetadata | None:
    try:
        stat = entry.stat(follow_symlinks=False)
    except OSError:
        return None

    path = Path(entry.path).resolve(strict=False)
    return FileMetadata(
        path=path,
        name=path.name,
        extension=path.suffix.lower(),
        size=int(stat.st_size),
        modified_at=float(stat.st_mtime),
        created_at=float(getattr(stat, "st_ctime", 0.0) or 0.0),
        category=classify_by_extension(path),
    )


class FileScanner:
    """Scan files without following symbolic links or modifying anything."""

    def __init__(
        self,
        *,
        ignored_directory_names: set[str] | frozenset[str] | None = None,
        max_files: int | None = DEFAULT_MAX_SCAN_FILES,
    ) -> None:
        self._ignored_directory_names = {
            name.lower()
            for name in (ignored_directory_names or DEFAULT_IGNORED_DIRECTORY_NAMES)
        }
        self._max_files = max_files

    def scan(
        self,
        root: Path | str,
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[FileMetadata]:
        allowed_root = assert_scan_root_allowed(root)
        count = 0
        for metadata in self._walk(allowed_root, should_stop=should_stop):
            if should_stop and should_stop():
                return
            if self._max_files is not None and count >= self._max_files:
                raise ScanLimitExceededError(
                    f"扫描文件数量超过上限：{self._max_files}"
                )
            count += 1
            yield metadata

    def _walk(
        self,
        directory: Path,
        *,
        should_stop: Callable[[], bool] | None = None,
    ) -> Iterator[FileMetadata]:
        if should_stop and should_stop():
            return
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if should_stop and should_stop():
                        return
                    path = Path(entry.path)
                    if is_symlink_or_reparse_point(path):
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if is_protected_path(path) or self._should_ignore_directory(path):
                            continue
                        yield from self._walk(path, should_stop=should_stop)
                    elif entry.is_file(follow_symlinks=False):
                        metadata = _metadata_from_direntry(entry)
                        if metadata is not None:
                            yield metadata
        except PermissionError:
            return
        except FileNotFoundError:
            return

    def _should_ignore_directory(self, path: Path) -> bool:
        name = path.name.lower()
        if name in self._ignored_directory_names:
            return True
        return (
            path.parent.name.lower() == "data"
            and name in DEFAULT_IGNORED_DATA_DIR_NAMES
        )
