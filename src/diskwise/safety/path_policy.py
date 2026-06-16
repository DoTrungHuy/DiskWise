"""Path safety rules for scans and file operations."""

from __future__ import annotations

import stat as stat_module
from pathlib import Path


PROTECTED_DIR_NAMES = {
    "$recycle.bin",
    "program files",
    "program files (x86)",
    "programdata",
    "system volume information",
    "windows",
}

SENSITIVE_EXTENSIONS = {
    ".env",
    ".key",
    ".pem",
    ".pfx",
    ".ppk",
}


class PathPolicyError(ValueError):
    """Raised when a path is outside DiskWise safety rules."""


def normalize_path(path: Path | str) -> Path:
    """Resolve a path without requiring it to already exist."""
    return Path(path).expanduser().resolve(strict=False)


def is_protected_path(path: Path | str) -> bool:
    """Return True for system locations DiskWise should not scan or modify."""
    resolved = normalize_path(path)
    parts = {part.lower() for part in resolved.parts}
    if parts.intersection(PROTECTED_DIR_NAMES):
        return True
    if resolved.anchor and resolved == Path(resolved.anchor):
        return True
    return False


def is_symlink_or_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows reparse points."""
    try:
        stat_result = path.lstat()
    except OSError:
        return True
    if path.is_symlink():
        return True
    reparse_flag = getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(stat_result, "st_file_attributes", 0) & reparse_flag)


def assert_scan_root_allowed(root: Path | str) -> Path:
    """Validate a user-selected scan root."""
    resolved = normalize_path(root)
    if not resolved.exists():
        raise PathPolicyError(f"目录不存在：{resolved}")
    if not resolved.is_dir():
        raise PathPolicyError(f"不是文件夹：{resolved}")
    if is_protected_path(resolved):
        raise PathPolicyError(f"为安全起见，禁止扫描系统目录：{resolved}")
    if is_symlink_or_reparse_point(resolved):
        raise PathPolicyError(f"为安全起见，禁止扫描符号链接或目录联接：{resolved}")
    return resolved


def is_within_directory(path: Path | str, parent: Path | str) -> bool:
    """Return True when path stays under parent after normalization."""
    resolved_path = normalize_path(path)
    resolved_parent = normalize_path(parent)
    try:
        resolved_path.relative_to(resolved_parent)
    except ValueError:
        return False
    return True


def assert_target_within_root(target: Path | str, root: Path | str) -> Path:
    """Validate that an operation target cannot escape the allowed root."""
    resolved = normalize_path(target)
    if not is_within_directory(resolved, root):
        raise PathPolicyError(f"目标路径越界：{resolved}")
    if is_protected_path(resolved):
        raise PathPolicyError(f"禁止写入系统目录：{resolved}")
    return resolved


def is_sensitive_for_cloud(path: Path | str) -> bool:
    """Return True for files that should not be sent to cloud AI."""
    candidate = Path(path)
    lowered = candidate.name.lower()
    if lowered in {".env", "id_rsa", "id_dsa"}:
        return True
    return candidate.suffix.lower() in SENSITIVE_EXTENSIONS
