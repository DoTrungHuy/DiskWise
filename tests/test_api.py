import json
from pathlib import Path

from fastapi.testclient import TestClient

from diskwise.ai.schemas import (
    AITask,
    GenerateResponse,
    ModelInfo,
    ProviderHealth,
    ProviderType,
    TaskModelConfig,
)
from diskwise.api.app import create_app
from diskwise.database.migrations import initialize_database
from diskwise.database.repositories.file_repository import FileRepository
from diskwise.database.repositories.model_config_repository import ModelConfigRepository
from diskwise.database.repositories.plan_repository import PlanRepository
from diskwise.scanner.file_scanner import FileScanner


def _client(tmp_path: Path) -> tuple[TestClient, Path]:
    database_path = tmp_path / "diskwise.db"
    initialize_database(database_path)
    return TestClient(create_app(database_path)), database_path


def _index_folder(database_path: Path, root: Path) -> None:
    repository = FileRepository(database_path)
    repository.save_many(root, FileScanner().scan(root))


def test_api_overview_empty_state(tmp_path):
    client, _ = _client(tmp_path)

    response = client.get("/api/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["fileCount"] == 0
    assert body["scanRoots"] == []
    assert body["latestPlan"] is None


def test_api_scan_and_keyword_search(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "database-lab.txt").write_text("SQL course report", encoding="utf-8")
    client, database_path = _client(tmp_path)

    scan = client.post("/api/scan", json={"path": str(root)})
    search = client.get("/api/search", params={"query": "database"})
    files = client.get("/api/files", params={"query": "database"})

    assert scan.status_code == 200
    assert scan.json()["count"] == 1
    assert search.status_code == 200
    assert search.json()["files"][0]["name"] == "database-lab.txt"
    assert files.json()["files"][0]["exists"]
    assert FileRepository(database_path).count_files() == 1


def test_api_duplicates_are_grouped(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "a.txt").write_text("same", encoding="utf-8")
    (root / "b.txt").write_text("same", encoding="utf-8")
    (root / "c.txt").write_text("different", encoding="utf-8")
    client, database_path = _client(tmp_path)
    _index_folder(database_path, root)

    response = client.get("/api/duplicates")

    assert response.status_code == 200
    groups = response.json()["groups"]
    assert len(groups) == 1
    assert {record["name"] for record in groups[0]["records"]} == {"a.txt", "b.txt"}


def test_api_plan_execution_requires_confirmation(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "setup.exe").write_bytes(b"binary")
    target = tmp_path / "organized"
    target.mkdir()
    client, database_path = _client(tmp_path)
    _index_folder(database_path, root)
    plan = client.post("/api/plans/category", json={"targetRoot": str(target)}).json()

    response = client.post(
        f"/api/plans/{plan['planId']}/execute",
        json={"selectedItemIds": [], "confirmation": "YES"},
    )

    assert response.status_code == 400
    assert "EXECUTE" in response.json()["detail"]
    assert PlanRepository(database_path).list_operations() == []


def test_api_plan_execute_logs_and_undoes_move(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    source = root / "setup.exe"
    source.write_bytes(b"binary")
    target = tmp_path / "organized"
    target.mkdir()
    client, database_path = _client(tmp_path)
    _index_folder(database_path, root)
    plan = client.post("/api/plans/category", json={"targetRoot": str(target)}).json()

    execute = client.post(
        f"/api/plans/{plan['planId']}/execute",
        json={"selectedItemIds": [], "confirmation": "EXECUTE"},
    )
    activity = client.get("/api/activity").json()["operations"]

    assert execute.status_code == 200
    assert execute.json()["results"][0]["status"] == "succeeded"
    moved_path = Path(execute.json()["results"][0]["target_path"])
    assert moved_path.exists()
    assert not source.exists()
    assert activity[0]["canUndo"]
    undo = client.post(
        f"/api/activity/{activity[0]['id']}/undo",
        json={"confirmation": "EXECUTE"},
    )
    assert undo.status_code == 200
    assert source.exists()


def test_api_plan_execution_rechecks_modified_source(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    source = root / "notes.txt"
    source.write_text("first", encoding="utf-8")
    target = tmp_path / "organized"
    target.mkdir()
    client, database_path = _client(tmp_path)
    _index_folder(database_path, root)
    plan = client.post("/api/plans/category", json={"targetRoot": str(target)}).json()
    source.write_text("changed", encoding="utf-8")

    execute = client.post(
        f"/api/plans/{plan['planId']}/execute",
        json={"selectedItemIds": [], "confirmation": "EXECUTE"},
    )

    assert execute.status_code == 200
    result = execute.json()["results"][0]
    assert result["status"] == "failed"
    assert "变化" in result["message"]
    assert source.exists()


def test_api_plan_execution_uses_conflict_suffix(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    source = root / "setup.exe"
    source.write_bytes(b"binary")
    target = tmp_path / "organized"
    (target / "安装包").mkdir(parents=True)
    (target / "安装包" / "setup.exe").write_bytes(b"existing")
    client, database_path = _client(tmp_path)
    _index_folder(database_path, root)
    plan = client.post("/api/plans/category", json={"targetRoot": str(target)}).json()

    execute = client.post(
        f"/api/plans/{plan['planId']}/execute",
        json={"selectedItemIds": [], "confirmation": "EXECUTE"},
    )

    assert execute.status_code == 200
    result = execute.json()["results"][0]
    assert result["status"] == "succeeded"
    assert Path(result["target_path"]).name == "setup (1).exe"


def test_api_permissions_default_cloud_ai_off(tmp_path):
    client, _ = _client(tmp_path)

    response = client.get("/api/permissions")
    body = response.json()
    cloud = next(
        item for item in body["permissions"] if item["capability"] == "cloud_ai"
    )
    sensitive = next(
        item
        for item in body["permissions"]
        if item["capability"] == "sensitive_file_protection"
    )

    assert response.status_code == 200
    assert cloud["enabled"] is False
    assert cloud["effectiveEnabled"] is False
    assert sensitive["locked"] is True
    assert sensitive["effectiveEnabled"] is True


def test_api_cloud_sensitive_file_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("DISKWISE_CLOUD_ENABLED", "true")
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / ".env").write_text("SECRET=value", encoding="utf-8")
    client, database_path = _client(tmp_path)
    _index_folder(database_path, root)
    client.patch("/api/permissions/cloud_ai", json={"enabled": True})
    ModelConfigRepository(database_path).save(
        TaskModelConfig(
            task=AITask.CLASSIFICATION,
            provider=ProviderType.OPENAI_COMPATIBLE,
            model_name="cloud-model",
            enabled=True,
        )
    )

    response = client.post(
        "/api/ai/classify",
        json={"fileId": 1, "cloudConsent": True},
    )

    assert response.status_code == 400
    assert "敏感文件" in response.json()["detail"]


def test_api_ai_classify_and_rename_with_mock_provider(tmp_path, monkeypatch):
    class FakeProvider:
        async def health_check(self):
            return ProviderHealth(
                provider=ProviderType.OLLAMA,
                healthy=True,
                message="fake ready",
            )

        async def list_models(self):
            return [ModelInfo(name="gemma4:e2b", provider=ProviderType.OLLAMA)]

        async def generate(self, request):
            if "file_id" not in request.prompt:
                return GenerateResponse(
                    model=request.model,
                    text=json.dumps(
                        {
                            "suggested_name": "database-lab-report.txt",
                            "reason": "文件内容指向数据库课程报告",
                        },
                        ensure_ascii=False,
                    ),
                )
            return GenerateResponse(
                model=request.model,
                text=json.dumps(
                    {
                        "file_id": 1,
                        "category": "课程资料",
                        "suggested_name": "database-lab-report.txt",
                        "confidence": 0.91,
                        "reason": "内容包含 SQL course report",
                    },
                    ensure_ascii=False,
                ),
            )

        async def embed(self, request):
            raise NotImplementedError

        async def aclose(self):
            return None

    monkeypatch.setattr(
        "diskwise.ai.service.create_provider",
        lambda provider_type, settings: FakeProvider(),
    )
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "database-lab.txt").write_text("SQL course report", encoding="utf-8")
    client, database_path = _client(tmp_path)
    _index_folder(database_path, root)

    classify = client.post("/api/ai/classify", json={"fileId": 1})
    rename = client.post("/api/ai/rename", json={"fileId": 1})

    assert classify.status_code == 200
    assert classify.json()["category"] == "课程资料"
    assert rename.status_code == 200
    assert rename.json()["suggestedName"] == "database-lab-report.txt"
    assert FileRepository(database_path).get_file(1).category == "课程资料"
