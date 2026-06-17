"""Execute saved plans with confirmation, rechecks, and undo logging."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from diskwise.database.repositories.file_repository import FileRecord, FileRepository
from diskwise.database.repositories.plan_repository import (
    OperationRecord,
    PlanItemRecord,
    PlanRepository,
)
from diskwise.executor.service import FileExecutor


CONFIRMATION_TEXT = "EXECUTE"


@dataclass(frozen=True)
class PlanExecutionResult:
    item_id: int
    operation_id: int | None
    status: str
    message: str
    target_path: str | None = None


class PlanExecutionService:
    """Run plan items only after a deliberate user confirmation."""

    def __init__(self, database_path: Path) -> None:
        self._files = FileRepository(database_path)
        self._plans = PlanRepository(database_path)
        self._executor = FileExecutor()

    def execute_plan(
        self,
        plan_id: int,
        *,
        selected_item_ids: list[int] | None = None,
        confirmation: str,
    ) -> list[PlanExecutionResult]:
        if confirmation != CONFIRMATION_TEXT:
            raise ValueError(f"请输入 {CONFIRMATION_TEXT} 以确认执行")

        plan = self._plans.get_plan(plan_id)
        selected = set(selected_item_ids or [item.id for item in plan.items])
        results: list[PlanExecutionResult] = []
        for item in plan.items:
            if item.id not in selected:
                continue
            results.append(self._execute_item(item))

        if results:
            final_status = "executed" if all(r.status == "succeeded" for r in results) else "partial"
            self._plans.update_plan_status(plan_id, final_status)
        return results

    def undo_operation(
        self,
        operation_id: int,
        *,
        confirmation: str,
    ) -> PlanExecutionResult:
        if confirmation != CONFIRMATION_TEXT:
            raise ValueError(f"请输入 {CONFIRMATION_TEXT} 以确认撤销")

        operation = self._plans.get_operation(operation_id)
        if operation.status != "succeeded":
            raise ValueError("只有已成功执行且尚未撤销的操作可以撤销")
        if not operation.undo_data:
            raise ValueError("该操作缺少撤销数据")

        restored = self._executor.undo(operation.undo_data, confirmed=True)
        self._plans.update_operation_status(operation.id, "undone")
        undo_operation_id = self._plans.save_operation(
            action="undo",
            source_path=operation.target_path or operation.source_path,
            target_path=str(restored) if restored else None,
            status="succeeded",
            plan_item_id=operation.plan_item_id,
        )
        return PlanExecutionResult(
            item_id=operation.plan_item_id or 0,
            operation_id=undo_operation_id,
            status="succeeded",
            message="撤销完成",
            target_path=str(restored) if restored else None,
        )

    def list_operations(self, limit: int = 100) -> list[OperationRecord]:
        return self._plans.list_operations(limit=limit)

    def _execute_item(self, item: PlanItemRecord) -> PlanExecutionResult:
        if item.status == "done":
            return PlanExecutionResult(
                item_id=item.id,
                operation_id=None,
                status="skipped",
                message="该计划项已经执行过",
            )
        try:
            record = self._files.get_file(item.file_id)
            self._assert_source_unchanged(record, item)
            if item.action != "move":
                raise ValueError(f"暂不支持的计划动作：{item.action}")
            target = self._executor.move(
                Path(item.source_path),
                Path(item.target_path),
                allowed_root=Path(item.target_path).parent,
                confirmed=True,
            )
            undo_data = {
                "action": item.action,
                "current_path": str(target),
                "original_path": item.source_path,
            }
            operation_id = self._plans.save_operation(
                action=item.action,
                source_path=item.source_path,
                target_path=str(target),
                status="succeeded",
                plan_item_id=item.id,
                undo_data=undo_data,
            )
            self._plans.update_item_status(item.id, "done")
            return PlanExecutionResult(
                item_id=item.id,
                operation_id=operation_id,
                status="succeeded",
                message="已移动",
                target_path=str(target),
            )
        except Exception as exc:
            operation_id = self._plans.save_operation(
                action=item.action,
                source_path=item.source_path,
                target_path=item.target_path,
                status="failed",
                plan_item_id=item.id,
                undo_data={"error": str(exc)},
            )
            self._plans.update_item_status(item.id, "failed")
            return PlanExecutionResult(
                item_id=item.id,
                operation_id=operation_id,
                status="failed",
                message=str(exc),
                target_path=item.target_path,
            )

    def _assert_source_unchanged(
        self,
        record: FileRecord,
        item: PlanItemRecord,
    ) -> None:
        source = Path(item.source_path)
        if str(source.resolve(strict=False)) != str(Path(record.path).resolve(strict=False)):
            raise ValueError("计划源路径与当前索引不一致")
        if not source.exists() or not source.is_file():
            raise ValueError(f"源文件不存在：{source}")
        stat = source.stat()
        if int(stat.st_size) != int(record.size):
            raise ValueError("源文件大小已变化，请重新扫描后再执行")
        if abs(float(stat.st_mtime) - float(record.modified_at)) > 1e-6:
            raise ValueError("源文件修改时间已变化，请重新扫描后再执行")


def operation_undo_data(operation: OperationRecord) -> dict[str, object]:
    if not operation.undo_data:
        return {}
    return json.loads(operation.undo_data)
