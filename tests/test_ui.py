from PySide6.QtWidgets import QTabWidget

from diskwise.ai.schemas import ModelInfo, ProviderHealth, ProviderType
from diskwise.database.migrations import initialize_database
from diskwise.ui.main_window import MainWindow
from diskwise.ui.settings_page import SettingsPage


def test_main_window_starts_with_four_pages(qtbot, tmp_path):
    database_path = tmp_path / "diskwise.db"
    initialize_database(database_path)

    window = MainWindow(database_path)
    qtbot.addWidget(window)

    tabs = window.findChild(QTabWidget, "mainTabs")
    assert tabs is not None
    assert tabs.count() == 4
    assert [tabs.tabText(index) for index in range(tabs.count())] == [
        "扫描",
        "搜索",
        "计划",
        "设置",
    ]


def test_settings_page_lists_multiple_discovered_models(qtbot, tmp_path):
    database_path = tmp_path / "diskwise.db"
    initialize_database(database_path)
    page = SettingsPage(database_path)
    qtbot.addWidget(page)

    page._on_models_ready(
        ProviderHealth(
            provider=ProviderType.OLLAMA,
            healthy=True,
            message="Ollama 正在运行",
        ),
        [
            ModelInfo(name="gemma4:e2b", provider=ProviderType.OLLAMA),
            ModelInfo(name="another-local-model", provider=ProviderType.OLLAMA),
        ],
    )

    model_names = [
        page.model_combo.itemText(index)
        for index in range(page.model_combo.count())
    ]
    assert model_names == ["gemma4:e2b", "another-local-model"]
