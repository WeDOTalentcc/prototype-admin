"""
Voz Fase 0.5 sentinels — desacoplar finalize_screening do WSI.

Contexto: finalize_screening rodava o bloco WSI (_WSIVoiceOrchestrator /
_analyze_voice_screening) INCONDICIONALMENTE no core, mesmo quando nenhum
plugin WSI estava registrado. Uma sessao non-WSI (coleta de dados futura)
rodaria WSI no transcript errado OU lancaria RuntimeError ("both strategies
failed").

Fix: gate o bloco WSI na presenca de um plugin com plugin_name == "wsi_screening".
Sem plugin WSI -> roteia pelo fan-out canonico on_session_finalized
(_on_session_finalized) e finaliza limpo.

Sentinels:
- A (regressao, deve ficar VERDE): com WSIVoicePlugin registrado, finalize
  ainda roda o pipeline WSI exatamente como antes (path LIVE intocado).
- B (novo): SEM plugin WSI (plugins=[]), finalize NAO chama o WSI orchestrator
  e NAO lanca RuntimeError; roteia pelo fan-out on_session_finalized.
- C (novo): com plugin non-WSI registrado, seu on_session_finalized e' invocado.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


def _make_session(session_id="s-decouple", company_id="comp-x", call_sid="CA_FAKE"):
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningSession,
    )

    s = VoiceScreeningSession(
        session_id=session_id,
        candidate_id="cand-x",
        candidate_name="Decouple Test",
        job_title="Decouple Job",
        company_id=company_id,
        phone_number="+5511999999999",
        job_id="job-x",
        status="initiated",
        call_sid=call_sid,
        started_at=datetime.utcnow(),
    )
    s.transcript_segments = [
        {"role": "lia", "text": "Olá!"},
        {"role": "candidate", "text": "Oi, tudo bem."},
    ]
    return s


class _NonWSIPlugin:
    """Plugin de coleta de dados fictício (NÃO WSI)."""

    def __init__(self) -> None:
        self.finalized_calls: list[Any] = []

    @property
    def plugin_name(self) -> str:
        return "data_collection"

    async def on_session_initiated(self, session, db) -> None:  # noqa: D401
        return None

    async def get_next_question(self, session, db) -> str | None:
        return None

    async def on_session_finalized(self, session, db, transcript) -> dict[str, Any]:
        self.finalized_calls.append(transcript)
        return {"collected_fields": {"cnh": "sim"}, "domain": "data_collection"}


# ─── A: regressão — WSI plugin presente roda o pipeline WSI (path LIVE) ────────

async def test_finalize_runs_wsi_when_wsi_plugin_registered():
    """A: VoiceScreeningOrchestrator (WSIVoicePlugin pre-instalado) -> WSI roda."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
    )

    orch = VoiceScreeningOrchestrator()
    session = _make_session(session_id="s-wsi-present")

    fake_wsi = {"overall_evaluation": {"overall_score": 8.5}, "recommendation": "advance"}
    fake_wsi_orch = MagicMock()
    fake_wsi_orch.process_call_completed = AsyncMock(return_value=fake_wsi)
    MockWSIOrch = MagicMock(return_value=fake_wsi_orch)

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               MockWSIOrch), \
         patch("app.domains.voice.services.voice_screening_orchestrator.publish_platform_event",
               new=AsyncMock()):

        result = await orch.finalize_screening(session_id="s-wsi-present", db=None)

    # Pin LIVE behavior: WSI orchestrator chamado, status completed, strategy primary.
    assert fake_wsi_orch.process_call_completed.called, (
        "A: WSI plugin presente -> _WSIVoiceOrchestrator.process_call_completed DEVE ser chamado"
    )
    assert result["status"] == "completed", f"A: esperado completed, got {result['status']}"
    assert result["wsi_strategy"] == "primary", (
        f"A: esperado strategy primary, got {result.get('wsi_strategy')}"
    )
    assert result["wsi_result"] == fake_wsi


# ─── B: SEM plugin WSI -> não roda WSI, não lança, roteia fan-out ──────────────

async def test_finalize_skips_wsi_when_no_wsi_plugin():
    """B: VoiceCoreOrchestrator(plugins=[]) -> WSI NÃO roda, sem RuntimeError."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceCoreOrchestrator,
    )

    orch = VoiceCoreOrchestrator(plugins=[])
    session = _make_session(session_id="s-no-wsi")

    fake_wsi_orch = MagicMock()
    fake_wsi_orch.process_call_completed = AsyncMock(
        return_value={"overall_evaluation": {"overall_score": 1.0}}
    )
    MockWSIOrch = MagicMock(return_value=fake_wsi_orch)

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               MockWSIOrch), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               new=AsyncMock(return_value={"overall_evaluation": {"overall_score": 1.0}})), \
         patch("app.domains.voice.services.voice_screening_orchestrator.publish_platform_event",
               new=AsyncMock()):

        result = await orch.finalize_screening(session_id="s-no-wsi", db=None)

    assert not fake_wsi_orch.process_call_completed.called, (
        "B: sem plugin WSI -> _WSIVoiceOrchestrator NÃO deve ser chamado"
    )
    assert result["status"] != "analysis_failed", (
        f"B: sem plugin WSI NÃO deve falhar (RuntimeError), got status={result['status']}"
    )
    assert result["status"] == "completed", f"B: esperado completed, got {result['status']}"


# ─── C: plugin non-WSI -> seu on_session_finalized é invocado ──────────────────

async def test_finalize_routes_to_nonwsi_plugin_hook():
    """C: VoiceCoreOrchestrator(plugins=[NonWSI]) -> on_session_finalized chamado."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceCoreOrchestrator,
    )

    plugin = _NonWSIPlugin()
    orch = VoiceCoreOrchestrator(plugins=[plugin])
    session = _make_session(session_id="s-nonwsi")

    fake_wsi_orch = MagicMock()
    fake_wsi_orch.process_call_completed = AsyncMock()
    MockWSIOrch = MagicMock(return_value=fake_wsi_orch)

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_log_finalize_screening_audit", new=AsyncMock()), \
         patch.object(orch, "_record_voice_billing", new=AsyncMock()), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator",
               MockWSIOrch), \
         patch("app.domains.voice.services.voice_screening_orchestrator.publish_platform_event",
               new=AsyncMock()):

        result = await orch.finalize_screening(session_id="s-nonwsi", db=None)

    assert not fake_wsi_orch.process_call_completed.called, (
        "C: plugin non-WSI -> WSI orchestrator NÃO deve rodar"
    )
    assert len(plugin.finalized_calls) == 1, (
        "C: on_session_finalized do plugin non-WSI DEVE ser invocado exatamente 1x"
    )
    assert result["status"] == "completed", f"C: esperado completed, got {result['status']}"
