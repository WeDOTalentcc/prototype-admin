"""
F-03 P1 sentinels: canonical audit em initiate_call + finalize_screening.

Audit: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-03.
LGPD Art. 20 + EU AI Act Art. 12 exigem trail de "decisao automatizada
com efeitos significativos". initiate_call (decide ligar) e finalize_screening
(gera score WSI + recomendacao) sao decisoes automatizadas com efeito.

Sentinels:
- A1 initiate_call sucesso (call_sid retornado) -> log_decision canonical
- A2 initiate_call fallback (circuit open) -> log_decision com status degraded
- A3 finalize_screening sucesso WSI -> log_decision com wsi_score
- A4 finalize_screening sem WSI score -> log_decision com action=session_closed_no_score
- A5 audit inclui campos canonical: decision_type, agent_name, criteria_used, candidate_id
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


def _orchestrator():
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
    return VoiceScreeningOrchestrator()


def _make_session(session_id="s-audit-test", company_id="comp-audit", call_sid=None):
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningSession
    return VoiceScreeningSession(
        session_id=session_id,
        candidate_id="cand-x",
        candidate_name="Audit Test",
        job_title="Audit Job",
        company_id=company_id,
        phone_number="+5511999999999",
        job_id="job-audit",
        status="initiated",
        call_sid=call_sid,
        started_at=datetime.utcnow(),
    )


# ─── A1: initiate_call success ─────────────────────────────────────────────────

async def test_initiate_call_logs_audit_when_twilio_call_sid_returned():
    """A1: call sucesso -> log_decision com decision_type=voice_call_initiated."""
    orch = _orchestrator()

    fake_call_result = {"success": True, "call_sid": "CA_FAKE_001"}

    with patch.object(orch, "verify_consent", new=AsyncMock(return_value=None)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "_register_wsi_session", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator.TWILIO_VOICE_CIRCUIT.call",
               new=AsyncMock(return_value=fake_call_result)), \
         patch("app.domains.voice.services.voice_screening_orchestrator.AuditService") as MockAudit:

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        MockAudit.return_value = mock_audit

        result = await orch.initiate_call(
            candidate_id="cand-x",
            candidate_name="Audit Test",
            phone_number="+5511999999999",
            job_title="Audit Job",
            company_id="comp-audit",
            job_id="job-audit",
            db=None,
        )

    assert result.status == "initiated", f"Status esperado initiated, got {result.status}"
    assert mock_audit.log_decision.called, "F-03 A1: log_decision deve ser chamado em initiate_call sucesso"

    kwargs = mock_audit.log_decision.call_args.kwargs
    assert kwargs.get("decision_type") == "voice_call_initiated", (
        f"decision_type esperado voice_call_initiated, got {kwargs.get('decision_type')}"
    )
    assert kwargs.get("agent_name") == "voice_screening_orchestrator"
    assert kwargs.get("company_id") == "comp-audit"
    assert kwargs.get("candidate_id") == "cand-x"


# ─── A2: initiate_call fallback (circuit open) ────────────────────────────────

async def test_initiate_call_logs_audit_with_fallback_status_when_circuit_open():
    """A2: circuit open -> log_decision com action=fallback_to_chat."""
    from app.shared.resilience.circuit_breaker import CircuitBreakerError

    orch = _orchestrator()

    circuit_err = CircuitBreakerError("twilio_voice", retry_after=30.0)

    with patch.object(orch, "verify_consent", new=AsyncMock(return_value=None)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator.TWILIO_VOICE_CIRCUIT.call",
               new=AsyncMock(side_effect=circuit_err)), \
         patch("app.domains.voice.services.voice_screening_orchestrator.AuditService") as MockAudit:

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        MockAudit.return_value = mock_audit

        result = await orch.initiate_call(
            candidate_id="cand-fb",
            candidate_name="FB Test",
            phone_number="+5511888888888",
            job_title="FB Job",
            company_id="comp-fb",
            db=None,
        )

    assert result.status == "fallback", f"Status esperado fallback, got {result.status}"
    assert mock_audit.log_decision.called, "F-03 A2: log_decision deve ser chamado mesmo em fallback"

    kwargs = mock_audit.log_decision.call_args.kwargs
    assert kwargs.get("decision_type") == "voice_call_initiated"
    assert kwargs.get("action") == "fallback_to_chat", (
        f"action esperado fallback_to_chat, got {kwargs.get('action')}"
    )


# ─── A3: finalize_screening success ───────────────────────────────────────────

async def test_finalize_screening_logs_audit_with_wsi_score():
    """A3: finalize com wsi result -> log_decision com decision_type=voice_screening_finalized."""
    orch = _orchestrator()
    session = _make_session(call_sid="CA_FAKE", session_id="s-finalize-1")
    session.transcript_segments = [
        {"role": "lia", "text": "Olá!"},
        {"role": "candidate", "text": "Oi, tudo bem."},
    ]

    fake_wsi = {"overall_evaluation": {"overall_score": 8.5}, "recommendation": "advance"}

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator", None), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               new=AsyncMock(return_value=fake_wsi)), \
         patch("app.domains.voice.services.voice_screening_orchestrator.AuditService") as MockAudit:

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        MockAudit.return_value = mock_audit

        result = await orch.finalize_screening(session_id="s-finalize-1", db=None)

    assert result["status"] == "completed", f"Status esperado completed, got {result['status']}"
    assert mock_audit.log_decision.called, "F-03 A3: log_decision deve ser chamado em finalize sucesso"

    kwargs = mock_audit.log_decision.call_args.kwargs
    assert kwargs.get("decision_type") == "voice_screening_finalized", (
        f"decision_type esperado voice_screening_finalized, got {kwargs.get('decision_type')}"
    )
    assert kwargs.get("action") == "wsi_score_computed", (
        f"action esperado wsi_score_computed, got {kwargs.get('action')}"
    )
    # WSI score deve estar no reasoning
    reasoning_str = " ".join(str(r) for r in kwargs.get("reasoning", []))
    assert "wsi_score" in reasoning_str.lower() or "8.5" in reasoning_str, (
        f"reasoning deveria conter wsi_score: {kwargs.get('reasoning')}"
    )


# ─── A4: finalize_screening WSI failure ───────────────────────────────────────

async def test_finalize_screening_logs_audit_when_wsi_unavailable():
    """A4: finalize sem score -> log_decision com action=session_closed_no_score."""
    orch = _orchestrator()
    session = _make_session(call_sid=None, session_id="s-finalize-no-wsi")
    session.transcript_segments = [{"role": "lia", "text": "test"}]

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator", None), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening", None), \
         patch("app.domains.voice.services.voice_screening_orchestrator.AuditService") as MockAudit:

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        MockAudit.return_value = mock_audit

        result = await orch.finalize_screening(session_id="s-finalize-no-wsi", db=None)

    assert result["status"] == "analysis_failed", f"Status esperado analysis_failed, got {result['status']}"
    assert mock_audit.log_decision.called, "F-03 A4: log_decision deve ser chamado mesmo em WSI failure"

    kwargs = mock_audit.log_decision.call_args.kwargs
    assert kwargs.get("decision_type") == "voice_screening_finalized"
    assert kwargs.get("action") == "session_closed_no_score", (
        f"action esperado session_closed_no_score, got {kwargs.get('action')}"
    )


# ─── A5: campos canonical estao presentes ─────────────────────────────────────

async def test_audit_includes_canonical_fields():
    """A5: audit em initiate_call inclui todos campos canonical obrigatorios."""
    orch = _orchestrator()
    fake_call_result = {"success": True, "call_sid": "CA_CANON_FIELDS"}

    with patch.object(orch, "verify_consent", new=AsyncMock(return_value=None)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "_register_wsi_session", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator.TWILIO_VOICE_CIRCUIT.call",
               new=AsyncMock(return_value=fake_call_result)), \
         patch("app.domains.voice.services.voice_screening_orchestrator.AuditService") as MockAudit:

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        MockAudit.return_value = mock_audit

        await orch.initiate_call(
            candidate_id="cand-canon",
            candidate_name="Canon Test",
            phone_number="+5511777777777",
            job_title="Canon Job",
            company_id="comp-canon",
            job_id="job-canon",
            db=None,
        )

    kwargs = mock_audit.log_decision.call_args.kwargs
    # Canonical AuditService.log_decision fields:
    for required in ("company_id", "agent_name", "decision_type", "action", "decision",
                     "reasoning", "criteria_used", "criteria_ignored", "candidate_id"):
        assert required in kwargs, f"F-03 A5: campo canonical {required} ausente no log_decision"

    # PROTECTED_CRITERIA_PT deve aparecer em criteria_ignored (LGPD)
    from app.shared.services.automated_decision_logger import PROTECTED_CRITERIA_PT
    criteria_ignored = kwargs.get("criteria_ignored") or []
    assert any(p in criteria_ignored for p in PROTECTED_CRITERIA_PT), (
        f"F-03 A5: criteria_ignored deve incluir PROTECTED_CRITERIA_PT canonical, got {criteria_ignored}"
    )
