"""Expose the fallback CliRunner under the expected namespace."""

from migrator._compat.typer import CliRunner

__all__ = ["CliRunner"]
