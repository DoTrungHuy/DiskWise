"""Optional OpenAI-compatible cloud provider."""

from __future__ import annotations

import httpx

from diskwise.ai.providers.base import AIProvider
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


class OpenAICompatibleProvider(AIProvider):
    """Call an explicitly enabled OpenAI-compatible HTTPS API."""

    def __init__(
        self,
        settings: AppSettings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._configured = bool(
            settings.cloud_enabled
            and settings.cloud_base_url
            and settings.cloud_api_key
        )
        token = (
            settings.cloud_api_key.get_secret_value()
            if settings.cloud_api_key
            else ""
        )
        self._client = httpx.AsyncClient(
            base_url=settings.cloud_base_url.rstrip("/") or "https://invalid.local",
            timeout=settings.request_timeout_seconds,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            transport=transport,
        )

    def _require_configured(self) -> None:
        if not self._configured:
            raise RuntimeError("云端 API 尚未显式启用或配置不完整")

    async def health_check(self) -> ProviderHealth:
        if not self._configured:
            return ProviderHealth(
                provider=ProviderType.OPENAI_COMPATIBLE,
                healthy=False,
                message="云端 API 未启用",
            )
        try:
            response = await self._client.get("/models")
            response.raise_for_status()
            return ProviderHealth(
                provider=ProviderType.OPENAI_COMPATIBLE,
                healthy=True,
                message="云端 API 可用",
            )
        except (httpx.HTTPError, ValueError) as exc:
            return ProviderHealth(
                provider=ProviderType.OPENAI_COMPATIBLE,
                healthy=False,
                message=f"云端 API 不可用：{exc}",
            )

    async def list_models(self) -> list[ModelInfo]:
        self._require_configured()
        response = await self._client.get("/models")
        response.raise_for_status()
        return [
            ModelInfo(
                name=item["id"],
                provider=ProviderType.OPENAI_COMPATIBLE,
                capabilities=["generation"],
            )
            for item in response.json().get("data", [])
            if item.get("id")
        ]

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        self._require_configured()
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        response = await self._client.post(
            "/chat/completions",
            json={"model": request.model, "messages": messages},
        )
        response.raise_for_status()
        data = response.json()
        return GenerateResponse(
            model=request.model,
            text=data["choices"][0]["message"]["content"],
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self._require_configured()
        response = await self._client.post(
            "/embeddings",
            json={"model": request.model, "input": request.texts},
        )
        response.raise_for_status()
        data = response.json()
        ordered = sorted(data["data"], key=lambda item: item["index"])
        return EmbeddingResponse(
            model=request.model,
            embeddings=[item["embedding"] for item in ordered],
        )

    async def aclose(self) -> None:
        await self._client.aclose()

