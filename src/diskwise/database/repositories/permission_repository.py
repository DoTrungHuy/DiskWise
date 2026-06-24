"""Persistence for local capability permissions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from diskwise.database.connection import connect


@dataclass(frozen=True)
class CapabilityPermissionRecord:
    capability: str
    enabled: bool
    updated_at: str


def _from_row(row) -> CapabilityPermissionRecord:
    return CapabilityPermissionRecord(
        capability=row["capability"],
        enabled=bool(row["enabled"]),
        updated_at=row["updated_at"],
    )


class PermissionRepository:
    """Read and update persisted local capability switches."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list_all(self) -> dict[str, CapabilityPermissionRecord]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT capability, enabled, updated_at
                FROM capability_permissions
                ORDER BY capability
                """
            ).fetchall()
        return {row["capability"]: _from_row(row) for row in rows}

    def get(self, capability: str) -> CapabilityPermissionRecord | None:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT capability, enabled, updated_at
                FROM capability_permissions
                WHERE capability = ?
                """,
                (capability,),
            ).fetchone()
        return _from_row(row) if row else None

    def set_enabled(self, capability: str, enabled: bool) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO capability_permissions
                    (capability, enabled, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(capability) DO UPDATE SET
                    enabled = excluded.enabled,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (capability, int(enabled)),
            )
