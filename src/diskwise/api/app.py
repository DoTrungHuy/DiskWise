"""FastAPI app for the local DiskWise workbench."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from diskwise.ai.classification.service import AIClassificationService
from diskwise.ai.renaming.service import AIRenamingService
from diskwise.ai.schemas import AITask, ProviderType
from diskwise.ai.service import AIService
from diskwise.api.schemas import (
    AIClassifyRequest,
    AIRenameRequest,
    CategoryPlanRequest,
    ExecutePlanRequest,
    PermissionUpdateRequest,
    ScanRequest,
    UndoOperationRequest,
)
from diskwise.config.paths import ensure_runtime_directories
from diskwise.config.settings import AppSettings
from diskwise.database.migrations import initialize_database
from diskwise.database.repositories.file_repository import FileRecord, FileRepository
from diskwise.database.repositories.model_config_repository import ModelConfigRepository
from diskwise.database.repositories.plan_repository import (
    OperationRecord,
    PlanItemRecord,
    PlanRecord,
    PlanRepository,
)
from diskwise.duplicates.detector import DuplicateDetector
from diskwise.extractors.service import ExtractionService
from diskwise.permissions.service import Capability, PermissionService
from diskwise.planner.execution_service import PlanExecutionService
from diskwise.planner.plan_service import PlanService
from diskwise.scanner.file_scanner import FileScanner
from diskwise.search.search_service import SearchService


def create_app(database_path: Path | None = None) -> FastAPI:
    if database_path is None:
        runtime_paths = ensure_runtime_directories()
        database_path = runtime_paths.database_path
    initialize_database(database_path)

    app = FastAPI(title="DiskWise Local API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.database_path = database_path

    @app.get("/api/overview")
    def overview() -> dict[str, Any]:
        files = FileRepository(database_path)
        plans = PlanRepository(database_path).list_latest(limit=1)
        duplicates = DuplicateDetector(database_path).update_hashes_for_candidates()
        permissions = PermissionService(database_path).snapshot()
        return {
            "fileCount": files.count_files(),
            "scanRoots": [root.__dict__ for root in files.list_scan_roots()],
            "categoryCounts": [
                {"category": category, "count": count}
                for category, count in files.category_counts()
            ],
            "extensionCounts": [
                {"extension": extension, "count": count}
                for extension, count in files.extension_counts()
            ],
            "duplicateGroupCount": len(duplicates),
            "latestPlan": _plan_to_dict(plans[0]) if plans else None,
            "ai": _model_settings(database_path),
            "permissions": _permission_snapshot_to_dict(permissions),
        }

    @app.get("/api/files")
    def files(
        query: str = "",
        category: str = "",
        extension: str = "",
        limit: int = 300,
    ) -> dict[str, Any]:
        records = FileRepository(database_path).list_files(
            limit=min(max(limit, 1), 1000),
            query=query,
            category=category,
            extension=extension,
        )
        return {"files": [_file_to_dict(record) for record in records]}

    @app.post("/api/scan")
    def scan(request: ScanRequest) -> dict[str, Any]:
        try:
            PermissionService(database_path).assert_enabled(Capability.SCAN_DIRECTORIES)
            root = Path(request.path)
            repository = FileRepository(database_path)
            count = repository.save_many(root, FileScanner().scan(root))
            return {"count": count, "path": str(root.resolve(strict=False))}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/files/{file_id}/extract")
    def extract_file(file_id: int) -> dict[str, Any]:
        repository = FileRepository(database_path)
        try:
            record = repository.get_file(file_id)
            result = ExtractionService().extract(Path(record.path))
            repository.save_content(
                file_id,
                content_type=result.content_type,
                content_preview=result.content_preview,
                extractor=result.extractor,
                error=result.error,
            )
            return {
                "ok": result.ok,
                "content_type": result.content_type,
                "content_preview": result.content_preview,
                "extractor": result.extractor,
                "error": result.error,
            }
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/search")
    def search(query: str = "", limit: int = 200) -> dict[str, Any]:
        records = SearchService(database_path).search(query, limit=min(max(limit, 1), 500))
        return {"files": [_file_to_dict(record) for record in records]}

    @app.get("/api/duplicates")
    def duplicates() -> dict[str, Any]:
        groups = DuplicateDetector(database_path).update_hashes_for_candidates()
        return {
            "groups": [
                {
                    "hash": full_hash,
                    "records": [_file_to_dict(record) for record in records],
                    "wastedBytes": max(len(records) - 1, 0) * records[0].size,
                }
                for full_hash, records in groups.items()
            ]
        }

    @app.post("/api/plans/category")
    def create_category_plan(request: CategoryPlanRequest) -> dict[str, Any]:
        try:
            plan_id, suggestions = PlanService(database_path).generate_category_plan(
                Path(request.target_root)
            )
            return {
                "planId": plan_id,
                "suggestions": [suggestion.__dict__ for suggestion in suggestions],
            }
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/plans/latest")
    def latest_plans(limit: int = 5) -> dict[str, Any]:
        plans = PlanRepository(database_path).list_latest(limit=min(max(limit, 1), 20))
        return {"plans": [_plan_to_dict(plan) for plan in plans]}

    @app.post("/api/plans/{plan_id}/execute")
    def execute_plan(plan_id: int, request: ExecutePlanRequest) -> dict[str, Any]:
        try:
            results = PlanExecutionService(database_path).execute_plan(
                plan_id,
                selected_item_ids=request.selected_item_ids,
                confirmation=request.confirmation,
            )
            return {"results": [result.__dict__ for result in results]}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/activity")
    def activity(limit: int = 100) -> dict[str, Any]:
        operations = PlanExecutionService(database_path).list_operations(
            limit=min(max(limit, 1), 200)
        )
        return {"operations": [_operation_to_dict(operation) for operation in operations]}

    @app.post("/api/activity/{operation_id}/undo")
    def undo(operation_id: int, request: UndoOperationRequest) -> dict[str, Any]:
        try:
            result = PlanExecutionService(database_path).undo_operation(
                operation_id,
                confirmation=request.confirmation,
            )
            return {"result": result.__dict__}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/settings/models")
    def settings_models() -> dict[str, Any]:
        return {"tasks": _model_settings(database_path)}

    @app.get("/api/permissions")
    def permissions() -> dict[str, Any]:
        snapshot = PermissionService(database_path).snapshot()
        return _permission_snapshot_to_dict(snapshot)

    @app.patch("/api/permissions/{capability}")
    def update_permission(
        capability: str,
        request: PermissionUpdateRequest,
    ) -> dict[str, Any]:
        try:
            snapshot = PermissionService(database_path).set_enabled(
                capability,
                request.enabled,
            )
            return _permission_snapshot_to_dict(snapshot)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/ai/health")
    async def ai_health() -> dict[str, Any]:
        settings = AppSettings.from_environment()
        service = AIService(settings)
        providers: list[dict[str, Any]] = []
        for provider in ProviderType:
            try:
                health = await service.health_check(provider)
                providers.append(health.model_dump())
            except Exception as exc:
                providers.append(
                    {
                        "provider": provider.value,
                        "healthy": False,
                        "message": str(exc),
                        "version": None,
                    }
                )
        return {
            "providers": providers,
            "tasks": _model_settings(database_path),
            "permissions": _permission_snapshot_to_dict(
                PermissionService(database_path, settings).snapshot()
            ),
        }

    @app.post("/api/ai/classify")
    async def classify_file(request: AIClassifyRequest) -> dict[str, Any]:
        try:
            result = await AIClassificationService(database_path).classify_file(
                request.file_id,
                cloud_consent=request.cloud_consent,
            )
            return {
                "fileId": result.file_id,
                "category": result.category,
                "suggestedName": result.suggested_name,
                "confidence": result.confidence,
                "reason": result.reason,
            }
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/ai/rename")
    async def rename_file(request: AIRenameRequest) -> dict[str, Any]:
        try:
            result = await AIRenamingService(database_path).suggest_name(
                request.file_id,
                cloud_consent=request.cloud_consent,
            )
            return {
                "fileId": request.file_id,
                "suggestedName": result.suggested_name,
                "reason": result.reason,
            }
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    web_dist = _web_dist_dir()
    if web_dist.exists():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")

    return app


def _web_dist_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "web" / "dist"


def _file_to_dict(record: FileRecord) -> dict[str, Any]:
    path = Path(record.path)
    exists = path.exists()
    return {
        "id": record.id,
        "path": record.path,
        "name": record.name,
        "extension": record.extension,
        "size": record.size,
        "modifiedAt": record.modified_at,
        "category": record.category,
        "contentPreview": record.content_preview,
        "quickHash": record.quick_hash,
        "fullHash": record.full_hash,
        "status": record.status,
        "exists": exists,
    }


def _plan_to_dict(plan: PlanRecord) -> dict[str, Any]:
    return {
        "id": plan.id,
        "title": plan.title,
        "status": plan.status,
        "items": [_plan_item_to_dict(item) for item in plan.items],
    }


def _plan_item_to_dict(item: PlanItemRecord) -> dict[str, Any]:
    source = Path(item.source_path)
    target = Path(item.target_path)
    return {
        "id": item.id,
        "planId": item.plan_id,
        "fileId": item.file_id,
        "action": item.action,
        "sourcePath": item.source_path,
        "targetPath": item.target_path,
        "sourceExists": source.exists(),
        "targetExists": target.exists(),
        "suggestedName": item.suggested_name,
        "category": item.category,
        "reason": item.reason,
        "status": item.status,
    }


def _operation_to_dict(operation: OperationRecord) -> dict[str, Any]:
    can_undo = (
        operation.status == "succeeded"
        and operation.action in {"move", "rename"}
        and bool(operation.undo_data)
    )
    return {
        "id": operation.id,
        "planItemId": operation.plan_item_id,
        "action": operation.action,
        "sourcePath": operation.source_path,
        "targetPath": operation.target_path,
        "undoData": operation.undo_data,
        "status": operation.status,
        "createdAt": operation.created_at,
        "canUndo": can_undo,
    }


def _permission_snapshot_to_dict(snapshot: object) -> dict[str, Any]:
    return {
        "cloudEnvEnabled": snapshot.cloud_env_enabled,
        "permissions": [
            {
                "capability": permission.capability,
                "label": permission.label,
                "description": permission.description,
                "enabled": permission.enabled,
                "effectiveEnabled": permission.effective_enabled,
                "requiresConfirmation": permission.requires_confirmation,
                "locked": permission.locked,
                "reason": permission.reason,
            }
            for permission in snapshot.permissions
        ],
    }


def _model_settings(database_path: Path) -> list[dict[str, Any]]:
    labels = {
        AITask.CLASSIFICATION: "文件分类",
        AITask.RENAMING: "智能命名",
        AITask.VISION: "图片理解",
        AITask.EMBEDDINGS: "语义搜索",
    }
    configs = ModelConfigRepository(database_path).list_all()
    cloud_enabled = os.getenv("DISKWISE_CLOUD_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return [
        {
            "task": config.task.value,
            "label": labels.get(config.task, config.task.value),
            "provider": config.provider.value,
            "modelName": config.model_name,
            "enabled": config.enabled,
            "cloudEnabled": cloud_enabled,
        }
        for config in configs
    ]
