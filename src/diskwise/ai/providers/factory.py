"""Provider construction from application settings."""

from __future__ import annotations

from diskwise.ai.providers.base import AIProvider
from diskwise.ai.providers.ollama_provider import OllamaProvider
from diskwise.ai.providers.openai_compatible_provider import (
    OpenAICompatibleProvider,
)
from diskwise.ai.schemas import ProviderType
from diskwise.config.settings import AppSettings


def create_provider(
    provider_type: ProviderType,
    settings: AppSettings,
) -> AIProvider:
    if provider_type is ProviderType.OLLAMA:
        return OllamaProvider(settings)
    if provider_type is ProviderType.OPENAI_COMPATIBLE:
        return OpenAICompatibleProvider(settings)
    raise ValueError(f"Unsupported provider: {provider_type}")

