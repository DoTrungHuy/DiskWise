"""File hashing helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path


def hash_file(path: Path | str, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def quick_hash_file(path: Path | str, *, sample_size: int = 1024 * 1024) -> str:
    candidate = Path(path)
    digest = hashlib.sha256()
    size = candidate.stat().st_size
    with candidate.open("rb") as file:
        digest.update(file.read(sample_size))
        if size > sample_size:
            file.seek(max(size - sample_size, 0))
            digest.update(file.read(sample_size))
    digest.update(str(size).encode("ascii"))
    return digest.hexdigest()
