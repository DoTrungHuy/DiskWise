"""Persistence for per-task AI model selections."""

from __future__ import annotations

from pathlib import Path

from diskwise.ai.schemas import AITask, ProviderType, TaskModelConfig
from diskwise.database.connection import connect


class ModelConfigRepository:
    """Read and update non-secret model selections."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def get(self, task: AITask) -> TaskModelConfig:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT task, provider, model_name, enabled
                FROM task_model_configs
                WHERE task = ?
                """,
                (task.value,),
            ).fetchone()
        if row is None:
            raise KeyError(f"No model configuration exists for {task.value}")
        return TaskModelConfig(
            task=AITask(row["task"]),
            provider=ProviderType(row["provider"]),
            model_name=row["model_name"],
            enabled=bool(row["enabled"]),
        )

    def list_all(self) -> list[TaskModelConfig]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT task, provider, model_name, enabled
                FROM task_model_configs
                ORDER BY task
                """
            ).fetchall()
        return [
            TaskModelConfig(
                task=AITask(row["task"]),
                provider=ProviderType(row["provider"]),
                model_name=row["model_name"],
                enabled=bool(row["enabled"]),
            )
            for row in rows
        ]

    def save(self, config: TaskModelConfig) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO task_model_configs
                    (task, provider, model_name, enabled, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(task) DO UPDATE SET
                    provider = excluded.provider,
                    model_name = excluded.model_name,
                    enabled = excluded.enabled,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    config.task.value,
                    config.provider.value,
                    config.model_name,
                    int(config.enabled),
                ),
            )

