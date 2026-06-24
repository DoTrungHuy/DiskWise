"""AI task workbench page."""

from __future__ import annotations

import asyncio
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from diskwise.ai.classification.service import AIClassificationService
from diskwise.ai.renaming.service import AIRenamingService
from diskwise.ai.schemas import ProviderType
from diskwise.ai.service import AIService
from diskwise.config.settings import AppSettings
from diskwise.database.repositories.file_repository import FileRepository
from diskwise.database.repositories.model_config_repository import ModelConfigRepository


class AIActionWorker(QThread):
    """Run AI tasks outside the GUI thread."""

    result_ready = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        database_path: Path,
        action: str,
        file_id: int,
        cloud_consent: bool,
    ) -> None:
        super().__init__()
        self._database_path = database_path
        self._action = action
        self._file_id = file_id
        self._cloud_consent = cloud_consent

    def run(self) -> None:
        try:
            if self._action == "classify":
                result = asyncio.run(
                    AIClassificationService(self._database_path).classify_file(
                        self._file_id,
                        cloud_consent=self._cloud_consent,
                    )
                )
                self.result_ready.emit(
                    f"分类：{result.category}，建议名称：{result.suggested_name}，置信度：{result.confidence:.2f}\n{result.reason}"
                )
                return
            result = asyncio.run(
                AIRenamingService(self._database_path).suggest_name(
                    self._file_id,
                    cloud_consent=self._cloud_consent,
                )
            )
            self.result_ready.emit(f"建议名称：{result.suggested_name}\n{result.reason}")
        except Exception as exc:
            self.failed.emit(str(exc))


class AIHealthWorker(QThread):
    """Check provider health outside the GUI thread."""

    result_ready = Signal(object)
    failed = Signal(str)

    def run(self) -> None:
        async def check() -> list[str]:
            service = AIService(AppSettings.from_environment())
            messages: list[str] = []
            for provider in ProviderType:
                try:
                    health = await service.health_check(provider)
                    prefix = "可用" if health.healthy else "不可用"
                    messages.append(f"{provider.value}: {prefix} - {health.message}")
                except Exception as exc:
                    messages.append(f"{provider.value}: 不可用 - {exc}")
            return messages

        try:
            self.result_ready.emit(asyncio.run(check()))
        except Exception as exc:
            self.failed.emit(str(exc))


class AIPage(QWidget):
    """Run local-first AI tasks for indexed files."""

    HEADERS = ["任务", "服务", "模型", "状态"]

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._database_path = database_path
        self._files = FileRepository(database_path)
        self._models = ModelConfigRepository(database_path)
        self._worker: AIActionWorker | AIHealthWorker | None = None

        heading = QLabel("AI 工作台")
        heading.setObjectName("pageTitle")
        note = QLabel(
            "对资料库中的文件执行 AI 分类和安全命名建议。默认使用本地模型；云端调用必须先在权限页授权。"
        )
        note.setWordWrap(True)
        note.setObjectName("pageNote")

        self.file_combo = QComboBox()
        self.cloud_checkbox = QCheckBox("本次允许云端 AI")
        self.status_label = QLabel("等待选择文件")
        self.result_label = QLabel("暂无 AI 结果")
        self.result_label.setWordWrap(True)

        self.refresh_button = QPushButton("刷新文件")
        self.health_button = QPushButton("检测模型服务")
        self.classify_button = QPushButton("AI 分类")
        self.rename_button = QPushButton("生成命名建议")

        controls = QHBoxLayout()
        controls.addWidget(self.file_combo, 1)
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.health_button)
        controls.addWidget(self.classify_button)
        controls.addWidget(self.rename_button)

        self.model_table = QTableWidget(0, len(self.HEADERS))
        self.model_table.setHorizontalHeaderLabels(self.HEADERS)
        self.model_table.setObjectName("aiModelTable")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addLayout(controls)
        layout.addWidget(self.cloud_checkbox)
        layout.addWidget(self.status_label)
        layout.addWidget(self.result_label)
        layout.addWidget(self.model_table)

        self.refresh_button.clicked.connect(self.refresh)
        self.health_button.clicked.connect(self.check_health)
        self.classify_button.clicked.connect(lambda: self._run_action("classify"))
        self.rename_button.clicked.connect(lambda: self._run_action("rename"))

        self.refresh()

    def refresh(self) -> None:
        self.file_combo.clear()
        for record in self._files.list_files(limit=300):
            self.file_combo.addItem(f"{record.name} - {record.path}", record.id)
        self._populate_models()
        enabled = self.file_combo.count() > 0
        self.classify_button.setEnabled(enabled)
        self.rename_button.setEnabled(enabled)
        self.status_label.setText("请选择文件执行 AI 任务" if enabled else "资料库暂无文件")

    def check_health(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._set_busy(True, "正在检测模型服务...")
        self._worker = AIHealthWorker()
        self._worker.result_ready.connect(self._on_health_ready)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _run_action(self, action: str) -> None:
        file_id = self.file_combo.currentData()
        if file_id is None or (self._worker and self._worker.isRunning()):
            return
        self._set_busy(True, "正在运行 AI 任务...")
        self._worker = AIActionWorker(
            self._database_path,
            action,
            int(file_id),
            self.cloud_checkbox.isChecked(),
        )
        self._worker.result_ready.connect(self._on_result_ready)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _populate_models(self) -> None:
        configs = self._models.list_all()
        self.model_table.setRowCount(len(configs))
        labels = {
            "classification": "文件分类",
            "renaming": "智能命名",
            "vision": "图片理解",
            "embeddings": "语义搜索",
        }
        for row, config in enumerate(configs):
            values = [
                labels.get(config.task.value, config.task.value),
                config.provider.value,
                config.model_name or "未选择",
                "启用" if config.enabled else "关闭",
            ]
            for column, value in enumerate(values):
                self.model_table.setItem(row, column, QTableWidgetItem(value))
        self.model_table.resizeColumnsToContents()

    def _set_busy(self, busy: bool, message: str | None = None) -> None:
        self.refresh_button.setEnabled(not busy)
        self.health_button.setEnabled(not busy)
        has_files = self.file_combo.count() > 0
        self.classify_button.setEnabled(not busy and has_files)
        self.rename_button.setEnabled(not busy and has_files)
        if message:
            self.status_label.setText(message)

    def _on_result_ready(self, message: str) -> None:
        self.result_label.setText(message)
        self.status_label.setText("AI 任务完成")
        self.refresh()

    def _on_health_ready(self, messages: object) -> None:
        self.result_label.setText("\n".join(str(message) for message in messages))
        self.status_label.setText("模型服务检测完成")

    def _on_failed(self, message: str) -> None:
        self.status_label.setText(f"AI 任务失败：{message}")
