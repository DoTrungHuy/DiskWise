"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QTabWidget

from diskwise.ui.activity_page import ActivityPage
from diskwise.ui.ai_page import AIPage
from diskwise.ui.dashboard_page import DashboardPage
from diskwise.ui.permission_page import PermissionPage
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
        tabs.addTab(AIPage(database_path), "AI")
        tabs.addTab(SearchPage(database_path), "搜索")
        tabs.addTab(PlanPage(database_path), "计划")
        tabs.addTab(PermissionPage(database_path), "权限")
        tabs.addTab(ActivityPage(database_path), "活动")
        tabs.addTab(SettingsPage(database_path), "设置")
        self.setCentralWidget(tabs)
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f6f7f9;
            }
            QTabWidget::pane {
                border: 0;
                background: #f6f7f9;
            }
            QTabBar::tab {
                padding: 12px 18px;
                margin: 0 2px;
                color: #475569;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #111827;
                font-weight: 600;
            }
            QLabel#pageTitle {
                font-size: 24px;
                font-weight: 700;
                color: #111827;
            }
            QLabel#pageNote {
                color: #64748b;
            }
            QFrame#metricCard,
            QFrame#infoPanel {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QLabel#metricTitle,
            QLabel#panelTitle {
                color: #64748b;
                font-size: 13px;
            }
            QLabel#metricValue {
                color: #111827;
                font-size: 28px;
                font-weight: 700;
            }
            QPushButton {
                padding: 8px 12px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
            }
            QPushButton:enabled:hover {
                background: #eff6ff;
                border-color: #2563eb;
            }
            QPushButton:disabled {
                color: #94a3b8;
                background: #f1f5f9;
            }
            QTableWidget {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #edf2f7;
            }
            QHeaderView::section {
                background: #f8fafc;
                border: 0;
                border-bottom: 1px solid #e2e8f0;
                padding: 8px;
                font-weight: 600;
            }
            """
        )
