"""Local Ollama provider with model discovery."""

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


def _infer_capabilities(model_name: str) -> list[str]:
    name = model_name.lower()
    if "embed" in name:
        return ["embeddings"]
    return ["generation"]


class OllamaProvider(AIProvider):
    """Call models managed by a locally running Ollama service."""

    def __init__(
        self,
        settings: AppSettings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.ollama_base_url.rstrip("/"),
            timeout=settings.request_timeout_seconds,
            transport=transport,
            trust_env=False,
        )

    async def health_check(self) -> ProviderHealth:
        try:
            response = await self._client.get("/api/version")
            response.raise_for_status()
            version = response.json().get("version")
            return ProviderHealth(
                provider=ProviderType.OLLAMA,
                healthy=True,
                message="Ollama 正在运行",
                version=version,
            )
        except (httpx.HTTPError, ValueError) as exc:
            return ProviderHealth(
                provider=ProviderType.OLLAMA,
                healthy=False,
                message=f"无法连接 Ollama：{exc}",
            )

    async def list_models(self) -> list[ModelInfo]:
        response = await self._client.get("/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        return [
            ModelInfo(
                name=item.get("name") or item.get("model"),
                provider=ProviderType.OLLAMA,
                capabilities=_infer_capabilities(
                    item.get("name") or item.get("model") or ""
                ),
                size_bytes=item.get("size"),
                modified_at=item.get("modified_at"),
            )
            for item in models
            if item.get("name") or item.get("model")
        ]

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        payload: dict[str, object] = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
        }
        if request.system_prompt:
            payload["system"] = request.system_prompt
        if request.images:
            payload["images"] = request.images
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return GenerateResponse(model=request.model, text=data["response"])

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        response = await self._client.post(
            "/api/embed",
            json={"model": request.model, "input": request.texts},
        )
        response.raise_for_status()
        data = response.json()
        return EmbeddingResponse(
            model=request.model,
            embeddings=data["embeddings"],
        )

    async def aclose(self) -> None:
        await self._client.aclose()
