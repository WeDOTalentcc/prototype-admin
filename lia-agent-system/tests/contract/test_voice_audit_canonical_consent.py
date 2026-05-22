"""
Tests for F-04 (P0 LGPD): Audit canonical em verify_consent.

LGPD Art. 7 + Lei 13.853/2019 exigem trail imutável de toda decisão automatizada
de consent (allowed/blocked/warning). Antes do fix, verify_consent só fazia
logger.warning/error — sem persist em audit_logs table.

Audit ref: ~/Documents/wedotalent_audit_2026-05-21/AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-04

This test pins:
- granted   → AuditService.log_decision called with decision="allowed"
- revoked   → AuditService.log_decision called with decision="blocked" + raise
- absent    → AuditService.log_decision called with decision="blocked" + raise
- db=None   → AuditService.log_decision called with decision="blocked" + raise (or skipped if no db)
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.voice.services.voice_screening_orchestrator import (
    ConsentNotGrantedError,
    VoiceScreeningOrchestrator,
)


def _make_orch() -> VoiceScreeningOrchestrator:
    """Construct orchestrator (no-arg constructor)."""
    return VoiceScreeningOrchestrator()


def _make_mock_db() -> MagicMock:
    db = MagicMock()
    db.execute = AsyncMock()
    return db


def _make_consent_result(allowed: bool, soft_warning: bool = False):
    """Build a fake ConsentCheckResult."""
    return SimpleNamespace(allowed=allowed, soft_warning=soft_warning, reason="test")


@pytest.mark.asyncio
async def test_consent_granted_logs_audit_decision_allowed():
    """Path: explicit consent granted → audit row decision='allowed'."""
    orch = _make_orch()
    db = _make_mock_db()

    fake_checker_cls = MagicMock()
    fake_checker = MagicMock()
    fake_checker.check_candidate_consent = AsyncMock(
        return_value=_make_consent_result(allowed=True)
    )
    fake_checker_cls.return_value = fake_checker

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService",
        fake_checker_cls,
    ), patch(
        "app.domains.voice.services.voice_screening_orchestrator.AuditService",
        return_value=mock_audit,
    ):
        result = await orch.verify_consent(
            candidate_id="cand-uuid-1",
            company_id="comp-uuid-1",
            db=db,
        )

    assert result is True
    assert mock_audit.log_decision.await_count == 1
    call_kwargs = mock_audit.log_decision.await_args.kwargs
    assert call_kwargs["company_id"] == "comp-uuid-1"
    assert call_kwargs["agent_name"] == "voice_screening_orchestrator"
    assert call_kwargs["decision_type"] == "voice_consent_check"
    assert call_kwargs["decision"] == "allowed"
    assert call_kwargs["candidate_id"] == "cand-uuid-1"


@pytest.mark.asyncio
async def test_consent_revoked_logs_audit_decision_blocked():
    """Path: consent revoked → audit row decision='blocked' + raise."""
    orch = _make_orch()
    db = _make_mock_db()

    fake_checker_cls = MagicMock()
    fake_checker = MagicMock()
    fake_checker.check_candidate_consent = AsyncMock(
        return_value=_make_consent_result(allowed=False)
    )
    fake_checker_cls.return_value = fake_checker

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService",
        fake_checker_cls,
    ), patch(
        "app.domains.voice.services.voice_screening_orchestrator.AuditService",
        return_value=mock_audit,
    ):
        with pytest.raises(ConsentNotGrantedError):
            await orch.verify_consent(
                candidate_id="cand-uuid-2",
                company_id="comp-uuid-2",
                db=db,
            )

    assert mock_audit.log_decision.await_count == 1
    call_kwargs = mock_audit.log_decision.await_args.kwargs
    assert call_kwargs["decision"] == "blocked"
    assert call_kwargs["candidate_id"] == "cand-uuid-2"


@pytest.mark.asyncio
async def test_consent_absent_soft_warning_logs_audit_decision_blocked():
    """Path: consent absent (soft_warning) → audit row decision='blocked' + raise.

    LGPD Art. 7: prior explicit consent é OBRIGATÓRIO. soft_warning não é suficiente
    para outbound voice call — bloqueia hard.
    """
    orch = _make_orch()
    db = _make_mock_db()

    fake_checker_cls = MagicMock()
    fake_checker = MagicMock()
    fake_checker.check_candidate_consent = AsyncMock(
        return_value=_make_consent_result(allowed=True, soft_warning=True)
    )
    fake_checker_cls.return_value = fake_checker

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService",
        fake_checker_cls,
    ), patch(
        "app.domains.voice.services.voice_screening_orchestrator.AuditService",
        return_value=mock_audit,
    ):
        with pytest.raises(ConsentNotGrantedError):
            await orch.verify_consent(
                candidate_id="cand-uuid-3",
                company_id="comp-uuid-3",
                db=db,
            )

    assert mock_audit.log_decision.await_count == 1
    call_kwargs = mock_audit.log_decision.await_args.kwargs
    assert call_kwargs["decision"] == "blocked"


@pytest.mark.asyncio
async def test_consent_db_unavailable_blocks_without_db_audit_attempt():
    """Path: db=None → ConsentNotGrantedError. Audit attempted with no-op since no db.

    Mesmo sem db, deve raisar — defesa em profundidade. Sem db não persiste
    audit (não há sessão), mas registra log estruturado para SIEM.
    """
    orch = _make_orch()

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.AuditService",
        return_value=mock_audit,
    ):
        with pytest.raises(ConsentNotGrantedError):
            await orch.verify_consent(
                candidate_id="cand-uuid-4",
                company_id="comp-uuid-4",
                db=None,
            )


@pytest.mark.asyncio
async def test_consent_check_exception_logs_audit_decision_blocked():
    """Path: ConsentCheckerService raises → audit row decision='blocked' + raise."""
    orch = _make_orch()
    db = _make_mock_db()

    fake_checker_cls = MagicMock()
    fake_checker = MagicMock()
    fake_checker.check_candidate_consent = AsyncMock(
        side_effect=RuntimeError("db connection lost")
    )
    fake_checker_cls.return_value = fake_checker

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator._ConsentCheckerService",
        fake_checker_cls,
    ), patch(
        "app.domains.voice.services.voice_screening_orchestrator.AuditService",
        return_value=mock_audit,
    ):
        with pytest.raises(ConsentNotGrantedError):
            await orch.verify_consent(
                candidate_id="cand-uuid-5",
                company_id="comp-uuid-5",
                db=db,
            )

    # audit invoked with decision=blocked for the check failure path
    assert mock_audit.log_decision.await_count == 1
    call_kwargs = mock_audit.log_decision.await_args.kwargs
    assert call_kwargs["decision"] == "blocked"
