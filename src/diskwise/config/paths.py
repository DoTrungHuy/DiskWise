"""Runtime path selection for development and installed applications."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_path


@dataclass(frozen=True)
class RuntimePaths:
    """Directories and files created by DiskWise at runtime."""

    root: Path
    database_path: Path
    vectors_dir: Path
    cache_dir: Path
    logs_dir: Path


def get_runtime_paths() -> RuntimePaths:
    """Return runtime paths without creating files or directories."""
    override = os.getenv("DISKWISE_DATA_DIR")
    root = (
        Path(override).expanduser()
        if override
        else Path(user_data_path("DiskWise", "DiskWise", roaming=False))
    )
    return RuntimePaths(
        root=root,
        database_path=root / "diskwise.db",
        vectors_dir=root / "vectors",
        cache_dir=root / "cache",
        logs_dir=root / "logs",
    )


def ensure_runtime_directories() -> RuntimePaths:
    """Create the application data directories and return their paths."""
    paths = get_runtime_paths()
    for directory in (
        paths.root,
        paths.vectors_dir,
        paths.cache_dir,
        paths.logs_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return paths

