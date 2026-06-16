"""File search page."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from diskwise.duplicates.detector import DuplicateDetector
from diskwise.search.search_service import SearchService


class SearchPage(QWidget):
    HEADERS = ["文件名", "分类", "大小", "路径"]

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._search = SearchService(database_path)
        self._duplicates = DuplicateDetector(database_path)

        heading = QLabel("文件搜索")
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        note = QLabel(
            "当前支持 SQLite 关键词搜索和重复文件检测。语义搜索会在配置向量模型后接入。"
        )
        note.setWordWrap(True)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("输入文件名、分类或摘要关键词")
        self.search_button = QPushButton("搜索")
        self.duplicate_button = QPushButton("查找重复文件")
        self.status_label = QLabel("等待搜索")

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setObjectName("searchResultsTable")

        controls = QHBoxLayout()
        controls.addWidget(self.query_input)
        controls.addWidget(self.search_button)
        controls.addWidget(self.duplicate_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table)

        self.search_button.clicked.connect(self.run_search)
        self.query_input.returnPressed.connect(self.run_search)
        self.duplicate_button.clicked.connect(self.find_duplicates)

    def run_search(self) -> None:
        query = self.query_input.text()
        records = self._search.search(query, limit=200)
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            for column, value in enumerate(
                [record.name, record.category or "未分类", str(record.size), record.path]
            ):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.status_label.setText(f"找到 {len(records)} 条结果")

    def find_duplicates(self) -> None:
        groups = self._duplicates.update_hashes_for_candidates()
        rows = [record for records in groups.values() for record in records]
        self.table.setRowCount(len(rows))
        for row, record in enumerate(rows):
            for column, value in enumerate(
                [record.name, record.category or "未分类", str(record.size), record.path]
            ):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.status_label.setText(f"找到 {len(groups)} 组重复文件")
