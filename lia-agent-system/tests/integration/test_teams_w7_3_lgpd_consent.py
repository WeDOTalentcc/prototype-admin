"""W7.3 — LGPD consent gate blocks WhatsApp screening when consent absent/revoked."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


@dataclass
class _ConsentGateResult:
    allowed: bool
    reason: str
    consent_type: str = "WHATSAPP"
    candidate_id: str = "c1"
    channel: str = "whatsapp"


# ─── helpers ───────────────────────────────────────────────────────────────────

def _make_payload(**kwargs):
    defaults = dict(
        candidate_id="c1",
        candidate_name="Maria",
        candidate_phone="+5511999990000",
        vacancy_id="v1",
        vacancy_title="Engenheira",
        recruiter_id="r1",
        recruiter_name="João",
        notes=None,
        action="approve",
    )
    defaults.update(kwargs)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


async def _run_approve(consent_result: _ConsentGateResult):
    """Call _handle_approve_action with a mocked consent gate."""
    from app.api.v1.teams import _handle_approve_action

    mock_db = AsyncMock()
    mock_gate = AsyncMock()
    mock_gate.check.return_value = consent_result

    with (
        patch("app.api.v1.teams.CommunicationConsentGate", return_value=mock_gate),
        patch("app.api.v1.teams._log_teams_action_audit", new_callable=AsyncMock) as mock_audit,
        patch("app.api.v1.teams._start_whatsapp_screening", new_callable=AsyncMock) as mock_screen,
    ):
        mock_audit.return_value = "audit-1"
        mock_screen.return_value = {"success": True, "message_id": "m1", "mock": False}
        result = await _handle_approve_action(_make_payload(), "company-x", mock_db)
        return result, mock_screen, mock_audit


# ─── tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_approve_blocked_when_consent_absent():
    result, mock_screen, mock_audit = await _run_approve(
        _ConsentGateResult(allowed=False, reason="absent")
    )
    assert result.success is False
    assert "LGPD" in result.message or "consentimento" in result.message.lower()
    mock_screen.assert_not_called()
    mock_audit.assert_called_once()
    call_kwargs = mock_audit.call_args.kwargs
    assert call_kwargs["action"] == "approve_blocked_lgpd_consent"
    assert call_kwargs["result"] == "blocked"


@pytest.mark.asyncio
async def test_approve_blocked_when_consent_revoked():
    result, mock_screen, _ = await _run_approve(
        _ConsentGateResult(allowed=False, reason="revoked")
    )
    assert result.success is False
    assert "revogou" in result.message.lower()
    mock_screen.assert_not_called()


@pytest.mark.asyncio
async def test_approve_proceeds_when_consent_granted():
    result, mock_screen, _ = await _run_approve(
        _ConsentGateResult(allowed=True, reason="granted")
    )
    assert result.success is True
    mock_screen.assert_called_once()


@pytest.mark.asyncio
async def test_approve_blocked_on_check_error():
    result, mock_screen, _ = await _run_approve(
        _ConsentGateResult(allowed=False, reason="check_error")
    )
    assert result.success is False
    mock_screen.assert_not_called()
