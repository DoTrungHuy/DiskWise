"""Persistence for semantic vectors."""

from __future__ import annotations

import json
from pathlib import Path

from diskwise.database.connection import connect


class EmbeddingRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def save(
        self,
        file_id: int,
        *,
        provider: str,
        model_name: str,
        vector: list[float],
        content_hash: str | None = None,
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO embeddings (
                    file_id, provider, model_name, vector_json, content_hash
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    provider = excluded.provider,
                    model_name = excluded.model_name,
                    vector_json = excluded.vector_json,
                    content_hash = excluded.content_hash,
                    created_at = CURRENT_TIMESTAMP
                """,
                (
                    file_id,
                    provider,
                    model_name,
                    json.dumps(vector),
                    content_hash,
                ),
            )

    def list_vectors(self) -> list[tuple[int, list[float]]]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                "SELECT file_id, vector_json FROM embeddings"
            ).fetchall()
        return [
            (int(row["file_id"]), [float(value) for value in json.loads(row["vector_json"])])
            for row in rows
        ]
