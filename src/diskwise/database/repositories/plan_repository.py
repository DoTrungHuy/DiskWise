"""Persistence for organization plans and executed operations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from diskwise.database.connection import connect


@dataclass(frozen=True)
class PlanItemRecord:
    id: int
    plan_id: int
    file_id: int
    action: str
    source_path: str
    target_path: str
    suggested_name: str | None
    category: str | None
    reason: str | None
    status: str


@dataclass(frozen=True)
class PlanRecord:
    id: int
    title: str
    status: str
    items: list[PlanItemRecord]


@dataclass(frozen=True)
class OperationRecord:
    id: int
    plan_item_id: int | None
    action: str
    source_path: str
    target_path: str | None
    undo_data: str | None
    status: str
    created_at: str


def _item_from_row(row) -> PlanItemRecord:
    return PlanItemRecord(
        id=row["id"],
        plan_id=row["plan_id"],
        file_id=row["file_id"],
        action=row["action"],
        source_path=row["source_path"],
        target_path=row["target_path"],
        suggested_name=row["suggested_name"],
        category=row["category"],
        reason=row["reason"],
        status=row["status"],
    )


def _operation_from_row(row) -> OperationRecord:
    return OperationRecord(
        id=row["id"],
        plan_item_id=row["plan_item_id"],
        action=row["action"],
        source_path=row["source_path"],
        target_path=row["target_path"],
        undo_data=row["undo_data"],
        status=row["status"],
        created_at=row["created_at"],
    )


class PlanRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def create_plan(self, title: str) -> int:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO plans (title, status) VALUES (?, 'draft')",
                (title,),
            )
            return int(cursor.lastrowid)

    def add_item(
        self,
        plan_id: int,
        *,
        file_id: int,
        action: str,
        source_path: str,
        target_path: str,
        suggested_name: str | None = None,
        category: str | None = None,
        reason: str | None = None,
    ) -> int:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO plan_items (
                    plan_id, file_id, action, source_path, target_path,
                    suggested_name, category, reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    file_id,
                    action,
                    source_path,
                    target_path,
                    suggested_name,
                    category,
                    reason,
                ),
            )
            return int(cursor.lastrowid)

    def get_plan(self, plan_id: int) -> PlanRecord:
        with connect(self._database_path) as connection:
            plan = connection.execute(
                "SELECT id, title, status FROM plans WHERE id = ?",
                (plan_id,),
            ).fetchone()
            if plan is None:
                raise KeyError(f"Plan id {plan_id} does not exist")
            rows = connection.execute(
                "SELECT * FROM plan_items WHERE plan_id = ? ORDER BY id",
                (plan_id,),
            ).fetchall()
        return PlanRecord(
            id=plan["id"],
            title=plan["title"],
            status=plan["status"],
            items=[_item_from_row(row) for row in rows],
        )

    def update_plan_status(self, plan_id: int, status: str) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                "UPDATE plans SET status = ? WHERE id = ?",
                (status, plan_id),
            )

    def update_item_status(self, item_id: int, status: str) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                "UPDATE plan_items SET status = ? WHERE id = ?",
                (status, item_id),
            )

    def list_latest(self, limit: int = 20) -> list[PlanRecord]:
        with connect(self._database_path) as connection:
            plans = connection.execute(
                "SELECT id, title, status FROM plans ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            plan_ids = [row["id"] for row in plans]
            items_by_plan: dict[int, list[PlanItemRecord]] = {
                plan_id: [] for plan_id in plan_ids
            }
            if plan_ids:
                placeholders = ",".join("?" for _ in plan_ids)
                rows = connection.execute(
                    f"SELECT * FROM plan_items WHERE plan_id IN ({placeholders}) ORDER BY id",
                    plan_ids,
                ).fetchall()
                for row in rows:
                    item = _item_from_row(row)
                    items_by_plan[item.plan_id].append(item)
        return [
            PlanRecord(
                id=row["id"],
                title=row["title"],
                status=row["status"],
                items=items_by_plan[row["id"]],
            )
            for row in plans
        ]

    def save_operation(
        self,
        *,
        action: str,
        source_path: str,
        target_path: str | None,
        status: str,
        plan_item_id: int | None = None,
        undo_data: dict[str, object] | None = None,
    ) -> int:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO operations (
                    plan_item_id, action, source_path, target_path, undo_data, status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_item_id,
                    action,
                    source_path,
                    target_path,
                    json.dumps(undo_data or {}, ensure_ascii=False),
                    status,
                ),
            )
            return int(cursor.lastrowid)

    def list_operations(self, limit: int = 100) -> list[OperationRecord]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM operations
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [_operation_from_row(row) for row in rows]

    def get_operation(self, operation_id: int) -> OperationRecord:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT * FROM operations WHERE id = ?",
                (operation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Operation id {operation_id} does not exist")
        return _operation_from_row(row)

    def update_operation_status(self, operation_id: int, status: str) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                "UPDATE operations SET status = ? WHERE id = ?",
                (status, operation_id),
            )
