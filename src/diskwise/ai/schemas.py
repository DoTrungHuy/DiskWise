"""Validated data exchanged with AI providers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ProviderType(StrEnum):
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"


class AITask(StrEnum):
    CLASSIFICATION = "classification"
    RENAMING = "renaming"
    VISION = "vision"
    EMBEDDINGS = "embeddings"


class ProviderHealth(BaseModel):
    provider: ProviderType
    healthy: bool
    message: str
    version: str | None = None


class ModelInfo(BaseModel):
    name: str
    provider: ProviderType
    capabilities: list[str] = Field(default_factory=list)
    size_bytes: int | None = None
    modified_at: str | None = None


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    system_prompt: str | None = None
    images: list[str] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    model: str
    text: str


class EmbeddingRequest(BaseModel):
    model: str
    texts: list[str] = Field(min_length=1)


class EmbeddingResponse(BaseModel):
    model: str
    embeddings: list[list[float]]


class TaskModelConfig(BaseModel):
    task: AITask
    provider: ProviderType
    model_name: str | None = None
    enabled: bool = True


class ClassificationResult(BaseModel):
    file_id: int
    category: str
    suggested_name: str
    confidence: float = Field(ge=0, le=1)
    reason: str

