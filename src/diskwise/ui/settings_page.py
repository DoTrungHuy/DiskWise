"""Model provider discovery and per-task selection page."""

from __future__ import annotations

import asyncio
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from diskwise.ai.providers.factory import create_provider
from diskwise.ai.schemas import AITask, ProviderType, TaskModelConfig
from diskwise.config.settings import AppSettings
from diskwise.database.repositories.model_config_repository import (
    ModelConfigRepository,
)


TASK_LABELS = {
    AITask.CLASSIFICATION: "文件分类",
    AITask.RENAMING: "智能命名",
    AITask.VISION: "图片理解",
    AITask.EMBEDDINGS: "语义搜索",
}


class ModelDiscoveryWorker(QThread):
    """Run provider network checks outside the GUI thread."""

    result_ready = Signal(object, object)
    failed = Signal(str)

    def __init__(
        self,
        provider_type: ProviderType,
        settings: AppSettings,
    ) -> None:
        super().__init__()
        self._provider_type = provider_type
        self._settings = settings

    def run(self) -> None:
        async def discover() -> tuple[object, object]:
            provider = create_provider(self._provider_type, self._settings)
            try:
                health = await provider.health_check()
                models = await provider.list_models() if health.healthy else []
                return health, models
            finally:
                await provider.aclose()

        try:
            health, models = asyncio.run(discover())
            self.result_ready.emit(health, models)
        except Exception as exc:
            self.failed.emit(str(exc))


class SettingsPage(QWidget):
    """Configure task-specific providers without storing API keys."""

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._settings = AppSettings.from_environment()
        self._repository = ModelConfigRepository(database_path)
        self._worker: ModelDiscoveryWorker | None = None

        heading = QLabel("AI 模型设置")
        heading.setObjectName("pageTitle")
        note = QLabel(
            "本地 Ollama 优先。云端 API 必须通过环境变量显式启用，"
            "程序不会自动将本地内容发送到云端。"
        )
        note.setWordWrap(True)
        note.setObjectName("pageNote")

        self.task_combo = QComboBox()
        for task, label in TASK_LABELS.items():
            self.task_combo.addItem(label, task)

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("本地 Ollama", ProviderType.OLLAMA)
        self.provider_combo.addItem(
            "OpenAI 兼容云端 API",
            ProviderType.OPENAI_COMPATIBLE,
        )

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.enabled_checkbox = QCheckBox("为此任务启用 AI")
        self.status_label = QLabel("尚未检测模型服务")

        self.refresh_button = QPushButton("检测并刷新模型")
        self.save_button = QPushButton("保存任务配置")

        form = QFormLayout()
        form.addRow("任务", self.task_combo)
        form.addRow("服务提供者", self.provider_combo)
        form.addRow("模型", self.model_combo)
        form.addRow("", self.enabled_checkbox)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.save_button)
        buttons.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.task_combo.currentIndexChanged.connect(self._load_task)
        self.refresh_button.clicked.connect(self.refresh_models)
        self.save_button.clicked.connect(self.save_task)
        self._load_task()

    def _current_task(self) -> AITask:
        return AITask(self.task_combo.currentData())

    def _current_provider(self) -> ProviderType:
        return ProviderType(self.provider_combo.currentData())

    def _load_task(self) -> None:
        config = self._repository.get(self._current_task())
        provider_index = self.provider_combo.findData(config.provider)
        self.provider_combo.setCurrentIndex(max(provider_index, 0))
        self.model_combo.setCurrentText(config.model_name or "")
        self.enabled_checkbox.setChecked(config.enabled)

    def save_task(self) -> None:
        model_name = self.model_combo.currentText().strip() or None
        config = TaskModelConfig(
            task=self._current_task(),
            provider=self._current_provider(),
            model_name=model_name,
            enabled=self.enabled_checkbox.isChecked(),
        )
        self._repository.save(config)
        self.status_label.setText("任务模型配置已保存")

    def refresh_models(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self.status_label.setText("正在检测模型服务...")
        self._worker = ModelDiscoveryWorker(
            self._current_provider(),
            self._settings,
        )
        self._worker.result_ready.connect(self._on_models_ready)
        self._worker.failed.connect(self._on_discovery_failed)
        self._worker.finished.connect(
            lambda: self.refresh_button.setEnabled(True)
        )
        self._worker.start()

    def _on_models_ready(self, health: object, models: object) -> None:
        current = self.model_combo.currentText()
        self.model_combo.clear()
        for model in models:
            self.model_combo.addItem(model.name)
        if current:
            self.model_combo.setCurrentText(current)
        self.status_label.setText(health.message)

    def _on_discovery_failed(self, message: str) -> None:
        self.status_label.setText(f"模型检测失败：{message}")
