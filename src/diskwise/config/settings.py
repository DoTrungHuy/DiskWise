"""Environment-backed application settings."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field, SecretStr


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AppSettings(BaseModel):
    """Configuration that is safe to pass to service constructors."""

    ollama_base_url: str = "http://localhost:11434"
    default_text_model: str = "gemma4:e2b"
    cloud_enabled: bool = False
    cloud_base_url: str = ""
    cloud_api_key: SecretStr | None = None
    request_timeout_seconds: float = Field(default=10.0, gt=0)

    @classmethod
    def from_environment(cls) -> "AppSettings":
        """Build settings from environment variables."""
        raw_key = os.getenv("DISKWISE_CLOUD_API_KEY")
        return cls(
            ollama_base_url=os.getenv(
                "DISKWISE_OLLAMA_BASE_URL", "http://localhost:11434"
            ),
            default_text_model=os.getenv(
                "DISKWISE_DEFAULT_TEXT_MODEL", "gemma4:e2b"
            ),
            cloud_enabled=_env_bool("DISKWISE_CLOUD_ENABLED"),
            cloud_base_url=os.getenv("DISKWISE_CLOUD_BASE_URL", ""),
            cloud_api_key=SecretStr(raw_key) if raw_key else None,
        )

