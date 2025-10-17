"""TMSL builder for Tabular models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:  # pragma: no cover - optional dependency
    from jinja2 import Environment, FileSystemLoader  # type: ignore
except Exception:  # pragma: no cover
    Environment = None  # type: ignore
    FileSystemLoader = None  # type: ignore

from ..config import Manifest, Settings
from ..translate.translator import DAXMeasure, DAXTranslationResult


@dataclass
class ModelBuildResult:
    tmsl_json: str
    measures: List[DAXMeasure]


class TMSLBuilder:
    def __init__(self, settings: Settings, template_dir: Optional[Path] = None) -> None:
        self.settings = settings
        self.template_dir = template_dir or Path("templates")
        if Environment:
            self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        else:
            self.env = None

    def build_model(
        self, manifest: Manifest, translations: List[DAXTranslationResult]
    ) -> ModelBuildResult:
        measures = [measure for result in translations for measure in result.measures]
        if self.env:
            template = self.env.get_template("dataset.tmsl.j2")
            rendered = template.render(
                measures=measures,
                settings=self.settings,
            )
            json.loads(rendered)
            return ModelBuildResult(tmsl_json=rendered, measures=measures)
        payload = self._fallback_payload(measures)
        return ModelBuildResult(tmsl_json=json.dumps(payload, indent=2), measures=measures)

    def _fallback_payload(self, measures: List[DAXMeasure]) -> dict:
        prefix = getattr(self.settings.naming, "dataset_prefix", None)
        if prefix is None and isinstance(self.settings.naming, dict):
            prefix = self.settings.naming.get("dataset_prefix", "")
        prefix = prefix or ""
        return {
            "createOrReplace": {
                "object": {"database": {"name": f"{prefix}MigratedDataset"}},
                "database": {
                    "name": f"{prefix}MigratedDataset",
                    "compatibilityLevel": 1520,
                    "model": {
                        "tables": [
                            {
                                "name": "Measures",
                                "partitions": [
                                    {
                                        "name": "MeasuresPartition",
                                        "source": {"type": "calculated"},
                                    }
                                ],
                                "measures": [
                                    {
                                        "name": measure.name,
                                        "expression": measure.expression,
                                        "description": "Translated from Tableau",
                                    }
                                    for measure in measures
                                ],
                            },
                            {
                                "name": "Date",
                                "partitions": [
                                    {
                                        "name": "DatePartition",
                                        "source": {
                                            "type": "calculated",
                                            "expression": "EVALUATE CALENDAR(DATE(2010,1,1), DATE(2030,12,31))",
                                        },
                                    }
                                ],
                            },
                        ]
                    },
                },
            }
        }
