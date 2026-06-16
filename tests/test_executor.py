import pytest

from diskwise.executor.service import FileExecutor, OperationNotConfirmedError
from diskwise.safety.path_policy import PathPolicyError


def test_real_file_operations_require_confirmation(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    destination = tmp_path / "destination.txt"

    with pytest.raises(OperationNotConfirmedError):
        FileExecutor().move(source, destination, allowed_root=tmp_path)


def test_move_file_after_confirmation(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    destination = tmp_path / "folder" / "destination.txt"

    moved = FileExecutor().move(
        source,
        destination,
        allowed_root=tmp_path,
        confirmed=True,
    )

    assert moved == destination
    assert not source.exists()
    assert destination.read_text(encoding="utf-8") == "hello"


def test_rename_sanitizes_filename(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")

    renamed = FileExecutor().rename(
        source,
        'bad:name?.txt',
        allowed_root=tmp_path,
        confirmed=True,
    )

    assert renamed.name == "bad-name-.txt"
    assert renamed.exists()


def test_move_rejects_destination_escape(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    outside = tmp_path.parent / "outside.txt"

    with pytest.raises(PathPolicyError):
        FileExecutor().move(
            source,
            outside,
            allowed_root=tmp_path,
            confirmed=True,
        )
