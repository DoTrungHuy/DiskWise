"""Safe file operation executor."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from diskwise.duplicates.hashing import hash_file
from diskwise.executor.conflict_resolver import next_available_path
from diskwise.safety.operation_validator import (
    sanitize_filename,
    validate_destination,
    validate_source_file,
)
from diskwise.safety.path_policy import assert_target_within_root


class OperationNotConfirmedError(RuntimeError):
    """Raised when a mutating operation was not explicitly confirmed."""


class FileExecutor:
    """Execute file operations only after explicit user confirmation."""

    def _require_confirmation(self, confirmed: bool) -> None:
        if not confirmed:
            raise OperationNotConfirmedError("文件操作必须先由用户确认")

    def move(
        self,
        source: Path,
        destination: Path,
        *,
        allowed_root: Path,
        confirmed: bool = False,
        allow_conflict_suffix: bool = True,
    ) -> Path:
        self._require_confirmation(confirmed)
        source = validate_source_file(source)
        destination = assert_target_within_root(destination, allowed_root)
        if allow_conflict_suffix:
            destination = next_available_path(destination)
        destination = validate_destination(destination, allowed_root=allowed_root)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if source.drive.lower() == destination.drive.lower():
            shutil.move(str(source), str(destination))
        else:
            original_hash = hash_file(source)
            shutil.copy2(source, destination)
            copied_hash = hash_file(destination)
            if copied_hash != original_hash:
                destination.unlink(missing_ok=True)
                raise IOError("跨盘复制校验失败，源文件已保留")
            source.unlink()
        return destination

    def rename(
        self,
        source: Path,
        new_name: str,
        *,
        allowed_root: Path,
        confirmed: bool = False,
    ) -> Path:
        self._require_confirmation(confirmed)
        source = validate_source_file(source)
        safe_name = sanitize_filename(new_name)
        if not safe_name:
            raise ValueError("新文件名为空或不安全")
        return self.move(
            source,
            source.with_name(safe_name),
            allowed_root=allowed_root,
            confirmed=True,
        )

    def delete_to_recycle_bin(
        self,
        target: Path,
        *,
        confirmed: bool = False,
    ) -> None:
        self._require_confirmation(confirmed)
        target = validate_source_file(target)
        try:
            from send2trash import send2trash  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("未安装 send2trash，暂不能删除到回收站") from exc
        send2trash(str(target))

    def undo(self, undo_json: str, *, confirmed: bool = False) -> Path | None:
        self._require_confirmation(confirmed)
        data = json.loads(undo_json)
        action = data.get("action")
        if action not in {"move", "rename"}:
            return None
        current = Path(str(data["current_path"]))
        original = Path(str(data["original_path"]))
        return self.move(
            current,
            original,
            allowed_root=original.parent,
            confirmed=True,
            allow_conflict_suffix=False,
        )
