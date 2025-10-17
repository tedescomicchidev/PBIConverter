import json
from pathlib import Path
from typer.testing import CliRunner

from migrator.cli import app


WORKBOOK_XML = """
<workbook>
  <worksheets>
    <worksheet name=\"Sheet1\">
      <tableau-calc name=\"Profit Ratio\">[Profit]/[Sales]</tableau-calc>
    </worksheet>
  </worksheets>
</workbook>
"""


def test_cli_dry_run(tmp_path: Path) -> None:
    workbook_path = tmp_path / "sample.twb"
    workbook_path.write_text(WORKBOOK_XML)
    manifest = {
        "workbooks": [
            {
                "name": "Sample",
                "path": str(workbook_path),
                "project": "Default",
                "target_workspace": "00000000-0000-0000-0000-000000000000",
                "strategy": "auto",
            }
        ]
    }
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(json.dumps(manifest))

    settings = {
        "azure": {
            "tenant_id": "t",
            "client_id": "c",
            "client_secret": "s",
        },
        "workspaces": {
            "default_workspace_id": "00000000-0000-0000-0000-000000000000",
            "xmla_endpoint": "endpoint",
        },
        "naming": {"dataset_prefix": "UNIT_", "report_prefix": "UNIT_"},
    }
    settings_path = tmp_path / "settings.yaml"
    settings_path.write_text(json.dumps(settings))

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "migrate",
            "--input",
            str(manifest_path),
            "--dry-run",
            "--out",
            str(tmp_path / "out"),
            "--settings",
            str(settings_path),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "out" / "dataset.tmsl.json").exists()
    assert (tmp_path / "out" / "measures.dax.md").exists()
