"""Reusable DAX snippets and helpers."""

from __future__ import annotations

CANONICAL_DATE_TABLE = "'Date'"


def measure_table_name() -> str:
    return "'Measures'"


def format_field(field: str) -> str:
    if "[" in field:
        return field
    return f"[{field}]"


def divide(numerator: str, denominator: str) -> str:
    return f"DIVIDE({numerator}, {denominator})"


def calculate(expression: str, *filters: str) -> str:
    filters_clause = ", ".join(filters)
    if filters_clause:
        return f"CALCULATE({expression}, {filters_clause})"
    return f"CALCULATE({expression})"


def allexcept(table: str, *columns: str) -> str:
    columns_clause = ", ".join(columns)
    return f"ALLEXCEPT({table}, {columns_clause})"


def removefilters(column: str) -> str:
    return f"REMOVEFILTERS({column})"


def sumx(table: str, expression: str) -> str:
    return f"SUMX({table}, {expression})"


def allselected(column: str) -> str:
    return f"ALLSELECTED({column})"


def filter(table: str, condition: str) -> str:
    return f"FILTER({table}, {condition})"
