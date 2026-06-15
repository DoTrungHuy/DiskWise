"""Safe application logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(logs_dir: Path) -> None:
    """Configure a local log without recording document contents or secrets."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(logs_dir / "diskwise.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

