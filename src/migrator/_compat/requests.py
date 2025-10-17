"""Very small subset of the requests API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Response:
    status_code: int
    text: str = ""


def post(url: str, headers: Optional[Dict[str, Any]] = None, data: Optional[str] = None) -> Response:  # pragma: no cover - stub
    return Response(status_code=200, text="")


__all__ = ["Response", "post"]
