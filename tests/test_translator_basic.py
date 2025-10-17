from migrator.tableau import parser
from migrator.translate.translator import TableauTranslator


def test_divide_translates_to_divide() -> None:
    translator = TableauTranslator()
    expr = parser.parse_expression("[Profit]/[Sales]")
    dax = translator.translate_expression(expr)
    assert dax == "DIVIDE([Profit], [Sales])"


def test_if_translates_to_if() -> None:
    translator = TableauTranslator()
    expr = parser.parse_expression("IF [Sales] > 0 THEN [Profit] ELSE 0 END")
    dax = translator.translate_expression(expr)
    assert dax.startswith("IF(")
