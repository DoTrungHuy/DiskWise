"""AI-backed file classification."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from diskwise.ai.classification.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    build_classification_prompt,
)
from diskwise.ai.schemas import (
    AITask,
    ClassificationResult,
    GenerateRequest,
    ProviderType,
)
from diskwise.ai.service import AIService
from diskwise.config.settings import AppSettings
from diskwise.database.repositories.file_repository import FileRepository
from diskwise.database.repositories.model_config_repository import ModelConfigRepository
from diskwise.permissions.service import PermissionService
from diskwise.safety.operation_validator import sanitize_filename
from diskwise.safety.path_policy import is_sensitive_for_cloud


DEFAULT_CATEGORIES = [
    "安装包",
    "系统镜像",
    "压缩包",
    "图片",
    "视频",
    "音频",
    "文档",
    "PDF",
    "表格",
    "演示文稿",
    "代码",
    "脚本",
    "课程资料",
    "工作文档",
    "其他",
]


class AIClassificationService:
    def __init__(
        self,
        database_path: Path,
        settings: AppSettings | None = None,
    ) -> None:
        self._files = FileRepository(database_path)
        self._configs = ModelConfigRepository(database_path)
        self._settings = settings or AppSettings.from_environment()
        self._ai = AIService(self._settings)
        self._permissions = PermissionService(database_path, self._settings)

    async def classify_file(
        self,
        file_id: int,
        *,
        cloud_consent: bool = False,
        categories: list[str] | None = None,
    ) -> ClassificationResult:
        record = self._files.get_file(file_id)
        config = self._configs.get(AITask.CLASSIFICATION)
        if not config.enabled or not config.model_name:
            raise RuntimeError("文件分类模型尚未启用")
        if config.provider is not ProviderType.OLLAMA:
            self._permissions.assert_cloud_ai_allowed()
            if is_sensitive_for_cloud(record.path):
                raise RuntimeError("敏感文件不会发送到云端 AI")

        prompt = build_classification_prompt(
            file_id=record.id,
            name=record.name,
            extension=record.extension,
            size=record.size,
            content_preview=record.content_preview,
            available_categories=categories or DEFAULT_CATEGORIES,
        )
        response = await self._ai.generate(
            config.provider,
            GenerateRequest(
                model=config.model_name,
                system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
                prompt=prompt,
            ),
            cloud_consent=cloud_consent,
        )
        result = self._parse_response(response.text)
        safe_name = sanitize_filename(result.suggested_name)
        if safe_name:
            result = result.model_copy(update={"suggested_name": safe_name})
        self._files.save_classification(
            file_id,
            source=f"ai:{config.provider.value}:{config.model_name}",
            category=result.category,
            suggested_name=result.suggested_name,
            confidence=result.confidence,
            reason=result.reason,
        )
        return result

    def _parse_response(self, text: str) -> ClassificationResult:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
        try:
            payload = json.loads(cleaned)
            return ClassificationResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"模型没有返回合法分类 JSON：{exc}") from exc
