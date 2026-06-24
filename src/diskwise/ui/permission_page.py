"""Local permission center page."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from diskwise.permissions.service import Capability, PermissionService


class PermissionPage(QWidget):
    """Show and update DiskWise local capability permissions."""

    HEADERS = ["能力", "状态", "确认要求", "说明", "原因"]

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._permissions = PermissionService(database_path)
        self._checkboxes: dict[str, QCheckBox] = {}

        heading = QLabel("权限中心")
        heading.setObjectName("pageTitle")
        note = QLabel(
            "所有高风险能力都在本机授权。关闭云端 AI 后，DiskWise 只会使用本地模型；执行和撤销仍需要输入 EXECUTE。"
        )
        note.setWordWrap(True)
        note.setObjectName("pageNote")

        self.status_label = QLabel("等待刷新权限")
        self.save_button = QPushButton("保存权限")
        self.refresh_button = QPushButton("刷新权限")

        switches = QHBoxLayout()
        for capability in [
            Capability.SCAN_DIRECTORIES,
            Capability.EXECUTE_PLANS,
            Capability.UNDO_OPERATIONS,
            Capability.CLOUD_AI,
        ]:
            checkbox = QCheckBox()
            checkbox.setProperty("capability", capability.value)
            self._checkboxes[capability.value] = checkbox
            switches.addWidget(checkbox)
        switches.addStretch()

        controls = QHBoxLayout()
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.save_button)
        controls.addStretch()

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setObjectName("permissionTable")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addLayout(switches)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table)

        self.refresh_button.clicked.connect(self.refresh)
        self.save_button.clicked.connect(self.save)
        self.refresh()

    def refresh(self) -> None:
        snapshot = self._permissions.snapshot()
        permissions = snapshot.permissions
        label_by_capability = {permission.capability: permission.label for permission in permissions}
        for capability, checkbox in self._checkboxes.items():
            checkbox.setText(label_by_capability.get(capability, capability))

        self.table.setRowCount(len(permissions))
        for row, permission in enumerate(permissions):
            if permission.capability in self._checkboxes:
                checkbox = self._checkboxes[permission.capability]
                checkbox.blockSignals(True)
                checkbox.setChecked(permission.enabled)
                checkbox.setEnabled(not permission.locked)
                checkbox.blockSignals(False)

            status = "启用" if permission.effective_enabled else "关闭"
            confirmation = "需要 EXECUTE" if permission.requires_confirmation else "不需要"
            values = [
                permission.label,
                status,
                confirmation,
                permission.description,
                permission.reason,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()
        cloud = "启用" if snapshot.cloud_env_enabled else "未启用"
        self.status_label.setText(f"权限已刷新；云端环境变量：{cloud}")

    def save(self) -> None:
        try:
            for capability, checkbox in self._checkboxes.items():
                self._permissions.set_enabled(capability, checkbox.isChecked())
        except Exception as exc:
            self.status_label.setText(f"保存失败：{exc}")
            self.refresh()
            return
        self.refresh()
        self.status_label.setText("权限已保存")
