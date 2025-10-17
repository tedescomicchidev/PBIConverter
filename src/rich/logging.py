"""Rich logging shim providing a basic handler."""

from __future__ import annotations

import logging


class RichHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - passthrough
        super().__init__()
