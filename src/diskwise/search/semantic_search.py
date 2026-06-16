"""Semantic vector search."""

from __future__ import annotations

import math
from pathlib import Path

from diskwise.ai.schemas import EmbeddingRequest, ProviderType
from diskwise.ai.service import AIService
from diskwise.config.settings import AppSettings
from diskwise.database.repositories.embedding_repository import EmbeddingRepository
from diskwise.database.repositories.file_repository import FileRecord, FileRepository


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class SemanticSearch:
    def __init__(self, database_path: Path, settings: AppSettings | None = None) -> None:
        self._files = FileRepository(database_path)
        self._embeddings = EmbeddingRepository(database_path)
        self._ai = AIService(settings or AppSettings.from_environment())

    async def search(
        self,
        query: str,
        *,
        provider: ProviderType,
        model_name: str,
        limit: int = 20,
        cloud_consent: bool = False,
    ) -> list[FileRecord]:
        response = await self._ai.embed(
            provider,
            EmbeddingRequest(model=model_name, texts=[query]),
            cloud_consent=cloud_consent,
        )
        query_vector = response.embeddings[0]
        scored = [
            (cosine_similarity(query_vector, vector), file_id)
            for file_id, vector in self._embeddings.list_vectors()
        ]
        scored.sort(reverse=True)
        records: list[FileRecord] = []
        for _, file_id in scored[:limit]:
            try:
                records.append(self._files.get_file(file_id))
            except KeyError:
                continue
        return records
