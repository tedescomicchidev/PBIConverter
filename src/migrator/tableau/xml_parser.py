"""Minimal Tableau XML parsing utilities."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:  # pragma: no cover - optional dependency
    from lxml import etree  # type: ignore
except Exception:  # pragma: no cover
    import xml.etree.ElementTree as etree  # type: ignore

from .ast import Expression
from . import parser as formula_parser


@dataclass
class CalculatedField:
    name: str
    formula: str
    expression: Expression


@dataclass
class Worksheet:
    name: str
    calculated_fields: List[CalculatedField]


@dataclass
class TableauWorkbook:
    path: Path
    worksheets: List[Worksheet]

    @classmethod
    def from_file(cls, path: Path) -> "TableauWorkbook":
        if path.suffix == ".twbx":
            with zipfile.ZipFile(path, "r") as archive:
                twb_name = next(name for name in archive.namelist() if name.endswith(".twb"))
                with archive.open(twb_name) as handle:
                    xml_bytes = handle.read()
        else:
            xml_bytes = path.read_bytes()
        root = etree.fromstring(xml_bytes)
        worksheets: List[Worksheet] = []
        worksheet_nodes = _findall(root, "worksheet")
        for worksheet_node in worksheet_nodes:
            calculated: List[CalculatedField] = []
            for calc in _findall(worksheet_node, "tableau-calc"):
                name = _get_attr(calc, "name") or "Unnamed"
                formula = _get_text(calc)
                expression = formula_parser.parse_expression(formula)
                calculated.append(
                    CalculatedField(name=name, formula=formula, expression=expression)
                )
            worksheets.append(
                Worksheet(
                    name=_get_attr(worksheet_node, "name") or "Sheet", calculated_fields=calculated
                )
            )
        return cls(path=path, worksheets=worksheets)


def _findall(node: any, tag: str) -> List[any]:
    if hasattr(node, "xpath"):
        return node.xpath(f".//{tag}")
    return list(node.findall(f".//{tag}"))


def _get_attr(node: any, key: str) -> str | None:
    if hasattr(node, "get"):
        return node.get(key)
    return node.attrib.get(key) if hasattr(node, "attrib") else None


def _get_text(node: any) -> str:
    if hasattr(node, "text") and node.text is not None:
        return node.text
    return ""
