"""Duplicate file detection."""

from __future__ import annotations

from pathlib import Path

from diskwise.database.repositories.file_repository import FileRepository, FileRecord
from diskwise.duplicates.hashing import hash_file, quick_hash_file


class DuplicateDetector:
    def __init__(self, database_path: Path) -> None:
        self._repository = FileRepository(database_path)

    def update_hashes_for_candidates(self) -> dict[str, list[FileRecord]]:
        for record in self._repository.duplicate_candidates():
            path = Path(record.path)
            if not path.exists() or not path.is_file():
                continue
            quick_hash = record.quick_hash or quick_hash_file(path)
            full_hash = record.full_hash or hash_file(path)
            self._repository.update_hashes(
                record.id,
                quick_hash=quick_hash,
                full_hash=full_hash,
            )
        return self._repository.duplicate_groups()
