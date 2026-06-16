from pathlib import Path

from diskwise.database.migrations import initialize_database
from diskwise.database.repositories.file_repository import FileRepository
from diskwise.duplicates.detector import DuplicateDetector
from diskwise.planner.plan_service import PlanService
from diskwise.scanner.file_scanner import FileScanner
from diskwise.search.search_service import SearchService


def _index_folder(database_path: Path, root: Path) -> FileRepository:
    initialize_database(database_path)
    repository = FileRepository(database_path)
    repository.save_many(root, FileScanner().scan(root))
    return repository


def test_keyword_search_finds_names_categories_and_content(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "database-lab.txt").write_text("SQL course report", encoding="utf-8")
    database_path = tmp_path / "diskwise.db"
    repository = _index_folder(database_path, root)
    file_id = repository.list_files()[0].id
    repository.save_content(
        file_id,
        content_type="text",
        content_preview="数据库课程实验报告",
        extractor="text",
    )

    results = SearchService(database_path).search("数据库")

    assert len(results) == 1
    assert results[0].name == "database-lab.txt"


def test_duplicate_detector_groups_equal_files(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "a.txt").write_text("same", encoding="utf-8")
    (root / "b.txt").write_text("same", encoding="utf-8")
    (root / "c.txt").write_text("different", encoding="utf-8")
    database_path = tmp_path / "diskwise.db"
    _index_folder(database_path, root)

    groups = DuplicateDetector(database_path).update_hashes_for_candidates()

    assert len(groups) == 1
    names = {record.name for records in groups.values() for record in records}
    assert names == {"a.txt", "b.txt"}


def test_plan_service_generates_category_preview(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "setup.exe").write_bytes(b"binary")
    target = tmp_path / "organized"
    target.mkdir()
    database_path = tmp_path / "diskwise.db"
    _index_folder(database_path, root)

    plan_id, suggestions = PlanService(database_path).generate_category_plan(target)

    assert plan_id > 0
    assert len(suggestions) == 1
    assert suggestions[0].action == "move"
    assert "安装包" in suggestions[0].target_path
