"""AST definitions for Tableau expressions."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Expression(BaseModel):
    """Base class for expressions."""

    def accept(self, visitor: "ExpressionVisitor") -> str:
        return visitor.visit(self)


class Literal(Expression):
    value: str


class NumberLiteral(Expression):
    value: float


class Field(Expression):
    name: str


class Identifier(Expression):
    name: str


class BinaryOperator(Expression):
    left: Expression
    operator: str
    right: Expression


class UnaryOperator(Expression):
    operator: str
    operand: Expression


class FunctionCall(Expression):
    name: str
    arguments: List[Expression]


class IfExpression(Expression):
    condition: Expression
    then_branch: Expression
    else_branch: Optional[Expression]


class LODExpression(Expression):
    lod_type: str
    dimensions: List[Field]
    expression: Expression


class ExpressionVisitor:
    """Visitor base class."""

    def visit(self, expression: Expression) -> str:  # pragma: no cover - abstract
        raise NotImplementedError
