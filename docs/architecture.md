# Architecture Overview

The migrator is composed of loosely coupled modules that expose explicit contracts:

* **Configuration** – `migrator.config` loads settings and manifest files using Pydantic models.
* **Logging** – `migrator.logging` configures Rich structured logging with JSONL output for auditability.
* **Tableau ingestion** – `migrator.tableau.xml_parser` parses Tableau XML files and extracts datasources, worksheets, calculated fields, and metadata required for classification.
* **Formula engine** – `migrator.tableau.tokenizer` and `migrator.tableau.ast` convert Tableau formulas into an abstract syntax tree that feeds the DAX translator.
* **Translator** – `migrator.translate.translator` applies rule-based mappings defined in `migrator.translate.dax_rules` to produce DAX expressions optimised for Power BI best practices.
* **Model builder** – `migrator.model.tmsl_builder` renders TMSL JSON using Jinja2 templates, including a Measures table and canonical Date table.
* **Publisher** – `migrator.powerbi.publisher` authenticates with MSAL and publishes datasets/reports or emits the intended REST calls in dry-run mode.
* **Validation** – `migrator.validation.validators` houses pluggable validation strategies that compare Tableau and Power BI outputs.

## Workflow

1. The CLI ingests the manifest and Tableau files.
2. Each workbook is classified as like-for-like or transform with rationale logging.
3. Calculated fields are parsed, translated to DAX, and added to the Measures table.
4. The Tabular model is rendered to TMSL and optionally published via the REST/XMLA endpoints.
5. Validation reports summarise parity metrics.

## Extensibility

The repository favours explicit interfaces and dataclasses to enable testing. The AST and translator layers support incremental expansion by adding new node types and mapping rules. The publisher and validator modules are written to allow dependency injection for external services.
