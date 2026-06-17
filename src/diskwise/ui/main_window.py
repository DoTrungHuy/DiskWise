"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QTabWidget

from diskwise.ui.activity_page import ActivityPage
from diskwise.ui.dashboard_page import DashboardPage
from diskwise.ui.plan_page import PlanPage
from diskwise.ui.scan_page import ScanPage
from diskwise.ui.search_page import SearchPage
from diskwise.ui.settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.setWindowTitle("DiskWise")
        self.resize(1280, 820)

        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")
        tabs.addTab(DashboardPage(database_path), "总览")
        tabs.addTab(ScanPage(database_path), "资料库")
        tabs.addTab(SearchPage(database_path), "搜索")
        tabs.addTab(PlanPage(database_path), "计划")
        tabs.addTab(ActivityPage(database_path), "活动")
        tabs.addTab(SettingsPage(database_path), "设置")
        self.setCentralWidget(tabs)
        self.setStyleSheet(
            """
            QMainWindow {
                background: #eef4ef;
            }
            QTabWidget::pane {
                border: 0;
                background: #eef4ef;
            }
            QTabBar::tab {
                padding: 12px 18px;
                margin: 0 2px;
                color: #304039;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #112019;
                font-weight: 600;
            }
            QLabel#pageTitle {
                font-size: 24px;
                font-weight: 700;
                color: #102018;
            }
            QLabel#pageNote {
                color: #53615b;
            }
            QFrame#metricCard,
            QFrame#infoPanel {
                background: #ffffff;
                border: 1px solid #dce5df;
                border-radius: 8px;
            }
            QLabel#metricTitle,
            QLabel#panelTitle {
                color: #52635c;
                font-size: 13px;
            }
            QLabel#metricValue {
                color: #102018;
                font-size: 28px;
                font-weight: 700;
            }
            QPushButton {
                padding: 8px 12px;
                border: 1px solid #c9d8cf;
                border-radius: 6px;
                background: #ffffff;
            }
            QPushButton:enabled:hover {
                background: #f4faf6;
                border-color: #87ad94;
            }
            QPushButton:disabled {
                color: #9aa6a0;
                background: #f3f5f3;
            }
            QTableWidget {
                background: #ffffff;
                border: 1px solid #dce5df;
                border-radius: 8px;
                gridline-color: #e7eee9;
            }
            QHeaderView::section {
                background: #f6faf7;
                border: 0;
                border-bottom: 1px solid #dce5df;
                padding: 8px;
                font-weight: 600;
            }
            """
        )
