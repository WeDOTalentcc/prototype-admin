"""
F-17 P1 sentinels: WSI completion strategy canonical.

Audit: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-17.
finalize_screening tinha 2 paths WSI completion (wsi_voice_orchestrator PRIMARY
ou analyze_voice_screening FALLBACK), sem rastreamento claro de qual foi usado.

Consolidacao: single entry point _finalize_wsi_canonical com Enum WSICompletionStrategy
(PRIMARY/FALLBACK/SKIP) + telemetria de qual estrategia foi usada.

Sentinels:
- W1 PRIMARY usado quando call_sid presente E _WSIVoiceOrchestrator disponivel
- W2 FALLBACK usado quando PRIMARY falha
- W3 SKIP usado quando ambos falham (raise RuntimeError canonical)
- W4 strategy retornado no result dict (auditavel)
- W5 audit log inclui strategy escolhida
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


def _orchestrator():
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
    return VoiceScreeningOrchestrator()


def _make_session(call_sid="CA_FAKE", session_id="s-wsi-strategy"):
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningSession
    s = VoiceScreeningSession(
        session_id=session_id,
        candidate_id="c-1",
        candidate_name="Strategy Test",
        job_title="Job",
        company_id="comp-strat",
        phone_number="+5511",
        job_id="job-strat",
        status="analyzing",
        call_sid=call_sid,
    )
    s.transcript_segments = [{"role": "lia", "text": "hi"}]
    s.started_at = datetime(2026, 5, 22, 10, 0, 0)
    s.ended_at = datetime(2026, 5, 22, 10, 1, 0)
    return s


# ─── W1: PRIMARY used when call_sid + WSIVoiceOrchestrator ────────────────────

async def test_primary_used_when_call_sid_present():
    """W1: call_sid + _WSIVoiceOrchestrator avail -> PRIMARY usado, FALLBACK nao."""
    orch = _orchestrator()
    session = _make_session(call_sid="CA_W1")

    fake_wsi_orch_class = MagicMock()
    fake_wsi_instance = MagicMock()
    fake_wsi_instance.process_call_completed = AsyncMock(return_value={
        "overall_evaluation": {"overall_score": 9.0},
        "strategy_canonical": "primary_wsi_voice_orchestrator",  # marker
    })
    fake_wsi_orch_class.return_value = fake_wsi_instance

    fallback_fn = AsyncMock(return_value={"NEVER_USED": True})

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch.object(orch, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               fake_wsi_orch_class), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               fallback_fn):

        result = await orch.finalize_screening(session_id="s-wsi-strategy", db=None)

    assert result["status"] == "completed"
    assert fake_wsi_instance.process_call_completed.called, "PRIMARY (wsi_voice_orchestrator) deve ser usado"
    assert not fallback_fn.called, "FALLBACK NAO deve ser chamado quando PRIMARY funciona"
    # Strategy reportada
    assert result.get("wsi_strategy") == "primary" or "primary" in str(result.get("wsi_strategy", "")), (
        f"F-17 W1: result deve incluir wsi_strategy=primary, got {result.get('wsi_strategy')}"
    )


# ─── W2: FALLBACK used when PRIMARY fails ─────────────────────────────────────

async def test_fallback_used_when_primary_fails():
    """W2: PRIMARY exception -> FALLBACK invoked, retorna strategy=fallback."""
    orch = _orchestrator()
    session = _make_session(call_sid="CA_W2")

    fake_wsi_orch_class = MagicMock()
    fake_wsi_instance = MagicMock()
    fake_wsi_instance.process_call_completed = AsyncMock(
        side_effect=RuntimeError("simulated primary failure")
    )
    fake_wsi_orch_class.return_value = fake_wsi_instance

    fallback_fn = AsyncMock(return_value={
        "overall_evaluation": {"overall_score": 6.0},
    })

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch.object(orch, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               fake_wsi_orch_class), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               fallback_fn):

        result = await orch.finalize_screening(session_id="s-wsi-strategy", db=None)

    assert result["status"] == "completed", f"FALLBACK retorna sucesso. got {result}"
    assert fake_wsi_instance.process_call_completed.called, "PRIMARY foi tentado"
    assert fallback_fn.called, "FALLBACK invocado apos PRIMARY exception"
    assert result.get("wsi_strategy") == "fallback" or "fallback" in str(result.get("wsi_strategy", "")), (
        f"F-17 W2: result deve incluir wsi_strategy=fallback, got {result.get('wsi_strategy')}"
    )


# ─── W3: SKIP usado quando ambos falham ───────────────────────────────────────

async def test_skip_used_when_both_fail():
    """W3: ambos falham -> SKIP / analysis_failed com strategy=skip."""
    orch = _orchestrator()
    session = _make_session(call_sid="CA_W3")

    fake_wsi_orch_class = MagicMock()
    fake_wsi_instance = MagicMock()
    fake_wsi_instance.process_call_completed = AsyncMock(
        side_effect=RuntimeError("primary down")
    )
    fake_wsi_orch_class.return_value = fake_wsi_instance

    fallback_fn = AsyncMock(side_effect=RuntimeError("fallback down too"))

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch.object(orch, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               fake_wsi_orch_class), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               fallback_fn):

        result = await orch.finalize_screening(session_id="s-wsi-strategy", db=None)

    # Either analysis_failed or strategy=skip
    assert result.get("status") == "analysis_failed", (
        f"F-17 W3: ambos falham -> analysis_failed, got {result.get('status')}"
    )


# ─── W4: strategy retornado no result dict ───────────────────────────────────

async def test_strategy_returned_in_result_dict():
    """W4: result dict canonical inclui campo wsi_strategy para auditabilidade."""
    orch = _orchestrator()
    session = _make_session(call_sid="CA_W4")

    fake_wsi_orch_class = MagicMock()
    fake_wsi_instance = MagicMock()
    fake_wsi_instance.process_call_completed = AsyncMock(return_value={
        "overall_evaluation": {"overall_score": 8.0},
    })
    fake_wsi_orch_class.return_value = fake_wsi_instance

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch.object(orch, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               fake_wsi_orch_class), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               AsyncMock()):

        result = await orch.finalize_screening(session_id="s-wsi-strategy", db=None)

    assert "wsi_strategy" in result, f"F-17 W4: wsi_strategy ausente no result dict: {list(result.keys())}"


# ─── W5: audit log inclui strategy escolhida ─────────────────────────────────

async def test_audit_includes_wsi_strategy():
    """W5: log_finalize_screening_audit recebe strategy no reasoning."""
    orch = _orchestrator()
    session = _make_session(call_sid="CA_W5")

    fake_wsi_orch_class = MagicMock()
    fake_wsi_instance = MagicMock()
    fake_wsi_instance.process_call_completed = AsyncMock(
        side_effect=RuntimeError("force fallback")
    )
    fake_wsi_orch_class.return_value = fake_wsi_instance

    fallback_fn = AsyncMock(return_value={"overall_evaluation": {"overall_score": 7.0}})

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               fake_wsi_orch_class), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               fallback_fn), \
         patch("app.domains.voice.services.voice_screening_orchestrator.AuditService") as MockAudit:

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        MockAudit.return_value = mock_audit

        await orch.finalize_screening(session_id="s-wsi-strategy", db=None)

    assert mock_audit.log_decision.called, "log_decision invocado em finalize"
    kwargs = mock_audit.log_decision.call_args.kwargs
    reasoning = kwargs.get("reasoning", [])
    reasoning_str = " ".join(str(r) for r in reasoning).lower()
    assert "strategy" in reasoning_str or "fallback" in reasoning_str, (
        f"F-17 W5: reasoning deveria incluir strategy/fallback, got {reasoning}"
    )
