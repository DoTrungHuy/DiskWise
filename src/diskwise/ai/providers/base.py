"""Common AI provider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from diskwise.ai.schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderHealth,
)


class AIProvider(ABC):
    """Interface implemented by every local or cloud provider."""

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        raise NotImplementedError

    @abstractmethod
    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        raise NotImplementedError

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise NotImplementedError

    @abstractmethod
    async def aclose(self) -> None:
        raise NotImplementedError

