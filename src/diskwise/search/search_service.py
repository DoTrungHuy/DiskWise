"""Hybrid file search service."""

from __future__ import annotations

from pathlib import Path

from diskwise.database.repositories.file_repository import FileRecord
from diskwise.search.keyword_search import KeywordSearch


class SearchService:
    """Combine keyword results now; semantic results can be merged by callers."""

    def __init__(self, database_path: Path) -> None:
        self._keyword = KeywordSearch(database_path)

    def search(self, query: str, limit: int = 100) -> list[FileRecord]:
        return self._keyword.search(query, limit=limit)
