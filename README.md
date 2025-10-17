# PBIConverter

PBIConverter automates migrations from Tableau workbooks to Power BI datasets. It provides a command line interface and Python API for parsing Tableau metadata, translating calculated fields to DAX, generating Tabular models, and optionally publishing to Power BI.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp config/settings.example.yaml config/settings.yaml
cp config/manifest.sample.yaml config/manifest.yaml
migrator migrate --input config/manifest.yaml --dry-run
```

## Configuration

The tool consumes two primary configuration files:

* `config/settings.yaml` – tenant, workspace, and naming conventions.
* `config/manifest.yaml` – list of Tableau workbooks and migration options.

Refer to the example files in the `config/` directory for the expected structure.

## CLI Overview

* `migrator migrate --input config/manifest.yaml --dry-run`
* `migrator translate --twb path/to/file.twb --out out/measures.dax.md`
* `migrator build-model --manifest config/manifest.yaml --export-tmsl out/dataset.tmsl.json`
* `migrator publish --tmsl out/dataset.tmsl.json --workspace-id <GUID>`
* `migrator validate --report out/migration_report.md`

## When to transform vs like-for-like

The CLI automatically classifies each workbook using heuristics. Like-for-like migrations are preferred when:

* No order-dependent table calculations are present.
* All views share a single grain and can map cleanly to a star schema.
* Only supported functions are used in calculated fields.

Transformative migrations are triggered when:

* Level-of-detail expressions span multiple grains.
* Table calculations require ordering (`WINDOW_*`, `RUNNING_*`).
* Complex parameters, user filters, or unions require semantic modeling changes.

## Limitations

* Order-dependent table calculations emit TODO notes and require manual validation.
* Custom visuals and Tableau extensions are not automatically recreated.
* Network operations are skipped in `--dry-run`; ensure permissions when publishing.

## Development

* Run `ruff`, `black`, and `mypy` before committing.
* Execute `pytest --cov` to run the unit test suite.
* `scripts/run_migration.py` wraps a typical dry-run migration for CI.

## Architecture

See `docs/architecture.md` for a high-level overview and `docs/mapping_catalogue.md` for translation mappings.
