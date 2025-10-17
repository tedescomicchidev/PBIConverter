"""Validation utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

from ..config import Manifest
from ..translate.translator import DAXTranslationResult


class ValidationIssue(BaseModel):
    message: str
    severity: str = "info"


@dataclass
class MigrationReport:
    issues: List[ValidationIssue] = field(default_factory=list)

    def json(self, indent: int = 2) -> str:
        payload = {"issues": [issue.dict() for issue in self.issues]}
        return json.dumps(payload, indent=indent)

    def to_markdown(self, path: Optional[Path] = None) -> str:
        lines = ["# Migration Report"]
        if not self.issues:
            lines.append("No validation issues recorded.")
        for issue in self.issues:
            lines.append(f"* **{issue.severity.upper()}** – {issue.message}")
        markdown = "\n".join(lines)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markdown)
        return markdown


class MigrationValidator:
    def validate(self, manifest: Manifest, translations: List[DAXTranslationResult]) -> MigrationReport:
        issues = []
        if not translations:
            issues.append(ValidationIssue(message="No translations generated", severity="warning"))
        return MigrationReport(issues=issues)
