import json
from pathlib import Path

from migrator.config import Manifest, Settings
from migrator.model.tmsl_builder import TMSLBuilder
from migrator.translate.translator import DAXMeasure, DAXTranslationResult


class _Settings(Settings):
    class Config:
        arbitrary_types_allowed = True


def _sample_settings() -> Settings:
    return Settings.parse_obj(
        {
            "azure": {
                "tenant_id": "t",
                "client_id": "c",
                "client_secret": "s",
            },
            "workspaces": {
                "default_workspace_id": "00000000-0000-0000-0000-000000000000",
                "xmla_endpoint": "endpoint",
            },
            "naming": {
                "dataset_prefix": "TEST_",
                "report_prefix": "TEST_",
            },
        }
    )


def test_tmsl_builder_outputs_valid_json(tmp_path: Path) -> None:
    settings = _sample_settings()
    builder = TMSLBuilder(settings=settings, template_dir=Path("templates"))
    manifest = Manifest(workbooks=[])
    translations = [
        DAXTranslationResult(measures=[DAXMeasure(name="Profit Ratio", expression="DIVIDE([Profit], [Sales])", source="")])
    ]
    result = builder.build_model(manifest, translations)
    parsed = json.loads(result.tmsl_json)
    assert parsed["createOrReplace"]["database"]["model"]["tables"][0]["measures"][0]["name"] == "Profit Ratio"
