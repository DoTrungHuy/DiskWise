"""Desktop workbench dashboard."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from diskwise.database.repositories.file_repository import FileRepository
from diskwise.database.repositories.model_config_repository import ModelConfigRepository
from diskwise.database.repositories.plan_repository import PlanRepository


class MetricCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricTitle")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("metricValue")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: object) -> None:
        self.value_label.setText(str(value))


class DashboardPage(QWidget):
    """At-a-glance state for the stable PySide6 shell."""

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._database_path = database_path
        self._files = FileRepository(database_path)
        self._plans = PlanRepository(database_path)
        self._models = ModelConfigRepository(database_path)

        heading = QLabel("DiskWise 工作台")
        heading.setObjectName("pageTitle")
        note = QLabel(
            "桌面版仍然是主入口。这里集中显示扫描、资料库、重复文件、计划和 AI 配置状态。"
        )
        note.setWordWrap(True)
        note.setObjectName("pageNote")

        self.refresh_button = QPushButton("刷新状态")
        self.refresh_button.clicked.connect(self.refresh)

        header = QHBoxLayout()
        header.addWidget(heading)
        header.addStretch()
        header.addWidget(self.refresh_button)

        self.files_card = MetricCard("已索引文件")
        self.roots_card = MetricCard("扫描目录")
        self.duplicates_card = MetricCard("已知重复组")
        self.ai_card = MetricCard("启用 AI 任务")

        cards = QGridLayout()
        cards.setSpacing(14)
        cards.addWidget(self.files_card, 0, 0)
        cards.addWidget(self.roots_card, 0, 1)
        cards.addWidget(self.duplicates_card, 0, 2)
        cards.addWidget(self.ai_card, 0, 3)

        self.scan_roots_label = QLabel()
        self.scan_roots_label.setWordWrap(True)
        self.categories_label = QLabel()
        self.categories_label.setWordWrap(True)
        self.latest_plan_label = QLabel()
        self.latest_plan_label.setWordWrap(True)

        detail_grid = QGridLayout()
        detail_grid.setSpacing(14)
        detail_grid.addWidget(self._panel("最近扫描目录", self.scan_roots_label), 0, 0)
        detail_grid.addWidget(self._panel("分类分布", self.categories_label), 0, 1)
        detail_grid.addWidget(self._panel("最新计划", self.latest_plan_label), 1, 0, 1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        layout.addLayout(header)
        layout.addWidget(note)
        layout.addLayout(cards)
        layout.addLayout(detail_grid)
        layout.addStretch()

        self.refresh()

    def refresh(self) -> None:
        roots = self._files.list_scan_roots()
        categories = self._files.category_counts()
        latest_plans = self._plans.list_latest(limit=1)
        duplicate_groups = self._files.duplicate_groups()
        enabled_ai = sum(1 for config in self._models.list_all() if config.enabled)

        self.files_card.set_value(self._files.count_files())
        self.roots_card.set_value(len(roots))
        self.duplicates_card.set_value(len(duplicate_groups))
        self.ai_card.set_value(enabled_ai)

        if roots:
            self.scan_roots_label.setText(
                "\n".join(f"{root.path}\n  {root.last_scanned_at or '尚未扫描'}" for root in roots[:5])
            )
        else:
            self.scan_roots_label.setText("尚未扫描任何目录")

        if categories:
            self.categories_label.setText(
                "\n".join(f"{category}: {count}" for category, count in categories[:8])
            )
        else:
            self.categories_label.setText("暂无分类数据")

        if latest_plans:
            plan = latest_plans[0]
            self.latest_plan_label.setText(
                f"#{plan.id} {plan.title} - {plan.status}，共 {len(plan.items)} 项"
            )
        else:
            self.latest_plan_label.setText("暂无计划")

    def _panel(self, title: str, body: QLabel) -> QFrame:
        panel = QFrame()
        panel.setObjectName("infoPanel")
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(title_label)
        layout.addWidget(body)
        return panel
