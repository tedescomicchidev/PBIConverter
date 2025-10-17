"""Convenience wrapper for CI dry-run migrations."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    manifest = Path("config/manifest.sample.yaml")
    subprocess.check_call([
        "python",
        "-m",
        "migrator.cli",
        "migrate",
        "--input",
        str(manifest),
        "--dry-run",
    ])


if __name__ == "__main__":
    main()
