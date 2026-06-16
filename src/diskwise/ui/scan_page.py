"""File scan page."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from diskwise.database.repositories.file_repository import FileRepository, FileRecord
from diskwise.extractors.service import ExtractionService
from diskwise.scanner.file_metadata import FileMetadata
from diskwise.scanner.file_scanner import FileScanner


class ScanWorker(QThread):
    """Run slow directory scans outside the GUI thread."""

    progress = Signal(int, object)
    completed = Signal(int)
    cancelled = Signal(int)
    failed = Signal(str)

    def __init__(self, database_path: Path, folder: Path) -> None:
        super().__init__()
        self._database_path = database_path
        self._folder = folder

    def run(self) -> None:
        try:
            repository = FileRepository(self._database_path)
            scanner = FileScanner()
            root_id = repository.upsert_scan_root(self._folder)
            count = 0
            for metadata in scanner.scan(
                self._folder,
                should_stop=self.isInterruptionRequested,
            ):
                if self.isInterruptionRequested():
                    self.cancelled.emit(count)
                    return
                repository.upsert_file(metadata, root_id)
                count += 1
                if count == 1 or count % 25 == 0:
                    self.progress.emit(count, metadata)
            if self.isInterruptionRequested():
                self.cancelled.emit(count)
                return
            self.completed.emit(count)
        except Exception as exc:
            self.failed.emit(str(exc))


class ScanPage(QWidget):
    """Scan authorized folders and save metadata to SQLite."""

    HEADERS = ["文件名", "分类", "大小", "扩展名", "修改时间", "路径"]

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self._database_path = database_path
        self._repository = FileRepository(database_path)
        self._scanner = FileScanner()
        self._extractors = ExtractionService()
        self._selected_root: Path | None = None
        self._scan_worker: ScanWorker | None = None

        heading = QLabel("文件扫描")
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        note = QLabel(
            "选择你授权的文件夹后，DiskWise 会只读扫描文件名、大小、类型和时间。"
            "不会跟随符号链接，也不会修改真实文件。"
        )
        note.setWordWrap(True)

        self.path_label = QLabel("尚未选择文件夹")
        self.status_label = QLabel("等待扫描")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

        self.choose_button = QPushButton("选择文件夹")
        self.scan_button = QPushButton("开始扫描")
        self.cancel_button = QPushButton("取消扫描")
        self.extract_button = QPushButton("提取所选文件摘要")
        self.scan_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.extract_button.setEnabled(False)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setObjectName("scanResultsTable")
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        buttons = QHBoxLayout()
        buttons.addWidget(self.choose_button)
        buttons.addWidget(self.scan_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.extract_button)
        buttons.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addWidget(self.path_label)
        layout.addLayout(buttons)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.table)

        self.choose_button.clicked.connect(self.choose_folder)
        self.scan_button.clicked.connect(self.scan_selected_folder)
        self.cancel_button.clicked.connect(self.cancel_scan)
        self.extract_button.clicked.connect(self.extract_selected_file)

        self.refresh_table()

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择要扫描的文件夹")
        if not folder:
            return
        self._selected_root = Path(folder)
        self.path_label.setText(str(self._selected_root))
        self.scan_button.setEnabled(True)

    def scan_selected_folder(self) -> None:
        if self._selected_root is None:
            return
        self.scan_folder(self._selected_root)

    def scan_folder(self, folder: Path) -> None:
        if self._scan_worker and self._scan_worker.isRunning():
            return
        self._selected_root = Path(folder)
        self.path_label.setText(str(self._selected_root))
        self._set_scanning(True)
        self.status_label.setText("正在扫描... 已索引 0 个文件")
        self.progress_bar.setRange(0, 0)
        self._scan_worker = ScanWorker(self._database_path, self._selected_root)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.completed.connect(self._on_scan_completed)
        self._scan_worker.cancelled.connect(self._on_scan_cancelled)
        self._scan_worker.failed.connect(self._on_scan_failed)
        self._scan_worker.finished.connect(self._on_worker_finished)
        self._scan_worker.start()

    def cancel_scan(self) -> None:
        if self._scan_worker and self._scan_worker.isRunning():
            self.cancel_button.setEnabled(False)
            self.status_label.setText("正在取消扫描...")
            self._scan_worker.requestInterruption()

    def _on_scan_progress(self, count: int, metadata: FileMetadata) -> None:
        self.status_label.setText(
            f"正在扫描... 已索引 {count} 个文件，当前：{metadata.name}"
        )

    def _on_scan_completed(self, count: int) -> None:
        self.status_label.setText(f"扫描完成：{count} 个文件")
        self._finish_scan()

    def _on_scan_cancelled(self, count: int) -> None:
        self.status_label.setText(f"扫描已取消：已索引 {count} 个文件")
        self._finish_scan()

    def _on_scan_failed(self, message: str) -> None:
        QMessageBox.warning(self, "扫描失败", message)
        self.status_label.setText(f"扫描失败：{message}")
        self._finish_scan()

    def _finish_scan(self) -> None:
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self._set_scanning(False)
        self.refresh_table()

    def _on_worker_finished(self) -> None:
        worker = self.sender()
        if worker is not None:
            worker.deleteLater()
        self._scan_worker = None

    def _set_scanning(self, scanning: bool) -> None:
        self.choose_button.setEnabled(not scanning)
        self.scan_button.setEnabled(not scanning and self._selected_root is not None)
        self.cancel_button.setEnabled(scanning)
        self.extract_button.setEnabled(
            not scanning and self.table.rowCount() > 0
        )

    def refresh_table(self) -> None:
        self._populate(self._repository.list_files(limit=500))
        scanning = bool(self._scan_worker and self._scan_worker.isRunning())
        self.extract_button.setEnabled(self.table.rowCount() > 0 and not scanning)

    def extract_selected_file(self) -> None:
        file_id = self._selected_file_id()
        if file_id is None:
            return
        record = self._repository.get_file(file_id)
        result = self._extractors.extract(Path(record.path))
        self._repository.save_content(
            file_id,
            content_type=result.content_type,
            content_preview=result.content_preview,
            extractor=result.extractor,
            error=result.error,
        )
        self.status_label.setText(
            "内容摘要已保存" if result.ok else f"内容提取受限：{result.error}"
        )
        self.refresh_table()

    def _selected_file_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        if item is None:
            return None
        return int(item.data(256))

    def _populate(self, records: list[FileRecord]) -> None:
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                record.name,
                record.category or "未分类",
                str(record.size),
                record.extension,
                str(int(record.modified_at)),
                record.path,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(256, record.id)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()
