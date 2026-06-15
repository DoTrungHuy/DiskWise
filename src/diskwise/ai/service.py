"""High-level AI service with explicit provider selection."""

from __future__ import annotations

from diskwise.ai.providers.factory import create_provider
from diskwise.ai.schemas import (
    EmbeddingRequest,
    EmbeddingResponse,
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ProviderHealth,
    ProviderType,
)
from diskwise.config.settings import AppSettings
from diskwise.safety.privacy_policy import require_cloud_consent


class AIService:
    """Use one selected provider without automatic cloud fallback."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    async def health_check(self, provider_type: ProviderType) -> ProviderHealth:
        provider = create_provider(provider_type, self._settings)
        try:
            return await provider.health_check()
        finally:
            await provider.aclose()

    async def list_models(self, provider_type: ProviderType) -> list[ModelInfo]:
        provider = create_provider(provider_type, self._settings)
        try:
            return await provider.list_models()
        finally:
            await provider.aclose()

    async def generate(
        self,
        provider_type: ProviderType,
        request: GenerateRequest,
        *,
        cloud_consent: bool = False,
    ) -> GenerateResponse:
        require_cloud_consent(provider_type, cloud_consent)
        provider = create_provider(provider_type, self._settings)
        try:
            return await provider.generate(request)
        finally:
            await provider.aclose()

    async def embed(
        self,
        provider_type: ProviderType,
        request: EmbeddingRequest,
        *,
        cloud_consent: bool = False,
    ) -> EmbeddingResponse:
        require_cloud_consent(provider_type, cloud_consent)
        provider = create_provider(provider_type, self._settings)
        try:
            return await provider.embed(request)
        finally:
            await provider.aclose()

