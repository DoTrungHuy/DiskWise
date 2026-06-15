"""Reusable explanatory page for features not yet enabled."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 22px; font-weight: 600;")
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()

