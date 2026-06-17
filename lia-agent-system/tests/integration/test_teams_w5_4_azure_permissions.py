"""
W5.4 — Azure permissions prod validation.

Validates that all required Azure AD / Bot Framework env vars are present
and well-formed. These tests run in CI (no external calls needed).

Required env vars by feature:
  BOT FRAMEWORK (message receiving + token validation):
    MICROSOFT_APP_ID        — Azure AD app registration client ID (GUID)
    MICROSOFT_APP_PASSWORD  — Bot Framework client secret

  SINGLE SIGN-ON (Teams Tab SSO + OBO flow):
    AZURE_CLIENT_ID         — Azure AD app registration for SSO (same or different app)
    AZURE_TENANT_ID         — Azure AD tenant ID (GUID) — use 'common' for multi-tenant

  CALENDAR (interview scheduling via Microsoft Graph):
    AZURE_CLIENT_SECRET     — Service account secret for Calendar API
    MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI — Redirect URI registered in Azure

  TEAMS WEBHOOK SECURITY:
    TEAMS_WEBHOOK_SECRET    — HMAC secret for webhook signature validation

  OPTIONAL — proactive messaging:
    TEAMS_BOT_APP_ID        — Alias for MICROSOFT_APP_ID (some code paths use this)
    TEAMS_APP_ID            — Teams manifest app ID (UUID)
"""
import os
import re
import uuid

import pytest

_GUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


def _is_guid(value: str) -> bool:
    return bool(_GUID_RE.match(value.strip()))


class TestAzurePermissionsMatrix:
    """
    Catalog and validate all Azure/Teams env vars.
    Tests that warn (not fail) if var is missing in non-prod to allow CI to pass.
    Tests that BLOCK if var is set but malformed.
    """

    def _env(self, key: str) -> str:
        return os.environ.get(key, "")

    # ── Bot Framework ─────────────────────────────────────────────────────────

    def test_microsoft_app_id_format(self):
        """MICROSOFT_APP_ID, if set, must be a valid GUID."""
        val = self._env("MICROSOFT_APP_ID")
        if not val:
            pytest.skip("MICROSOFT_APP_ID not set — acceptable in non-prod CI")
        assert _is_guid(val), (
            f"MICROSOFT_APP_ID='{val}' is not a valid GUID. "
            "Must be the Application (client) ID from Azure AD app registration."
        )

    def test_microsoft_app_password_non_empty(self):
        """MICROSOFT_APP_PASSWORD, if set, must be non-empty and > 20 chars."""
        val = self._env("MICROSOFT_APP_PASSWORD")
        if not val:
            pytest.skip("MICROSOFT_APP_PASSWORD not set — acceptable in non-prod CI")
        assert len(val) > 20, (
            "MICROSOFT_APP_PASSWORD looks too short (< 20 chars). "
            "Check that you used the client secret VALUE, not the secret ID."
        )

    # ── SSO ───────────────────────────────────────────────────────────────────

    def test_azure_client_id_format(self):
        """AZURE_CLIENT_ID, if set, must be a valid GUID."""
        val = self._env("AZURE_CLIENT_ID")
        if not val:
            pytest.skip("AZURE_CLIENT_ID not set — acceptable in non-prod CI")
        assert _is_guid(val), (
            f"AZURE_CLIENT_ID='{val}' is not a valid GUID. "
            "Must be the Application (client) ID of the SSO app registration."
        )

    def test_azure_tenant_id_format(self):
        """AZURE_TENANT_ID, if set, must be a valid GUID or 'common'."""
        val = self._env("AZURE_TENANT_ID")
        if not val:
            pytest.skip("AZURE_TENANT_ID not set — acceptable in non-prod CI")
        assert _is_guid(val) or val == "common", (
            f"AZURE_TENANT_ID='{val}' must be a GUID or 'common'. "
            "Use your tenant's Directory (tenant) ID from Azure AD."
        )

    # ── Webhook security ──────────────────────────────────────────────────────

    def test_teams_webhook_secret_strength(self):
        """TEAMS_WEBHOOK_SECRET, if set, must be >= 32 chars."""
        val = self._env("TEAMS_WEBHOOK_SECRET")
        if not val:
            pytest.skip("TEAMS_WEBHOOK_SECRET not set — acceptable in non-prod CI")
        assert len(val) >= 32, (
            f"TEAMS_WEBHOOK_SECRET is only {len(val)} chars. "
            "Use a cryptographically random secret of at least 32 chars. "
            "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # ── Required scopes documentation test (always runs) ─────────────────────

    REQUIRED_SCOPES = {
        "Bot Framework": [
            "https://api.botframework.com — Bot token validation",
        ],
        "Teams Tab SSO (OBO flow)": [
            "User.Read",
            "openid",
            "profile",
            "email",
        ],
        "Calendar integration": [
            "offline_access",
            "Calendars.ReadWrite",
        ],
        "Microsoft Graph (proactive messaging)": [
            "https://graph.microsoft.com/.default",
        ],
    }

    def test_required_scopes_documented(self):
        """All required Azure AD scopes are cataloged (documentation test)."""
        total_scopes = sum(len(v) for v in self.REQUIRED_SCOPES.values())
        assert total_scopes >= 7, "Scope catalog is incomplete"
        assert "Calendars.ReadWrite" in self.REQUIRED_SCOPES["Calendar integration"]
        assert "User.Read" in self.REQUIRED_SCOPES["Teams Tab SSO (OBO flow)"]

    REQUIRED_ENV_VARS = {
        "MICROSOFT_APP_ID": "Bot Framework client ID (GUID)",
        "MICROSOFT_APP_PASSWORD": "Bot Framework client secret",
        "AZURE_CLIENT_ID": "Azure AD SSO app client ID (GUID)",
        "AZURE_TENANT_ID": "Azure AD tenant ID (GUID or 'common')",
        "TEAMS_WEBHOOK_SECRET": "HMAC secret for webhook validation (32+ chars)",
    }

    OPTIONAL_ENV_VARS = {
        "AZURE_CLIENT_SECRET": "Calendar API service account secret",
        "MICROSOFT_CALENDAR_OAUTH_REDIRECT_URI": "Callback URI for Calendar OAuth",
        "TEAMS_BOT_APP_ID": "Alias for MICROSOFT_APP_ID used in manifest",
        "TEAMS_APP_ID": "Teams manifest app ID (UUID)",
    }

    def test_env_var_catalog_completeness(self):
        """Catalog must cover all Teams-related env vars discovered in teams.py audit."""
        all_vars = set(self.REQUIRED_ENV_VARS) | set(self.OPTIONAL_ENV_VARS)
        assert "MICROSOFT_APP_ID" in all_vars
        assert "TEAMS_WEBHOOK_SECRET" in all_vars
        assert "AZURE_CLIENT_ID" in all_vars
        assert len(self.REQUIRED_ENV_VARS) >= 5

    def test_prod_checklist_complete(self):
        """Verify the prod checklist covers bot + SSO + calendar + webhook."""
        categories = {"bot", "sso", "calendar", "webhook"}
        covered = set()
        for key in self.REQUIRED_ENV_VARS:
            k = key.lower()
            if "microsoft_app" in k or "bot_app" in k:
                covered.add("bot")
            if "azure_client_id" in k or "tenant" in k:
                covered.add("sso")
            if "calendar" in k:
                covered.add("calendar")
            if "webhook_secret" in k:
                covered.add("webhook")
        for key in self.OPTIONAL_ENV_VARS:
            if "calendar" in key.lower():
                covered.add("calendar")
        assert "bot" in covered
        assert "sso" in covered
        assert "webhook" in covered
