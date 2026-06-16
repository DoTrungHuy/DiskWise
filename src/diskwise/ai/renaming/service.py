"""AI-backed safe rename suggestions."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from diskwise.ai.renaming.prompts import RENAMING_SYSTEM_PROMPT, build_renaming_prompt
from diskwise.ai.schemas import AITask, GenerateRequest
from diskwise.ai.service import AIService
from diskwise.config.settings import AppSettings
from diskwise.database.repositories.file_repository import FileRepository
from diskwise.database.repositories.model_config_repository import ModelConfigRepository
from diskwise.safety.operation_validator import sanitize_filename
from diskwise.safety.path_policy import is_sensitive_for_cloud


class RenameSuggestion(BaseModel):
    suggested_name: str
    reason: str


class AIRenamingService:
    def __init__(
        self,
        database_path: Path,
        settings: AppSettings | None = None,
    ) -> None:
        self._files = FileRepository(database_path)
        self._configs = ModelConfigRepository(database_path)
        self._ai = AIService(settings or AppSettings.from_environment())

    async def suggest_name(
        self,
        file_id: int,
        *,
        cloud_consent: bool = False,
    ) -> RenameSuggestion:
        record = self._files.get_file(file_id)
        config = self._configs.get(AITask.RENAMING)
        if not config.enabled or not config.model_name:
            raise RuntimeError("智能命名模型尚未启用")
        if config.provider.value != "ollama" and is_sensitive_for_cloud(record.path):
            raise RuntimeError("敏感文件不会发送到云端 AI")

        response = await self._ai.generate(
            config.provider,
            GenerateRequest(
                model=config.model_name,
                system_prompt=RENAMING_SYSTEM_PROMPT,
                prompt=build_renaming_prompt(
                    current_name=record.name,
                    category=record.category,
                    content_preview=record.content_preview,
                ),
            ),
            cloud_consent=cloud_consent,
        )
        payload = json.loads(response.text.strip())
        suggestion = RenameSuggestion.model_validate(payload)
        safe_name = sanitize_filename(suggestion.suggested_name)
        if not safe_name:
            raise ValueError("模型返回的文件名不安全")
        return suggestion.model_copy(update={"suggested_name": safe_name})
