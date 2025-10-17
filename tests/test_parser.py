from pathlib import Path

from migrator.tableau import parser
from migrator.tableau.ast import BinaryOperator, Field


def test_parse_simple_divide(tmp_path: Path) -> None:
    expr = parser.parse_expression("[Profit]/[Sales]")
    assert isinstance(expr, BinaryOperator)
    assert isinstance(expr.left, Field)
    assert expr.left.name == "Profit"
