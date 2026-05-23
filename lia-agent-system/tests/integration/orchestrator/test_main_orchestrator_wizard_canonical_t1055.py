"""Sentinela canonical — Phase 1.4 Wizard Canonical Executor (Task #1055).

Garante que o ``MainOrchestrator._try_wizard_canonical`` delega ao
``WizardSessionService.process_message`` no caminho REST, simétrico ao
``agent_chat_ws.py:914`` (caminho WS canonical), e empacota o
``ws_stage_payload`` em ``ChatResponse.structured_data["ws_stage_payload"]``
para o FE consumir via ``message_metadata.ws_stage_payload``.

Sem este intercept, o turno do wizard era engolido pela Phase 1.5 Agentic
Loop e o ``WizardPipelineTemplateCard`` jamais renderizava em REST
(pw-cenario-A red).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.execution.main_orchestrator import MainOrchestrator
from app.orchestrator.context.context_adapter import UniversalContext


def _ctx(message: str, conversation_id: str = "conv-T1055") -> UniversalContext:
    ctx = UniversalContext(
        message=message,
        user_id="user-demo",
        company_id="00000000-0000-4000-a000-000000000001",
        conversation_id=conversation_id,
    )
    ctx.skip_memory_persist = True
    return ctx


@pytest.mark.asyncio
async def test_bootstrap_first_turn_match_start_pattern_delegates_to_wizard_session_service():
    """Turno 1 — 'Quero criar uma vaga…' aciona delegação canonical."""
    orch = MainOrchestrator(orchestrator=MagicMock())

    fake_payload = {"stage": "intake", "data": {"pipeline_template": "technical"}}
    with patch(
        "app.domains.job_creation.services.wizard_session_service.WizardSessionService"
    ) as WSS:
        WSS.is_session_active = AsyncMock(return_value=False)
        WSS.derive_thread_id = MagicMock(return_value="wiz-thread-1")
        WSS.process_message = AsyncMock(
            return_value=("Vamos lá, recebi a vaga.", fake_payload, 0)
        )

        resp = await orch._try_wizard_canonical(
            ctx=_ctx("Quero criar uma vaga de Engenheiro de Software Pleno"),
            conv_id="conv-T1055",
            conv=None,
            db=None,
        )

    assert resp is not None, "bootstrap (turno 1) deve disparar delegação"
    assert resp.agent_used == "wizard_session_canonical"
    WSS.process_message.assert_awaited_once()
    assert resp.structured_data is not None
    assert "ws_stage_payload" in resp.structured_data
    payload = resp.structured_data["ws_stage_payload"]
    assert payload["type"] == "wizard_stage"
    assert payload["thread_id"] == "wiz-thread-1"
    assert payload["stage"] == "intake"
    assert payload["data"]["pipeline_template"] == "technical"


@pytest.mark.asyncio
async def test_continuation_turn_session_active_pin_delegates():
    """Turno ≥2 — sessão wizard ativa (espelha CascadedRouter.wizard_session_pin Task #1051)."""
    orch = MainOrchestrator(orchestrator=MagicMock())

    with patch(
        "app.domains.job_creation.services.wizard_session_service.WizardSessionService"
    ) as WSS:
        WSS.is_session_active = AsyncMock(return_value=True)
        WSS.derive_thread_id = MagicMock(return_value="wiz-thread-2")
        WSS.process_message = AsyncMock(
            return_value=("Próxima etapa…", {"stage": "jd_enrichment"}, 0)
        )

        resp = await orch._try_wizard_canonical(
            # mensagem genérica que NÃO casa com start patterns — só passa pelo pin
            ctx=_ctx("Engenharia, 2 vagas, prazo 30 dias"),
            conv_id="conv-T1055",
            conv=None,
            db=None,
        )

    assert resp is not None
    WSS.is_session_active.assert_awaited_once()
    WSS.process_message.assert_awaited_once()
    assert resp.structured_data["ws_stage_payload"]["stage"] == "jd_enrichment"


@pytest.mark.asyncio
async def test_non_wizard_message_returns_none_falls_through_to_phase_15():
    """Mensagem não-wizard sem sessão ativa NÃO dispara — caller cai para Phase 1.5."""
    orch = MainOrchestrator(orchestrator=MagicMock())

    with patch(
        "app.domains.job_creation.services.wizard_session_service.WizardSessionService"
    ) as WSS:
        WSS.is_session_active = AsyncMock(return_value=False)
        WSS.process_message = AsyncMock()

        resp = await orch._try_wizard_canonical(
            ctx=_ctx("qual o status do candidato João?"),
            conv_id="conv-T1055",
            conv=None,
            db=None,
        )

    assert resp is None, "mensagem não-wizard deve retornar None"
    WSS.process_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_payload_still_returns_response_without_ws_stage_payload():
    """Wizard executou mas não emitiu payload (handoff stage) — content só."""
    orch = MainOrchestrator(orchestrator=MagicMock())

    with patch(
        "app.domains.job_creation.services.wizard_session_service.WizardSessionService"
    ) as WSS:
        WSS.is_session_active = AsyncMock(return_value=True)
        WSS.derive_thread_id = MagicMock(return_value="wiz-thread-3")
        WSS.process_message = AsyncMock(
            return_value=("Concluído.", {}, 0)
        )

        resp = await orch._try_wizard_canonical(
            ctx=_ctx("aceitar"),
            conv_id="conv-T1055",
            conv=None,
            db=None,
        )

    assert resp is not None
    assert resp.content == "Concluído."
    # Sem payload — structured_data deve ser None (não emitir ws_stage_payload vazio)
    assert resp.structured_data is None


@pytest.mark.asyncio
async def test_start_patterns_canonical_match_jobcreationdomain_source():
    """Cobertura dos start patterns canonical (espelha JobCreationDomain.process_intent)."""
    expected = {
        "criar vaga", "nova vaga", "abrir vaga", "contratar",
        "preciso de", "quero criar", "vamos criar",
    }
    actual = set(MainOrchestrator._WIZARD_START_PATTERNS)
    missing = expected - actual
    assert not missing, (
        f"start patterns divergem do JobCreationDomain.process_intent: "
        f"missing={missing}"
    )
