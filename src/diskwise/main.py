"""DiskWise desktop application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from diskwise.config.paths import ensure_runtime_directories
from diskwise.database.migrations import initialize_database
from diskwise.logging.setup import configure_logging
from diskwise.ui.main_window import MainWindow


def main() -> int:
    """Initialize application services and start the Qt event loop."""
    runtime_paths = ensure_runtime_directories()
    configure_logging(runtime_paths.logs_dir)
    initialize_database(runtime_paths.database_path)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("DiskWise")
    app.setOrganizationName("DiskWise")

    window = MainWindow(database_path=runtime_paths.database_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

