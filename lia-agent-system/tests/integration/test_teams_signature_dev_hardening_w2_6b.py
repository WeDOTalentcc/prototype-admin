"""
Integration tests — W2.6.b: P1-5 webhook signature dev = open door.

Auditoria 2026-04-26 (P1-5):
  if APP_ENV != "production" and TEAMS_WEBHOOK_SECRET vazio: allow-all com warning
  Em deploy mal configurado (APP_ENV typo, e.g. "Production" lowercase quebrado),
  bypass silencioso. Production stays open.

Fix W2.6.b — 3-state:
  - production: secret obrigatorio (ja era)
  - non-production COM TEAMS_WEBHOOK_DEV_BYPASS=true explicito: allow-all
  - non-production SEM bypass flag: ainda exige secret (fail-closed default)
"""
from __future__ import annotations
import inspect
import pytest


class TestWebhookSignatureDevHardening:
    def test_dev_bypass_requires_explicit_flag(self):
        """
        Source must reference TEAMS_WEBHOOK_DEV_BYPASS env var.
        Without explicit opt-in, dev mode no longer allows requests without
        TEAMS_WEBHOOK_SECRET.
        """
        import app.api.v1.teams as mod
        src = inspect.getsource(mod._verify_teams_webhook_signature)
        assert "TEAMS_WEBHOOK_DEV_BYPASS" in src, (
            "_verify_teams_webhook_signature must check TEAMS_WEBHOOK_DEV_BYPASS "
            "explicit flag for dev bypass (P1-5)"
        )

    def test_no_implicit_dev_bypass(self):
        """
        Source must NOT contain the previous implicit pattern (return True
        based only on `not teams_webhook_secret`).
        """
        import app.api.v1.teams as mod
        src = inspect.getsource(mod._verify_teams_webhook_signature)
        # Old pattern: warning + return True without bypass flag check
        bad_pattern = 'if not teams_webhook_secret:\n        logger.warning("[TEAMS WEBHOOK] TEAMS_WEBHOOK_SECRET not configured, skipping signature verification (development mode only)")\n        return True'
        assert bad_pattern not in src, (
            "P1-5 fix: implicit dev bypass removed. Use TEAMS_WEBHOOK_DEV_BYPASS=true."
        )
