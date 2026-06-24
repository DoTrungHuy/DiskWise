"""Operation activity and undo page."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from diskwise.planner.execution_service import CONFIRMATION_TEXT, PlanExecutionService


class ActivityPage(QWidget):
    HEADERS = ["ID", "动作", "原路径", "目标路径", "状态", "时间"]

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._execution = PlanExecutionService(database_path)

        heading = QLabel("活动与撤销")
        heading.setObjectName("pageTitle")
        note = QLabel(
            "所有通过计划执行的移动都会记录在这里。可逆操作需要再次输入 EXECUTE 才能撤销。"
        )
        note.setWordWrap(True)
        note.setObjectName("pageNote")

        self.refresh_button = QPushButton("刷新日志")
        self.undo_button = QPushButton("撤销所选操作")
        self.undo_button.setEnabled(False)
        self.status_label = QLabel("等待操作")

        controls = QHBoxLayout()
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.undo_button)
        controls.addStretch()

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setObjectName("activityTable")
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table)

        self.refresh_button.clicked.connect(self.refresh)
        self.undo_button.clicked.connect(self.undo_selected_operation)
        self.table.itemSelectionChanged.connect(self._update_undo_state)

        self.refresh()

    def refresh(self) -> None:
        operations = self._execution.list_operations(limit=100)
        self.table.setRowCount(len(operations))
        for row, operation in enumerate(operations):
            values = [
                str(operation.id),
                operation.action,
                operation.source_path,
                operation.target_path or "",
                operation.status,
                operation.created_at,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, operation.id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, _can_undo(operation))
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()
        self.status_label.setText(f"共 {len(operations)} 条操作记录")
        self._update_undo_state()

    def undo_selected_operation(self) -> None:
        operation_id = self._selected_operation_id()
        if operation_id is None:
            return
        confirmation, ok = QInputDialog.getText(
            self,
            "确认撤销",
            f"输入 {CONFIRMATION_TEXT} 后撤销所选操作：",
        )
        if not ok:
            return
        if confirmation != CONFIRMATION_TEXT:
            self.status_label.setText("确认文本不匹配，未执行撤销")
            return
        try:
            result = self._execution.undo_operation(
                operation_id,
                confirmation=confirmation,
            )
        except Exception as exc:
            QMessageBox.warning(self, "撤销失败", str(exc))
            self.status_label.setText(f"撤销失败：{exc}")
            return
        self.status_label.setText(
            f"撤销完成：{result.source_path} -> {result.target_path}"
        )
        self.refresh()

    def _selected_operation_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        if item is None:
            return None
        return int(item.data(Qt.ItemDataRole.UserRole))

    def _update_undo_state(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.undo_button.setEnabled(False)
            return
        item = self.table.item(rows[0].row(), 0)
        self.undo_button.setEnabled(bool(item and item.data(Qt.ItemDataRole.UserRole + 1)))


def _can_undo(operation: object) -> bool:
    return (
        getattr(operation, "status", "") == "succeeded"
        and getattr(operation, "action", "") in {"move", "rename"}
        and bool(getattr(operation, "undo_data", None))
    )
