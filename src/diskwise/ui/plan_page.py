"""Organization plan preview page."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
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

from diskwise.database.repositories.plan_repository import PlanRecord, PlanRepository
from diskwise.planner.execution_service import CONFIRMATION_TEXT, PlanExecutionService
from diskwise.planner.plan_service import PlanService


class PlanPage(QWidget):
    HEADERS = ["选择", "动作", "分类", "原路径", "目标路径", "风险", "状态", "原因"]

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._database_path = database_path
        self._plans = PlanService(database_path)
        self._plan_repository = PlanRepository(database_path)
        self._execution = PlanExecutionService(database_path)
        self._target_root: Path | None = None
        self._current_plan_id: int | None = None

        heading = QLabel("整理计划")
        heading.setObjectName("pageTitle")
        note = QLabel(
            "先生成移动建议，再逐项勾选并输入 EXECUTE 才能执行。"
            "计划执行会重新检查源文件状态，并在活动页记录可撤销操作。"
        )
        note.setWordWrap(True)
        note.setObjectName("pageNote")

        self.target_label = QLabel("尚未选择目标文件夹")
        self.status_label = QLabel("等待生成计划")
        self.choose_button = QPushButton("选择整理目标文件夹")
        self.generate_button = QPushButton("生成分类整理计划")
        self.refresh_button = QPushButton("载入最新计划")
        self.execute_button = QPushButton("执行勾选项")
        self.generate_button.setEnabled(False)
        self.execute_button.setEnabled(False)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setObjectName("planPreviewTable")
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        controls = QHBoxLayout()
        controls.addWidget(self.choose_button)
        controls.addWidget(self.generate_button)
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.execute_button)
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
        self.refresh_button.clicked.connect(self.load_latest_plan)
        self.execute_button.clicked.connect(self.execute_checked_items)

        self.load_latest_plan()

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
        self._current_plan_id = plan_id
        self._populate_plan(self._plan_repository.get_plan(plan_id))
        self.status_label.setText(f"计划 #{plan_id} 已生成，共 {len(suggestions)} 项")

    def load_latest_plan(self) -> None:
        latest = self._plan_repository.list_latest(limit=1)
        if not latest:
            self._current_plan_id = None
            self.table.setRowCount(0)
            self.execute_button.setEnabled(False)
            self.status_label.setText("暂无计划")
            return
        plan = latest[0]
        self._current_plan_id = plan.id
        self._populate_plan(plan)
        self.status_label.setText(f"已载入计划 #{plan.id}：{len(plan.items)} 项")

    def execute_checked_items(self) -> None:
        if self._current_plan_id is None:
            return
        selected_item_ids = self._checked_item_ids()
        if not selected_item_ids:
            self.status_label.setText("请先勾选至少一个待执行项目")
            return
        confirmation, ok = QInputDialog.getText(
            self,
            "确认执行",
            f"输入 {CONFIRMATION_TEXT} 后执行 {len(selected_item_ids)} 个项目：",
        )
        if not ok:
            return
        if confirmation != CONFIRMATION_TEXT:
            self.status_label.setText("确认文本不匹配，未执行计划")
            return
        try:
            results = self._execution.execute_plan(
                self._current_plan_id,
                selected_item_ids=selected_item_ids,
                confirmation=confirmation,
            )
        except Exception as exc:
            QMessageBox.warning(self, "执行失败", str(exc))
            self.status_label.setText(f"执行失败：{exc}")
            return
        succeeded = sum(1 for result in results if result.status == "succeeded")
        failed = len(results) - succeeded
        self._populate_plan(self._plan_repository.get_plan(self._current_plan_id))
        self.status_label.setText(f"执行完成：成功 {succeeded} 项，失败 {failed} 项")

    def _populate_plan(self, plan: PlanRecord) -> None:
        self.table.setRowCount(len(plan.items))
        pending_count = 0
        for row, item in enumerate(plan.items):
            pending = item.status == "pending"
            pending_count += int(pending)
            check_item = QTableWidgetItem("")
            check_item.setData(Qt.ItemDataRole.UserRole, item.id)
            check_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsSelectable
            )
            check_item.setCheckState(
                Qt.CheckState.Checked if pending else Qt.CheckState.Unchecked
            )
            self.table.setItem(row, 0, check_item)

            risk = self._risk_text(item.source_path, item.target_path)
            values = [
                item.action,
                item.category or "其他",
                item.source_path,
                item.target_path,
                risk,
                item.status,
                item.reason or "",
            ]
            for offset, value in enumerate(values, start=1):
                cell = QTableWidgetItem(value)
                if not pending:
                    cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, offset, cell)
        self.table.resizeColumnsToContents()
        self.execute_button.setEnabled(pending_count > 0)

    def _checked_item_ids(self) -> list[int]:
        item_ids: list[int] = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            status = self.table.item(row, 6)
            if (
                item is not None
                and status is not None
                and item.checkState() == Qt.CheckState.Checked
                and status.text() == "pending"
            ):
                item_ids.append(int(item.data(Qt.ItemDataRole.UserRole)))
        return item_ids

    def _risk_text(self, source_path: str, target_path: str) -> str:
        source = Path(source_path)
        target = Path(target_path)
        risks: list[str] = []
        if not source.exists():
            risks.append("源文件缺失")
        if target.exists():
            risks.append("目标冲突")
        return "、".join(risks) if risks else "可执行"
