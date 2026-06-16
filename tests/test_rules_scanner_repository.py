from pathlib import Path

import pytest

from diskwise.database.migrations import initialize_database
from diskwise.database.repositories.file_repository import FileRepository
from diskwise.rules.rule_classifier import classify_by_extension
from diskwise.safety.path_policy import PathPolicyError, assert_scan_root_allowed
from diskwise.scanner.file_scanner import FileScanner


def test_rule_classifier_uses_extension_rules():
    assert classify_by_extension(Path("ubuntu.iso")) == "系统镜像"
    assert classify_by_extension(Path("setup.exe")) == "安装包"
    assert classify_by_extension(Path("movie.mp4")) == "视频"
    assert classify_by_extension(Path("archive.zip")) == "压缩包"
    assert classify_by_extension(Path("unknown.diskwise")) is None


def test_scanner_indexes_files_without_following_symlink(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "note.txt").write_text("hello", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    (nested / "video.mp4").write_bytes(b"movie")
    try:
        (root / "link.txt").symlink_to(root / "note.txt")
    except (OSError, NotImplementedError):
        pass

    files = list(FileScanner().scan(root))

    names = {metadata.name for metadata in files}
    assert "note.txt" in names
    assert "video.mp4" in names
    assert "link.txt" not in names


def test_scan_results_can_be_saved_to_sqlite(tmp_path):
    root = tmp_path / "scan-root"
    root.mkdir()
    (root / "setup.exe").write_bytes(b"binary")
    database_path = tmp_path / "diskwise.db"
    initialize_database(database_path)

    repository = FileRepository(database_path)
    count = repository.save_many(root, FileScanner().scan(root))

    assert count == 1
    records = repository.list_files()
    assert records[0].name == "setup.exe"
    assert records[0].category == "安装包"


def test_protected_drive_root_is_rejected():
    with pytest.raises(PathPolicyError):
        assert_scan_root_allowed(Path("C:/"))
