"""Main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QTabWidget

from diskwise.ui.placeholder_page import PlaceholderPage
from diskwise.ui.settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.setWindowTitle("DiskWise")
        self.resize(980, 680)

        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")
        tabs.addTab(
            PlaceholderPage(
                "文件扫描",
                "0.1 骨架版本不会读取真实目录。下一阶段将在用户授权后"
                "加入只读扫描和进度控制。",
            ),
            "扫描",
        )
        tabs.addTab(
            PlaceholderPage(
                "文件搜索",
                "关键词与语义搜索将在建立文件索引后启用。",
            ),
            "搜索",
        )
        tabs.addTab(
            PlaceholderPage(
                "整理计划",
                "未来只展示建议，必须经过安全检查和用户确认后才能执行。",
            ),
            "计划",
        )
        tabs.addTab(SettingsPage(database_path), "设置")
        self.setCentralWidget(tabs)

