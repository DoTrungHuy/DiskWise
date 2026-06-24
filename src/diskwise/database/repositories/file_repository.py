"""Persistence for scanned files, extracted content, and search records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from diskwise.database.connection import connect
from diskwise.scanner.file_metadata import FileMetadata


@dataclass(frozen=True)
class FileRecord:
    id: int
    path: str
    name: str
    extension: str
    size: int
    modified_at: float
    category: str | None
    quick_hash: str | None = None
    full_hash: str | None = None
    content_preview: str | None = None
    status: str = "active"


@dataclass(frozen=True)
class ScanRootRecord:
    id: int
    path: str
    created_at: str
    last_scanned_at: str | None


def _row_to_record(row) -> FileRecord:
    return FileRecord(
        id=row["id"],
        path=row["path"],
        name=row["name"],
        extension=row["extension"],
        size=row["size"],
        modified_at=row["modified_at"],
        category=row["category"],
        quick_hash=row["quick_hash"],
        full_hash=row["full_hash"],
        content_preview=row["content_preview"] if "content_preview" in row.keys() else None,
        status=row["status"] if "status" in row.keys() else "active",
    )


class FileRepository:
    """Store and query the file index."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def upsert_scan_root(self, root: Path) -> int:
        normalized = str(root.resolve())
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO scan_roots (path, last_scanned_at)
                VALUES (?, CURRENT_TIMESTAMP)
                ON CONFLICT(path) DO UPDATE SET last_scanned_at = CURRENT_TIMESTAMP
                """,
                (normalized,),
            )
            row = connection.execute(
                "SELECT id FROM scan_roots WHERE path = ?",
                (normalized,),
            ).fetchone()
            return int(row["id"])

    def upsert_file(self, metadata: FileMetadata, root_id: int) -> int:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO files (
                    root_id, path, name, extension, size, modified_at,
                    created_at, category, status, indexed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
                ON CONFLICT(path) DO UPDATE SET
                    root_id = excluded.root_id,
                    name = excluded.name,
                    extension = excluded.extension,
                    size = excluded.size,
                    modified_at = excluded.modified_at,
                    created_at = excluded.created_at,
                    category = excluded.category,
                    status = 'active',
                    indexed_at = CURRENT_TIMESTAMP
                """,
                (
                    root_id,
                    str(metadata.path),
                    metadata.name,
                    metadata.extension,
                    metadata.size,
                    metadata.modified_at,
                    metadata.created_at,
                    metadata.category,
                ),
            )
            row = connection.execute(
                "SELECT id FROM files WHERE path = ?",
                (str(metadata.path),),
            ).fetchone()
            return int(row["id"])

    def save_many(self, root: Path, files: Iterable[FileMetadata]) -> int:
        root_id = self.upsert_scan_root(root)
        count = 0
        for metadata in files:
            self.upsert_file(metadata, root_id)
            count += 1
        return count

    def list_files(
        self,
        limit: int = 500,
        *,
        query: str = "",
        category: str = "",
        extension: str = "",
    ) -> list[FileRecord]:
        filters = ["f.status = 'active'"]
        params: list[object] = []
        if query.strip():
            like = f"%{query.strip()}%"
            filters.append(
                """
                (
                    f.path LIKE ?
                    OR f.name LIKE ?
                    OR COALESCE(f.category, '') LIKE ?
                    OR COALESCE(c.content_preview, '') LIKE ?
                )
                """
            )
            params.extend([like, like, like, like])
        if category.strip():
            filters.append("COALESCE(f.category, '') = ?")
            params.append(category.strip())
        if extension.strip():
            normalized_extension = extension.strip().lower()
            if normalized_extension and not normalized_extension.startswith("."):
                normalized_extension = f".{normalized_extension}"
            filters.append("f.extension = ?")
            params.append(normalized_extension)
        params.append(limit)
        with connect(self._database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT f.*, c.content_preview
                FROM files f
                LEFT JOIN extracted_content c ON c.file_id = f.id
                WHERE {" AND ".join(filters)}
                ORDER BY f.indexed_at DESC, f.path
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def count_files(self) -> int:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM files WHERE status = 'active'"
            ).fetchone()
        return int(row["count"])

    def category_counts(self) -> list[tuple[str, int]]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT COALESCE(category, '未分类') AS category, COUNT(*) AS count
                FROM files
                WHERE status = 'active'
                GROUP BY COALESCE(category, '未分类')
                ORDER BY count DESC, category
                """
            ).fetchall()
        return [(row["category"], int(row["count"])) for row in rows]

    def extension_counts(self) -> list[tuple[str, int]]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT COALESCE(NULLIF(extension, ''), '(无扩展名)') AS extension,
                       COUNT(*) AS count
                FROM files
                WHERE status = 'active'
                GROUP BY COALESCE(NULLIF(extension, ''), '(无扩展名)')
                ORDER BY count DESC, extension
                LIMIT 20
                """
            ).fetchall()
        return [(row["extension"], int(row["count"])) for row in rows]

    def list_scan_roots(self) -> list[ScanRootRecord]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, path, created_at, last_scanned_at
                FROM scan_roots
                ORDER BY last_scanned_at DESC, path
                """
            ).fetchall()
        return [
            ScanRootRecord(
                id=row["id"],
                path=row["path"],
                created_at=row["created_at"],
                last_scanned_at=row["last_scanned_at"],
            )
            for row in rows
        ]

    def get_file(self, file_id: int) -> FileRecord:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT f.*, c.content_preview
                FROM files f
                LEFT JOIN extracted_content c ON c.file_id = f.id
                WHERE f.id = ?
                """,
                (file_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"File id {file_id} does not exist")
        return _row_to_record(row)

    def search_files(self, query: str, limit: int = 200) -> list[FileRecord]:
        like = f"%{query.strip()}%"
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT f.*, c.content_preview
                FROM files f
                LEFT JOIN extracted_content c ON c.file_id = f.id
                WHERE f.status = 'active'
                  AND (
                    f.path LIKE ?
                    OR f.name LIKE ?
                    OR COALESCE(f.category, '') LIKE ?
                    OR COALESCE(c.content_preview, '') LIKE ?
                  )
                ORDER BY f.modified_at DESC
                LIMIT ?
                """,
                (like, like, like, like, limit),
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def save_content(
        self,
        file_id: int,
        *,
        content_type: str,
        content_preview: str,
        extractor: str,
        error: str | None = None,
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO extracted_content (
                    file_id, content_type, content_preview, extractor, error
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    content_type = excluded.content_type,
                    content_preview = excluded.content_preview,
                    extractor = excluded.extractor,
                    error = excluded.error,
                    extracted_at = CURRENT_TIMESTAMP
                """,
                (file_id, content_type, content_preview, extractor, error),
            )
            connection.execute(
                "DELETE FROM file_content_fts WHERE rowid = ?",
                (file_id,),
            )
            row = connection.execute(
                "SELECT path, name, category FROM files WHERE id = ?",
                (file_id,),
            ).fetchone()
            if row:
                connection.execute(
                    """
                    INSERT INTO file_content_fts (
                        rowid, path, name, category, content_preview
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        file_id,
                        row["path"],
                        row["name"],
                        row["category"] or "",
                        content_preview,
                    ),
                )

    def save_classification(
        self,
        file_id: int,
        *,
        source: str,
        category: str,
        subcategory: str | None = None,
        suggested_name: str | None = None,
        confidence: float | None = None,
        reason: str | None = None,
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO classifications (
                    file_id, source, category, subcategory,
                    suggested_name, confidence, reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    source,
                    category,
                    subcategory,
                    suggested_name,
                    confidence,
                    reason,
                ),
            )
            connection.execute(
                "UPDATE files SET category = ? WHERE id = ?",
                (category, file_id),
            )

    def update_hashes(
        self,
        file_id: int,
        *,
        quick_hash: str | None = None,
        full_hash: str | None = None,
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE files
                SET quick_hash = COALESCE(?, quick_hash),
                    full_hash = COALESCE(?, full_hash)
                WHERE id = ?
                """,
                (quick_hash, full_hash, file_id),
            )

    def duplicate_candidates(self) -> list[FileRecord]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT f.*, c.content_preview
                FROM files f
                LEFT JOIN extracted_content c ON c.file_id = f.id
                WHERE f.status = 'active'
                  AND f.size IN (
                    SELECT size FROM files
                    WHERE status = 'active'
                    GROUP BY size HAVING COUNT(*) > 1
                  )
                ORDER BY f.size DESC, f.path
                """
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def duplicate_groups(self) -> dict[str, list[FileRecord]]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT f.*, c.content_preview
                FROM files f
                LEFT JOIN extracted_content c ON c.file_id = f.id
                WHERE f.status = 'active'
                  AND f.full_hash IS NOT NULL
                  AND f.full_hash IN (
                    SELECT full_hash FROM files
                    WHERE status = 'active' AND full_hash IS NOT NULL
                    GROUP BY full_hash HAVING COUNT(*) > 1
                  )
                ORDER BY f.full_hash, f.path
                """
            ).fetchall()
        groups: dict[str, list[FileRecord]] = {}
        for row in rows:
            record = _row_to_record(row)
            if record.full_hash:
                groups.setdefault(record.full_hash, []).append(record)
        return groups
