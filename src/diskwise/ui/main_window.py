"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QTabWidget

from diskwise.ui.plan_page import PlanPage
from diskwise.ui.scan_page import ScanPage
from diskwise.ui.search_page import SearchPage
from diskwise.ui.settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.setWindowTitle("DiskWise")
        self.resize(1120, 760)

        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")
        tabs.addTab(ScanPage(database_path), "扫描")
        tabs.addTab(SearchPage(database_path), "搜索")
        tabs.addTab(PlanPage(database_path), "计划")
        tabs.addTab(SettingsPage(database_path), "设置")
        self.setCentralWidget(tabs)
