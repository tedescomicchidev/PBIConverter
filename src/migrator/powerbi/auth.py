"""Authentication helpers for Power BI."""

from __future__ import annotations

from dataclasses import dataclass

try:  # pragma: no cover - optional dependency
    from msal import ConfidentialClientApplication  # type: ignore
except Exception:  # pragma: no cover
    ConfidentialClientApplication = None  # type: ignore

from ..config import Settings


@dataclass
class AuthContext:
    token: str


class PowerBIAuthenticator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def acquire_token(self) -> AuthContext:
        if ConfidentialClientApplication is None:
            return AuthContext(token="")
        app = ConfidentialClientApplication(
            client_id=self.settings.azure.client_id,
            client_credential=self.settings.azure.client_secret,
            authority=f"{self.settings.azure.authority_url}/{self.settings.azure.tenant_id}",
        )
        result = app.acquire_token_for_client(scopes=[self.settings.azure.scope])
        token = result.get("access_token", "")
        return AuthContext(token=token)
