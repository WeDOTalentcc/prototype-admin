"""
F-16 P1 sentinels: FairnessGuard fail-CLOSED on engine failure.

Audit: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-16.
Decisao Paulo 2026-05-22: fail-CLOSED quando guard cair (nao passar raw text).

Sentinels:
- F1 Engine exception -> scripted safe fallback (NAO retorna raw text)
- F2 Engine timeout -> scripted safe fallback
- F3 Clean text passes through (no false positive)
- F4 is_blocked=True -> scripted safe fallback (existing behavior)
- F5 Engine failure registra canonical audit (LGPD Art. 20 trail)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_session(company_id="company-test", session_id="s-fairness-test", candidate_id="cand-1"):
    """Build a minimal VoiceScreeningSession-like object."""
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningSession
    return VoiceScreeningSession(
        session_id=session_id,
        candidate_id=candidate_id,
        candidate_name="Test Candidate",
        job_title="Test Job",
        company_id=company_id,
        phone_number="+5511999999999",
        job_id="job-x",
        status="active",
    )


def _orchestrator():
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
    return VoiceScreeningOrchestrator()


def test_fairness_engine_exception_uses_scripted_fallback():
    """F1: guard exception -> NAO retorna raw text, retorna scripted safe."""
    orch = _orchestrator()
    session = _make_session()
    raw_text = "Texto raw potencialmente problemático que NAO PODE vazar"

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
        side_effect=RuntimeError("simulated engine crash"),
    ):
        result = orch._check_fairness_on_response(raw_text, session)

    assert result != raw_text, (
        "F-16 fail-CLOSED: exception no guard NAO pode resultar em raw text passando through"
    )
    # Scripted fallback canonical: "Poderia me contar mais sobre..." OR generic neutral.
    assert result and isinstance(result, str), "Fallback deve retornar string nao-vazia"


def test_fairness_engine_timeout_uses_scripted_fallback():
    """F2: TimeoutError tambem cai em fail-CLOSED."""
    orch = _orchestrator()
    session = _make_session()
    raw_text = "Texto que nao deveria vazar"

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
        side_effect=TimeoutError("engine timeout"),
    ):
        result = orch._check_fairness_on_response(raw_text, session)

    assert result != raw_text, "F-16 timeout fail-CLOSED ativo"


def test_fairness_clean_text_passes_through():
    """F3: texto limpo (is_blocked=False) passa sem alteracao."""
    orch = _orchestrator()
    session = _make_session()
    clean_text = "Conte-me sobre sua experiência profissional."

    mock_result = MagicMock()
    mock_result.is_blocked = False

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
        return_value=mock_result,
    ):
        result = orch._check_fairness_on_response(clean_text, session)

    assert result == clean_text, "Texto limpo deve passar pelo guard sem alteracao"


def test_fairness_blocked_uses_scripted_fallback():
    """F4: is_blocked=True -> safe fallback (mantido)."""
    orch = _orchestrator()
    session = _make_session()
    risky_text = "Texto sinalizado pelo guard"

    mock_result = MagicMock()
    mock_result.is_blocked = True

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
        return_value=mock_result,
    ):
        result = orch._check_fairness_on_response(risky_text, session)

    assert result != risky_text, "is_blocked=True deve substituir texto risky"


def test_fairness_exception_logs_canonical_audit():
    """F5: exception no guard registra log_decision canonical (LGPD Art. 20)."""
    orch = _orchestrator()
    session = _make_session()
    raw_text = "texto que vai disparar fail-closed"

    with patch(
        "app.domains.voice.services.voice_screening_orchestrator.check_fairness",
        side_effect=RuntimeError("simulated crash"),
    ), patch(
        "app.shared.compliance.audit_service.AuditService"
    ) as MockAudit:
        mock_audit_instance = MagicMock()
        # log_decision is async — return a completed awaitable
        async def _async_noop(*args, **kwargs): return None
        mock_audit_instance.log_decision = MagicMock(side_effect=_async_noop)
        MockAudit.return_value = mock_audit_instance

        result = orch._check_fairness_on_response(raw_text, session)

    # Audit log_decision foi chamado com decision_type canonical
    assert MockAudit.called, "AuditService deve ser instanciado em fail-CLOSED"
    call_args = mock_audit_instance.log_decision.call_args
    if call_args is not None:
        kwargs = call_args.kwargs
        assert kwargs.get("decision_type") == "fairness_guard_failure", (
            f"decision_type deve ser fairness_guard_failure, got {kwargs.get('decision_type')}"
        )
        assert kwargs.get("agent_name") == "voice_screening_orchestrator"
        assert kwargs.get("company_id") == session.company_id
        # human_review_required True (escalada)
        assert kwargs.get("human_review_required") is True

    assert result != raw_text, "fail-CLOSED ativo mesmo com audit"
