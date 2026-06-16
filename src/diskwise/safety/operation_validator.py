"""Validate file operation requests."""

from __future__ import annotations

import re
from pathlib import Path

from diskwise.safety.path_policy import (
    PathPolicyError,
    assert_target_within_root,
    is_protected_path,
    normalize_path,
)


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub("-", name).strip().strip(".")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned[:180]


def validate_source_file(source: Path | str) -> Path:
    resolved = normalize_path(source)
    if not resolved.exists():
        raise PathPolicyError(f"源文件不存在：{resolved}")
    if not resolved.is_file():
        raise PathPolicyError(f"源路径不是文件：{resolved}")
    if is_protected_path(resolved):
        raise PathPolicyError(f"禁止操作系统目录中的文件：{resolved}")
    return resolved


def validate_destination(
    destination: Path | str,
    *,
    allowed_root: Path | str,
) -> Path:
    resolved = assert_target_within_root(destination, allowed_root)
    if resolved.exists():
        raise PathPolicyError(f"目标已存在：{resolved}")
    return resolved
