"""Logging helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from rich.logging import RichHandler


_LOGGER_NAME = "migrator"


def configure_logging(verbose: bool = False, jsonl_path: Path | None = None) -> None:
    """Configure logging handlers.

    Parameters
    ----------
    verbose:
        Whether to output debug level logs.
    jsonl_path:
        Optional path to emit JSONL logs.
    """

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )

    if jsonl_path:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        handler = _JSONLinesHandler(jsonl_path)
        logging.getLogger().addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")


class _JSONLinesHandler(logging.Handler):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        payload: dict[str, Any]
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            payload = {"message": message, "level": record.levelname}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
