"""Keyword search over the SQLite file index."""

from __future__ import annotations

from pathlib import Path

from diskwise.database.repositories.file_repository import FileRecord, FileRepository


class KeywordSearch:
    def __init__(self, database_path: Path) -> None:
        self._repository = FileRepository(database_path)

    def search(self, query: str, limit: int = 100) -> list[FileRecord]:
        if not query.strip():
            return self._repository.list_files(limit=limit)
        return self._repository.search_files(query, limit=limit)
