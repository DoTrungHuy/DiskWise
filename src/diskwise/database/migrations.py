"""Idempotent database initialization."""

from __future__ import annotations

from pathlib import Path

from diskwise.database.connection import connect
from diskwise.database.schema import (
    CREATE_SCHEMA_SQL,
    DEFAULT_CAPABILITY_PERMISSIONS,
    DEFAULT_MODEL_CONFIGS,
    SCHEMA_VERSION,
)


def initialize_database(database_path: Path) -> None:
    """Create the schema and initial task model configuration."""
    with connect(database_path) as connection:
        connection.executescript(CREATE_SCHEMA_SQL)
        connection.execute(
            "INSERT OR IGNORE INTO schema_versions (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO task_model_configs
                (task, provider, model_name, enabled)
            VALUES (?, ?, ?, ?)
            """,
            DEFAULT_MODEL_CONFIGS,
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO capability_permissions
                (capability, enabled)
            VALUES (?, ?)
            """,
            DEFAULT_CAPABILITY_PERMISSIONS,
        )

