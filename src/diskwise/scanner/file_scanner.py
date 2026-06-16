"""Read-only file tree scanner."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from diskwise.rules.rule_classifier import classify_by_extension
from diskwise.safety.path_policy import (
    assert_scan_root_allowed,
    is_protected_path,
    is_symlink_or_reparse_point,
)
from diskwise.scanner.file_metadata import FileMetadata


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

    def scan(self, root: Path | str) -> Iterator[FileMetadata]:
        allowed_root = assert_scan_root_allowed(root)
        yield from self._walk(allowed_root)

    def _walk(self, directory: Path) -> Iterator[FileMetadata]:
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if is_symlink_or_reparse_point(path):
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if is_protected_path(path):
                            continue
                        yield from self._walk(path)
                    elif entry.is_file(follow_symlinks=False):
                        metadata = _metadata_from_direntry(entry)
                        if metadata is not None:
                            yield metadata
        except PermissionError:
            return
        except FileNotFoundError:
            return
