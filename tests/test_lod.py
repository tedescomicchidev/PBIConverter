from migrator.tableau import parser
from migrator.translate.translator import TableauTranslator


def test_fixed_lod_translates_to_calculate_allexcept() -> None:
    translator = TableauTranslator()
    expr = parser.parse_expression("{ FIXED [Region]: SUM([Sales]) }")
    dax = translator.translate_expression(expr)
    assert "ALLEXCEPT" in dax
    assert dax.startswith("CALCULATE")
