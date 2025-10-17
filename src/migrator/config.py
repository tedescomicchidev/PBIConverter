"""Configuration models for the migrator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback
    yaml = None  # type: ignore

from pydantic import BaseModel, Field


class AzureSettings(BaseModel):
    tenant_id: str = Field(..., alias="tenant_id")
    client_id: str
    client_secret: str
    authority_url: str = "https://login.microsoftonline.com"
    scope: str = "https://analysis.windows.net/powerbi/api/.default"


class NamingSettings(BaseModel):
    dataset_prefix: str = "TB2PBI_"
    report_prefix: str = "TB2PBI_"


class WorkspaceSettings(BaseModel):
    default_workspace_id: str
    xmla_endpoint: str


class GatewaySettings(BaseModel):
    default_gateway_id: Optional[str] = None


class Settings(BaseModel):
    azure: AzureSettings
    naming: NamingSettings = NamingSettings()
    workspaces: WorkspaceSettings
    gateways: GatewaySettings = GatewaySettings()


class WorkbookOptions(BaseModel):
    enforce_transform: bool = False


class WorkbookEntry(BaseModel):
    name: str
    path: str
    project: Optional[str]
    target_workspace: Optional[str]
    strategy: str = Field("auto", description="like|transform|auto")
    options: WorkbookOptions = WorkbookOptions()

    @property
    def resolved_strategy(self) -> str:
        return self.strategy


class Manifest(BaseModel):
    workbooks: List[WorkbookEntry]


def load_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    return json.loads(text or "{}")


def load_settings(path: Path) -> Settings:
    return Settings.parse_obj(load_yaml(path))


def load_manifest(path: Path) -> Manifest:
    return Manifest.parse_obj(load_yaml(path))
