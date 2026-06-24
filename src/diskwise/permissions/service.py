"""Local-first capability permission policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from diskwise.config.settings import AppSettings
from diskwise.database.repositories.permission_repository import PermissionRepository


class Capability(StrEnum):
    SCAN_DIRECTORIES = "scan_directories"
    EXECUTE_PLANS = "execute_plans"
    UNDO_OPERATIONS = "undo_operations"
    CLOUD_AI = "cloud_ai"
    SENSITIVE_FILE_PROTECTION = "sensitive_file_protection"


@dataclass(frozen=True)
class CapabilityMetadata:
    label: str
    description: str
    requires_confirmation: bool = False
    locked: bool = False


@dataclass(frozen=True)
class CapabilityPermission:
    capability: str
    label: str
    description: str
    enabled: bool
    effective_enabled: bool
    requires_confirmation: bool
    locked: bool
    reason: str


@dataclass(frozen=True)
class PermissionSnapshot:
    permissions: list[CapabilityPermission]
    cloud_env_enabled: bool


CAPABILITY_METADATA = {
    Capability.SCAN_DIRECTORIES: CapabilityMetadata(
        label="目录扫描",
        description="允许读取用户选择的目录并建立本地文件索引。",
    ),
    Capability.EXECUTE_PLANS: CapabilityMetadata(
        label="执行整理计划",
        description="允许移动计划中的文件；执行前仍必须输入 EXECUTE。",
        requires_confirmation=True,
    ),
    Capability.UNDO_OPERATIONS: CapabilityMetadata(
        label="撤销操作",
        description="允许按操作日志撤销可逆移动；撤销前仍必须输入 EXECUTE。",
        requires_confirmation=True,
    ),
    Capability.CLOUD_AI: CapabilityMetadata(
        label="云端 AI",
        description="允许在环境变量启用后，把非敏感摘要发送到 OpenAI 兼容 API。",
    ),
    Capability.SENSITIVE_FILE_PROTECTION: CapabilityMetadata(
        label="敏感文件保护",
        description="阻止 .env、密钥文件等敏感内容发送到云端 AI。",
        locked=True,
    ),
}


class CapabilityPermissionError(PermissionError):
    """Raised when a local capability is disabled."""


class PermissionService:
    """Combine stored switches with local safety policy."""

    def __init__(
        self,
        database_path: Path,
        settings: AppSettings | None = None,
    ) -> None:
        self._repository = PermissionRepository(database_path)
        self._settings = settings or AppSettings.from_environment()

    def snapshot(self) -> PermissionSnapshot:
        records = self._repository.list_all()
        permissions: list[CapabilityPermission] = []
        for capability, metadata in CAPABILITY_METADATA.items():
            record = records.get(capability.value)
            enabled = bool(record.enabled) if record else capability is not Capability.CLOUD_AI
            effective_enabled = enabled
            reason = "已启用" if enabled else "已关闭"
            if capability is Capability.CLOUD_AI:
                effective_enabled = enabled and self._settings.cloud_enabled
                if not enabled:
                    reason = "权限中心未启用云端 AI"
                elif not self._settings.cloud_enabled:
                    reason = "环境变量 DISKWISE_CLOUD_ENABLED 未启用"
                else:
                    reason = "云端 AI 已授权"
            if metadata.locked:
                effective_enabled = True
                enabled = True
                reason = "安全保护已锁定"
            permissions.append(
                CapabilityPermission(
                    capability=capability.value,
                    label=metadata.label,
                    description=metadata.description,
                    enabled=enabled,
                    effective_enabled=effective_enabled,
                    requires_confirmation=metadata.requires_confirmation,
                    locked=metadata.locked,
                    reason=reason,
                )
            )
        return PermissionSnapshot(
            permissions=permissions,
            cloud_env_enabled=self._settings.cloud_enabled,
        )

    def set_enabled(self, capability: str | Capability, enabled: bool) -> PermissionSnapshot:
        normalized = Capability(capability)
        metadata = CAPABILITY_METADATA[normalized]
        if metadata.locked and not enabled:
            raise CapabilityPermissionError(f"{metadata.label} 是锁定的安全能力，不能关闭")
        self._repository.set_enabled(normalized.value, enabled)
        return self.snapshot()

    def assert_enabled(self, capability: str | Capability) -> None:
        normalized = Capability(capability)
        permission = self._permission(normalized)
        if not permission.effective_enabled:
            raise CapabilityPermissionError(permission.reason)

    def assert_cloud_ai_allowed(self) -> None:
        self.assert_enabled(Capability.CLOUD_AI)

    def _permission(self, capability: Capability) -> CapabilityPermission:
        for permission in self.snapshot().permissions:
            if permission.capability == capability.value:
                return permission
        raise CapabilityPermissionError(f"未知能力：{capability.value}")
