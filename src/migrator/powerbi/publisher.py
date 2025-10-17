"""Dataset publishing helpers."""

from __future__ import annotations

import json
from typing import Optional

import requests

from ..config import Settings
from ..logging import get_logger
from ..model.tmsl_builder import ModelBuildResult
from .auth import PowerBIAuthenticator


class PowerBIPublisher:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.log = get_logger(__name__)
        self.authenticator = PowerBIAuthenticator(settings)

    def publish_dataset(
        self,
        model: ModelBuildResult,
        workspace_override: Optional[str] = None,
        dry_run: bool = True,
    ) -> None:
        workspace_id = workspace_override or self.settings.workspaces.default_workspace_id
        if dry_run:
            self.log.info(f"publish_dry_run workspace={workspace_id} bytes={len(model.tmsl_json)}")
            return
        token = self.authenticator.acquire_token().token
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        endpoint = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/import"
        response = requests.post(endpoint, headers=headers, data=model.tmsl_json)
        if response.status_code >= 300:
            raise RuntimeError(f"Failed to publish dataset: {response.text}")
        self.log.info(f"published_dataset workspace={workspace_id}")
