"""CLI entrypoints for the Tableau to Power BI migrator."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency
    import typer  # type: ignore
except Exception:  # pragma: no cover - fallback
    from ._compat import typer  # type: ignore

from .config import Settings, load_manifest, load_settings
from .logging import configure_logging, get_logger
from .model.tmsl_builder import ModelBuildResult, TMSLBuilder
from .powerbi.publisher import PowerBIPublisher
from .tableau.classifier import TableauClassifier
from .tableau.xml_parser import TableauWorkbook
from .translate.translator import DAXTranslationResult, TableauTranslator
from .validation.validators import MigrationReport, MigrationValidator

app = typer.Typer(help="Tableau to Power BI migration toolkit")


DEFAULT_SETTINGS_PATH = Path("config/settings.yaml")
EXAMPLE_SETTINGS_PATH = Path("config/settings.example.yaml")


def _load_settings_file(path: Path) -> Settings:
    """Load settings, falling back to the example file when necessary."""

    if path.exists():
        return load_settings(path)
    if path == DEFAULT_SETTINGS_PATH and EXAMPLE_SETTINGS_PATH.exists():
        return load_settings(EXAMPLE_SETTINGS_PATH)
    raise typer.BadParameter(f"Settings file not found: {path}")


def _resolve_output_dir(out: Optional[Path]) -> Path:
    directory = out or Path("out")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@app.command()
def migrate(
    input: Path = typer.Option(..., "--input", help="Manifest file path"),
    dry_run: bool = typer.Option(True, "--dry-run", help="Emit artifacts only"),
    publish: bool = typer.Option(False, "--publish", help="Publish to Power BI"),
    validate: bool = typer.Option(False, "--validate", help="Run validation"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
    out: Optional[Path] = typer.Option(None, "--out", help="Output directory"),
    settings: Path = typer.Option(
        DEFAULT_SETTINGS_PATH,
        "--settings",
        help="Settings file path (defaults to config/settings.yaml, falls back to example)",
    ),
) -> None:
    """Run the full migration pipeline for all workbooks in the manifest."""

    configure_logging(verbose)
    log = get_logger(__name__)
    manifest = load_manifest(input)
    settings_model = _load_settings_file(settings)
    output_dir = _resolve_output_dir(out)

    translator = TableauTranslator()
    classifier = TableauClassifier()
    builder = TMSLBuilder(settings=settings_model)
    publisher = PowerBIPublisher(settings=settings_model)
    validator = MigrationValidator()

    dax_outputs: list[DAXTranslationResult] = []
    tmsl_result: Optional[ModelBuildResult] = None

    for workbook_entry in manifest.workbooks:
        log.info(f"processing_workbook {workbook_entry.name}")
        workbook = TableauWorkbook.from_file(Path(workbook_entry.path))
        classification = classifier.classify(workbook)
        log.info(
            f"classification strategy={classification.strategy} "
            f"rationale={classification.summary()} workbook={workbook_entry.name}"
        )
        translation = translator.translate_workbook(workbook)
        dax_outputs.append(translation)
        if tmsl_result is None:
            tmsl_result = builder.build_model(manifest, dax_outputs)

    if tmsl_result is None:
        raise typer.Exit(code=1)

    tmsl_path = output_dir / "dataset.tmsl.json"
    tmsl_path.write_text(tmsl_result.tmsl_json)
    log.info(f"wrote_tmsl path={tmsl_path}")

    dax_md = output_dir / "measures.dax.md"
    dax_md.write_text("\n\n".join(result.measures_markdown for result in dax_outputs))
    log.info(f"wrote_dax path={dax_md}")

    if publish and not dry_run:
        publisher.publish_dataset(tmsl_result)
    else:
        log.info(f"publish_skipped dry_run={dry_run}")

    report = None
    if validate:
        report = validator.validate(manifest, dax_outputs)
        report_path = output_dir / "migration_report.json"
        report_path.write_text(report.json(indent=2))
        log.info(f"wrote_report path={report_path}")

    md_report = output_dir / "migration_report.md"
    md_report.write_text((report or MigrationReport()).to_markdown())
    log.info(f"wrote_report_md path={md_report}")


@app.command()
def translate(
    twb: Path = typer.Option(..., "--twb", help="Tableau workbook path"),
    out: Path = typer.Option(Path("out/measures.dax.md"), "--out", help="Output markdown"),
) -> None:
    """Translate calculated fields from a Tableau workbook to DAX markdown."""

    configure_logging(False)
    workbook = TableauWorkbook.from_file(twb)
    translator = TableauTranslator()
    result = translator.translate_workbook(workbook)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.measures_markdown)


@app.command("build-model")
def build_model(
    manifest: Path = typer.Option(..., "--manifest", help="Manifest file"),
    export_tmsl: Path = typer.Option(Path("out/dataset.tmsl.json"), "--export-tmsl"),
    settings: Path = typer.Option(
        DEFAULT_SETTINGS_PATH,
        "--settings",
        help="Settings file path (defaults to config/settings.yaml, falls back to example)",
    ),
) -> None:
    """Generate TMSL JSON for the manifest without publishing."""

    configure_logging(False)
    manifest_model = load_manifest(manifest)
    settings_model = _load_settings_file(settings)
    translator = TableauTranslator()
    dax_outputs: list[DAXTranslationResult] = []
    for workbook_entry in manifest_model.workbooks:
        workbook = TableauWorkbook.from_file(Path(workbook_entry.path))
        dax_outputs.append(translator.translate_workbook(workbook))
    builder = TMSLBuilder(settings=settings_model)
    result = builder.build_model(manifest_model, dax_outputs)
    export_tmsl.parent.mkdir(parents=True, exist_ok=True)
    export_tmsl.write_text(result.tmsl_json)


@app.command()
def publish(
    tmsl: Path = typer.Option(..., "--tmsl", help="TMSL JSON path"),
    workspace_id: str = typer.Option(..., "--workspace-id", help="Target workspace"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    settings: Path = typer.Option(
        DEFAULT_SETTINGS_PATH,
        "--settings",
        help="Settings file path (defaults to config/settings.yaml, falls back to example)",
    ),
) -> None:
    """Publish a pre-generated TMSL model to Power BI."""

    configure_logging(False)
    settings_model = _load_settings_file(settings)
    result = ModelBuildResult(tmsl_json=tmsl.read_text(), measures=[])
    publisher = PowerBIPublisher(settings=settings_model)
    publisher.publish_dataset(result, workspace_override=workspace_id, dry_run=dry_run)


@app.command()
def validate(
    report: Path = typer.Option(Path("out/migration_report.md"), "--report", help="Report path"),
) -> None:
    """Generate an empty validation report placeholder."""

    configure_logging(False)
    MigrationReport().to_markdown(path=report)


if __name__ == "__main__":
    app()
