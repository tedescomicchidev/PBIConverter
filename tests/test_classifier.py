from pathlib import Path

from migrator.tableau.classifier import TableauClassifier
from migrator.tableau.xml_parser import TableauWorkbook


def _build_workbook(tmp_path: Path, formula: str) -> TableauWorkbook:
    xml = f"""
    <workbook>
      <worksheets>
        <worksheet name=\"Sheet1\">
          <tableau-calc name=\"Calc\">{formula}</tableau-calc>
        </worksheet>
      </worksheets>
    </workbook>
    """
    path = tmp_path / "workbook.twb"
    path.write_text(xml)
    return TableauWorkbook.from_file(path)


def test_classifier_rationale_for_running_sum(tmp_path: Path) -> None:
    workbook = _build_workbook(tmp_path, "RUNNING_SUM([Sales])")
    classifier = TableauClassifier()
    result = classifier.classify(workbook)
    assert result.strategy == "transform"
    assert any("order-dependent" in rationale for rationale in result.rationales)
