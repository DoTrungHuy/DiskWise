"""Generate safe, reviewable organization plans."""

from __future__ import annotations

from pathlib import Path

from diskwise.database.repositories.file_repository import FileRepository, FileRecord
from diskwise.database.repositories.plan_repository import PlanRepository
from diskwise.planner.models import PlanSuggestion
from diskwise.safety.operation_validator import sanitize_filename
from diskwise.safety.path_policy import assert_target_within_root


class PlanService:
    def __init__(self, database_path: Path) -> None:
        self._files = FileRepository(database_path)
        self._plans = PlanRepository(database_path)

    def generate_category_plan(
        self,
        target_root: Path,
        *,
        limit: int = 500,
    ) -> tuple[int, list[PlanSuggestion]]:
        target_root = target_root.resolve(strict=False)
        plan_id = self._plans.create_plan("按分类整理文件")
        suggestions: list[PlanSuggestion] = []
        for record in self._files.list_files(limit=limit):
            suggestion = self._suggest_for_file(record, target_root)
            if suggestion is None:
                continue
            suggestions.append(suggestion)
            self._plans.add_item(
                plan_id,
                file_id=suggestion.file_id,
                action=suggestion.action,
                source_path=suggestion.source_path,
                target_path=suggestion.target_path,
                suggested_name=suggestion.suggested_name,
                category=suggestion.category,
                reason=suggestion.reason,
            )
        return plan_id, suggestions

    def _suggest_for_file(
        self,
        record: FileRecord,
        target_root: Path,
    ) -> PlanSuggestion | None:
        category = record.category or "其他"
        safe_category = sanitize_filename(category) or "其他"
        safe_name = sanitize_filename(record.name) or f"file-{record.id}"
        target = target_root / safe_category / safe_name
        assert_target_within_root(target, target_root)
        source = Path(record.path).resolve(strict=False)
        if source == target:
            return None
        return PlanSuggestion(
            file_id=record.id,
            action="move",
            source_path=str(source),
            target_path=str(target),
            suggested_name=safe_name,
            category=category,
            reason=f"根据分类“{category}”移动到对应文件夹",
        )
