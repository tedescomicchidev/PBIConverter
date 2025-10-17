"""Translate Tableau ASTs into DAX expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..tableau.ast import (
    BinaryOperator,
    Expression,
    Field,
    FunctionCall,
    IfExpression,
    LODExpression,
    Literal,
    NumberLiteral,
    UnaryOperator,
)
from ..tableau.xml_parser import TableauWorkbook
from . import dax_rules


@dataclass
class DAXMeasure:
    name: str
    expression: str
    source: str


@dataclass
class DAXTranslationResult:
    measures: List[DAXMeasure]

    @property
    def measures_markdown(self) -> str:
        sections: List[str] = []
        for measure in self.measures:
            sections.extend([f"### {measure.name}", "```DAX", measure.expression, "```"])
        return "\n".join(sections)


class TableauTranslator:
    """Translate Tableau calculated fields to DAX measures."""

    def translate_workbook(self, workbook: TableauWorkbook) -> DAXTranslationResult:
        measures: List[DAXMeasure] = []
        for worksheet in workbook.worksheets:
            for calc in worksheet.calculated_fields:
                dax_expression = self.translate_expression(calc.expression)
                measures.append(
                    DAXMeasure(name=calc.name, expression=dax_expression, source=calc.formula)
                )
        return DAXTranslationResult(measures=measures)

    def translate_expression(self, expression: Expression) -> str:
        if isinstance(expression, NumberLiteral):
            return str(expression.value)
        if isinstance(expression, Literal):
            return f'"{expression.value}"'
        if isinstance(expression, Field):
            return dax_rules.format_field(expression.name)
        if isinstance(expression, UnaryOperator):
            operand = self.translate_expression(expression.operand)
            return f"{expression.operator}{operand}"
        if isinstance(expression, BinaryOperator):
            return self._translate_binary(expression)
        if isinstance(expression, FunctionCall):
            return self._translate_function(expression)
        if isinstance(expression, IfExpression):
            condition = self.translate_expression(expression.condition)
            then_expr = self.translate_expression(expression.then_branch)
            else_expr = (
                self.translate_expression(expression.else_branch)
                if expression.else_branch
                else "BLANK()"
            )
            return f"IF({condition}, {then_expr}, {else_expr})"
        if isinstance(expression, LODExpression):
            return self._translate_lod(expression)
        raise NotImplementedError(f"Unsupported expression: {expression}")

    def _translate_binary(self, expression: BinaryOperator) -> str:
        left = self.translate_expression(expression.left)
        right = self.translate_expression(expression.right)
        if expression.operator == "/":
            return dax_rules.divide(left, right)
        return f"{left} {expression.operator} {right}"

    def _translate_function(self, expression: FunctionCall) -> str:
        name = expression.name.upper()
        args = [self.translate_expression(arg) for arg in expression.arguments]
        if name == "RUNNING_SUM" and args:
            base = args[0]
            date_column = f"{dax_rules.CANONICAL_DATE_TABLE}[Date]"
            condition = f"{date_column} <= MAX({date_column})"
            return dax_rules.calculate(
                base, dax_rules.filter(dax_rules.allselected(date_column), condition)
            )
        if name == "WINDOW_SUM" and args:
            column = f"{dax_rules.CANONICAL_DATE_TABLE}[Date]"
            return dax_rules.calculate(
                args[0],
                dax_rules.filter(
                    dax_rules.allselected(column),
                    "/* TODO: window frame requires manual ordering */ TRUE()",
                ),
            )
        joined_args = ", ".join(args)
        return f"{name}({joined_args})"

    def _translate_lod(self, lod: LODExpression) -> str:
        expr = self.translate_expression(lod.expression)
        if lod.lod_type == "FIXED" and lod.dimensions:
            table = f"Dim{lod.dimensions[0].name}"
            columns = [f"{table}[{dimension.name}]" for dimension in lod.dimensions]
            return dax_rules.calculate(expr, dax_rules.allexcept(table, *columns))
        if lod.lod_type == "EXCLUDE" and lod.dimensions:
            filters = [
                dax_rules.removefilters(f"Dim{dimension.name}[{dimension.name}]")
                for dimension in lod.dimensions
            ]
            return dax_rules.calculate(expr, *filters)
        if lod.lod_type == "INCLUDE" and lod.dimensions:
            dimension = lod.dimensions[0]
            table = f"VALUES(Dim{dimension.name}[{dimension.name}])"
            return dax_rules.sumx(table, expr)
        return f"/* TODO: unsupported LOD {lod.lod_type} */ {expr}"
