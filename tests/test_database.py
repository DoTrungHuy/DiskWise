from diskwise.ai.schemas import AITask, ProviderType, TaskModelConfig
from diskwise.database.connection import connect
from diskwise.database.migrations import initialize_database
from diskwise.database.repositories.model_config_repository import (
    ModelConfigRepository,
)


def test_database_initialization_is_idempotent(tmp_path):
    database_path = tmp_path / "diskwise.db"

    initialize_database(database_path)
    initialize_database(database_path)

    repository = ModelConfigRepository(database_path)
    configs = repository.list_all()
    assert len(configs) == 4
    assert repository.get(AITask.CLASSIFICATION).model_name == "gemma4:e2b"


def test_model_selection_can_be_changed_per_task(tmp_path):
    database_path = tmp_path / "diskwise.db"
    initialize_database(database_path)
    repository = ModelConfigRepository(database_path)

    repository.save(
        TaskModelConfig(
            task=AITask.RENAMING,
            provider=ProviderType.OPENAI_COMPATIBLE,
            model_name="cloud-model",
            enabled=True,
        )
    )

    saved = repository.get(AITask.RENAMING)
    assert saved.provider is ProviderType.OPENAI_COMPATIBLE
    assert saved.model_name == "cloud-model"


def test_core_tables_are_created(tmp_path):
    database_path = tmp_path / "diskwise.db"
    initialize_database(database_path)

    with connect(database_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual')"
            ).fetchall()
        }

    assert {
        "scan_roots",
        "files",
        "extracted_content",
        "classifications",
        "embeddings",
        "plans",
        "plan_items",
        "operations",
        "model_runs",
    }.issubset(tables)
