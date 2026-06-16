"""Organization plan preview page."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from diskwise.planner.plan_service import PlanService


class PlanPage(QWidget):
    HEADERS = ["动作", "分类", "原路径", "目标路径", "原因"]

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._plans = PlanService(database_path)
        self._target_root: Path | None = None

        heading = QLabel("整理计划")
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        note = QLabel(
            "这里先生成移动建议预览。计划写入 SQLite，但不会自动执行；"
            "真正移动文件必须经过单独确认。"
        )
        note.setWordWrap(True)

        self.target_label = QLabel("尚未选择目标文件夹")
        self.status_label = QLabel("等待生成计划")
        self.choose_button = QPushButton("选择整理目标文件夹")
        self.generate_button = QPushButton("生成分类整理计划")
        self.generate_button.setEnabled(False)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setObjectName("planPreviewTable")

        controls = QHBoxLayout()
        controls.addWidget(self.choose_button)
        controls.addWidget(self.generate_button)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addWidget(self.target_label)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table)

        self.choose_button.clicked.connect(self.choose_target)
        self.generate_button.clicked.connect(self.generate_plan)

    def choose_target(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择整理目标文件夹")
        if not folder:
            return
        self._target_root = Path(folder)
        self.target_label.setText(str(self._target_root))
        self.generate_button.setEnabled(True)

    def generate_plan(self) -> None:
        if self._target_root is None:
            return
        try:
            plan_id, suggestions = self._plans.generate_category_plan(self._target_root)
        except Exception as exc:
            QMessageBox.warning(self, "计划生成失败", str(exc))
            self.status_label.setText(f"计划生成失败：{exc}")
            return
        self.table.setRowCount(len(suggestions))
        for row, suggestion in enumerate(suggestions):
            values = [
                suggestion.action,
                suggestion.category or "其他",
                suggestion.source_path,
                suggestion.target_path,
                suggestion.reason,
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.status_label.setText(f"计划 #{plan_id} 已生成，共 {len(suggestions)} 项")
