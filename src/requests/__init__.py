"""Minimal requests shim for dry-run testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Response:
    status_code: int
    text: str = ""


def post(url: str, headers: Dict[str, Any] | None = None, data: str | None = None) -> Response:  # pragma: no cover - stub
    return Response(status_code=200, text="")
