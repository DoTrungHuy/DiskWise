import asyncio

import httpx

from diskwise.ai.providers.ollama_provider import OllamaProvider
from diskwise.config.settings import AppSettings


def test_ollama_health_and_multiple_model_discovery():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "test"})
        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "gemma4:e2b", "size": 100},
                        {"name": "embeddinggemma:latest", "size": 50},
                    ]
                },
            )
        return httpx.Response(404)

    async def scenario():
        provider = OllamaProvider(
            AppSettings(),
            transport=httpx.MockTransport(handler),
        )
        try:
            health = await provider.health_check()
            models = await provider.list_models()
        finally:
            await provider.aclose()
        return health, models

    health, models = asyncio.run(scenario())
    assert health.healthy is True
    assert [model.name for model in models] == [
        "gemma4:e2b",
        "embeddinggemma:latest",
    ]
    assert models[1].capabilities == ["embeddings"]


def test_ollama_connection_error_is_friendly():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async def scenario():
        provider = OllamaProvider(
            AppSettings(),
            transport=httpx.MockTransport(handler),
        )
        try:
            return await provider.health_check()
        finally:
            await provider.aclose()

    health = asyncio.run(scenario())
    assert health.healthy is False
    assert "无法连接 Ollama" in health.message

