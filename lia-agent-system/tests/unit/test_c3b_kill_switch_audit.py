"""
Anti-regressão · W3-015 + W3-016 (2026-05-23).

W3-015: FactChecker result wired em c3b_layer.post_compliance (era descartado).
W3-016: LIA_DISABLE_C3B audit event quando kill-switch ativo em prod/staging.
"""
from __future__ import annotations

import importlib
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestW3016KillSwitchAudit:
    """LIA_DISABLE_C3B audit event idempotente."""

    def test_emit_helper_exists(self) -> None:
        import app.shared.compliance.c3b_layer as c3b
        importlib.reload(c3b)
        assert hasattr(c3b, "_emit_c3b_disabled_audit_once")

    @pytest.mark.asyncio
    async def test_audit_emitted_when_disabled_in_prod(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("LIA_DISABLE_C3B", "1")
        monkeypatch.setenv("APP_ENV", "production")
        import app.shared.compliance.c3b_layer as c3b
        importlib.reload(c3b)
        c3b._C3B_DISABLED_AUDIT_EMITTED = False  # reset

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        with patch("app.shared.compliance.audit_service.audit_service", mock_audit):
            await c3b._emit_c3b_disabled_audit_once()

        assert mock_audit.log_decision.called, (
            "Audit event DEVE ser emitido em prod com LIA_DISABLE_C3B=1"
        )
        call_kwargs = mock_audit.log_decision.call_args.kwargs
        assert call_kwargs.get("decision_type") == "compliance_disabled"
        assert call_kwargs.get("action") == "kill_switch_active"

    @pytest.mark.asyncio
    async def test_audit_skipped_in_dev(self, monkeypatch) -> None:
        monkeypatch.setenv("LIA_DISABLE_C3B", "1")
        monkeypatch.setenv("APP_ENV", "development")
        import app.shared.compliance.c3b_layer as c3b
        importlib.reload(c3b)
        c3b._C3B_DISABLED_AUDIT_EMITTED = False

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        with patch("app.shared.compliance.audit_service.audit_service", mock_audit):
            await c3b._emit_c3b_disabled_audit_once()

        assert not mock_audit.log_decision.called, (
            "Audit event NÃO deve ser emitido em dev (warn-only)"
        )

    @pytest.mark.asyncio
    async def test_audit_idempotent(self, monkeypatch) -> None:
        """2ª call não emite novo audit (flag idempotente)."""
        monkeypatch.setenv("LIA_DISABLE_C3B", "1")
        monkeypatch.setenv("APP_ENV", "production")
        import app.shared.compliance.c3b_layer as c3b
        importlib.reload(c3b)
        c3b._C3B_DISABLED_AUDIT_EMITTED = False

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        with patch("app.shared.compliance.audit_service.audit_service", mock_audit):
            await c3b._emit_c3b_disabled_audit_once()
            await c3b._emit_c3b_disabled_audit_once()
            await c3b._emit_c3b_disabled_audit_once()

        assert mock_audit.log_decision.call_count == 1, (
            "Audit deve ser emitido APENAS na 1ª call (idempotente)"
        )


class TestW3015FactCheckerWired:
    """FactChecker result não-mais descartado em post_compliance."""

    def test_post_compliance_uses_fc_metadata(self) -> None:
        """Source-level: post_compliance referencia fc_metadata + fc_inaccurate."""
        from pathlib import Path

        c3b_path = (
            Path(__file__).resolve().parents[2]
            / "app"
            / "shared"
            / "compliance"
            / "c3b_layer.py"
        )
        src = c3b_path.read_text()
        assert "fc_inaccurate" in src, (
            "c3b_layer.post_compliance DEVE captar inaccurate_claims do FactChecker"
        )
        assert "fact_check_inaccurate" in src or "fc_result.to_metadata" in src, (
            "c3b_layer.post_compliance DEVE wire FactChecker result em audit"
        )
