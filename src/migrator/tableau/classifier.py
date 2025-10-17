"""Classify Tableau workbooks for migration strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .xml_parser import TableauWorkbook


@dataclass
class ClassificationResult:
    strategy: str
    rationales: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return "; ".join(self.rationales) if self.rationales else "No blockers detected."


class TableauClassifier:
    def classify(self, workbook: TableauWorkbook) -> ClassificationResult:
        rationales: List[str] = []
        strategy = "like"
        for worksheet in workbook.worksheets:
            for calc in worksheet.calculated_fields:
                formula_upper = calc.formula.upper()
                if "WINDOW_" in formula_upper or "RUNNING_" in formula_upper:
                    strategy = "transform"
                    rationales.append(
                        f"Worksheet {worksheet.name} contains order-dependent table calc {calc.name}."
                    )
                if "FIXED" in formula_upper and ":" in calc.formula:
                    rationales.append(
                        f"Calculated field {calc.name} uses FIXED LOD requiring grain review."
                    )
        if not rationales:
            rationales.append("All calculated fields supported for like-for-like migration.")
        return ClassificationResult(strategy=strategy, rationales=rationales)
