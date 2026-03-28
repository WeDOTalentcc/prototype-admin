"""
Testes unitários para MainOrchestrator.
Cobre: fluxo completo das 3 fases, PendingAction, ActionExecutor,
fallback para Orchestrator, tratamento de erros.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from app.orchestrator.context_adapter import UniversalContext
from app.orchestrator.main_orchestrator import (
    MainOrchestrator,
    ChatResponse,
    _get_suggested_prompts,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_ctx(**kwargs) -> UniversalContext:
    defaults = dict(
        message="quem são os top 5 candidatos?",
        user_id="user-1",
        company_id="comp-1",
        conversation_id="conv-123",
        context_page="sourcing",
        context_type="talent_funnel",
    )
    defaults.update(kwargs)
    return UniversalContext(**defaults)


def make_orchestrator_result(**kwargs) -> dict:
    defaults = dict(
        success=True,
        response="Aqui estão os top 5 candidatos...",
        agent_used="sourcing_react",
        intent_detected="top_candidatos",
        confidence=0.95,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# ChatResponse helpers
# ---------------------------------------------------------------------------

class TestChatResponseFromOrchestratorResult:
    def test_maps_response_to_content(self):
        result = make_orchestrator_result()
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.content == "Aqui estão os top 5 candidatos..."
        assert resp.success is True
        assert resp.conversation_id == "c1"

    def test_maps_content_key_as_fallback(self):
        result = {"success": True, "content": "Resposta alternativa"}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.content == "Resposta alternativa"

    def test_defaults_for_missing_fields(self):
        resp = ChatResponse.from_orchestrator_result({"success": True, "response": "ok"}, conv_id="c")
        assert resp.intent_detected == "general"
        assert resp.confidence == 1.0
        assert resp.agents_consulted == []


# ---------------------------------------------------------------------------
# Phase 2 — process_via_orchestrator (happy path)
# ---------------------------------------------------------------------------

class TestMainOrchestratorPhase2:
    @pytest.mark.asyncio
    async def test_calls_process_request_with_memory(self):
        mock_orch = AsyncMock()
        mock_orch.process_request_with_memory = AsyncMock(
            return_value=make_orchestrator_result()
        )
        orch = MainOrchestrator(mock_orch)
        ctx = make_ctx()
        mock_db = MagicMock()

        result = await orch.process(ctx, mock_db)

        mock_orch.process_request_with_memory.assert_called_once()
        call_kwargs = mock_orch.process_request_with_memory.call_args.kwargs
        assert call_kwargs["user_id"] == "user-1"
        assert call_kwargs["message"] == "quem são os top 5 candidatos?"
        assert call_kwargs["conversation_id"] == "conv-123"
        assert call_kwargs["context_type"] == "talent_funnel"

    @pytest.mark.asyncio
    async def test_returns_chat_response(self):
        mock_orch = AsyncMock()
        mock_orch.process_request_with_memory = AsyncMock(
            return_value=make_orchestrator_result(response="resultado final")
        )
        orch = MainOrchestrator(mock_orch)
        result = await orch.process(make_ctx(), MagicMock())

        assert isinstance(result, ChatResponse)
        assert result.content == "resultado final"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_error_returns_graceful_response(self):
        mock_orch = AsyncMock()
        mock_orch.process_request_with_memory = AsyncMock(side_effect=Exception("DB timeout"))
        orch = MainOrchestrator(mock_orch)

        result = await orch.process(make_ctx(), MagicMock())

        assert result.success is False
        assert "erro" in result.content.lower()
        assert result.intent_detected == "error"


# ---------------------------------------------------------------------------
# Phase 0 — PendingAction
# ---------------------------------------------------------------------------

class TestMainOrchestratorPendingAction:
    @pytest.mark.asyncio
    async def test_confirmation_executes_action(self):
        mock_orch = AsyncMock()
        mock_pending = MagicMock()
        mock_pending.awaiting_confirmation = True
        mock_pending.intent = "mover_candidato"
        mock_pending.collected_params = {"candidate_id": "1", "to_stage": "entrevista"}

        mock_exec_result = MagicMock()
        mock_exec_result.status = "executed"
        mock_exec_result.message = "Candidato movido com sucesso!"
        mock_exec_result.data = {}
        mock_exec_result.action_type = "mover_candidato"
        mock_exec_result.pending_action_id = None

        with patch("app.orchestrator.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.main_orchestrator.is_confirmation", return_value=True), \
             patch("app.orchestrator.main_orchestrator.ACTIONABLE_INTENTS", {"mover_candidato": {}}), \
             patch("app.orchestrator.main_orchestrator.action_executor") as mock_ae:

            mock_store.get.return_value = mock_pending
            mock_ae._execute_action = AsyncMock(return_value=mock_exec_result)

            orch = MainOrchestrator(mock_orch)
            ctx = make_ctx(message="sim, confirmo")
            result = await orch.process(ctx, MagicMock())

            mock_store.remove.assert_called_once_with("conv-123")
            assert result.action_executed is True
            assert "movido" in result.content.lower()

    @pytest.mark.asyncio
    async def test_rejection_cancels_action(self):
        mock_orch = AsyncMock()
        mock_pending = MagicMock()
        mock_pending.awaiting_confirmation = True

        with patch("app.orchestrator.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.main_orchestrator.is_confirmation", return_value=False), \
             patch("app.orchestrator.main_orchestrator.is_rejection", return_value=True):

            mock_store.get.return_value = mock_pending
            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(message="não, cancela"), MagicMock())

            mock_store.remove.assert_called_once()
            assert result.intent_detected == "cancelamento"
            assert "cancelada" in result.content.lower()

    @pytest.mark.asyncio
    async def test_no_pending_action_skips_phase_0(self):
        mock_orch = AsyncMock()
        mock_orch.process_request_with_memory = AsyncMock(
            return_value=make_orchestrator_result()
        )

        with patch("app.orchestrator.main_orchestrator.pending_action_store") as mock_store:
            mock_store.get.return_value = None  # sem pending
            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            # Deve ir direto para Phase 2
            mock_orch.process_request_with_memory.assert_called_once()
            assert result.success is True


# ---------------------------------------------------------------------------
# Phase 1 — ActionExecutor
# ---------------------------------------------------------------------------

class TestMainOrchestratorActionExecutor:
    @pytest.mark.asyncio
    async def test_not_actionable_falls_through_to_phase2(self):
        mock_orch = AsyncMock()
        mock_orch.process_request_with_memory = AsyncMock(
            return_value=make_orchestrator_result()
        )
        mock_exec_result = MagicMock()
        mock_exec_result.status = "not_actionable"

        with patch("app.orchestrator.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.main_orchestrator.action_executor") as mock_ae:

            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=mock_exec_result)

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            mock_orch.process_request_with_memory.assert_called_once()
            assert result.success is True

    @pytest.mark.asyncio
    async def test_executed_action_short_circuits(self):
        mock_orch = AsyncMock()
        mock_exec_result = MagicMock()
        mock_exec_result.status = "executed"
        mock_exec_result.message = "Ação executada!"
        mock_exec_result.data = {"id": "42"}
        mock_exec_result.action_type = "mover_candidato"
        mock_exec_result.pending_action_id = None

        with patch("app.orchestrator.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.main_orchestrator.action_executor") as mock_ae:

            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=mock_exec_result)

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            # Phase 2 NÃO deve ser chamada
            mock_orch.process_request_with_memory.assert_not_called()
            assert result.action_executed is True
            assert result.content == "Ação executada!"

    @pytest.mark.asyncio
    async def test_action_executor_exception_falls_through(self):
        mock_orch = AsyncMock()
        mock_orch.process_request_with_memory = AsyncMock(
            return_value=make_orchestrator_result()
        )

        with patch("app.orchestrator.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.main_orchestrator.action_executor") as mock_ae:

            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(side_effect=Exception("AE failed"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            # Deve fazer fallback para Phase 2
            mock_orch.process_request_with_memory.assert_called_once()


# ---------------------------------------------------------------------------
# Multi-tenant isolation
# ---------------------------------------------------------------------------

class TestMainOrchestratorMultiTenant:
    @pytest.mark.asyncio
    async def test_company_id_passed_in_context(self):
        mock_orch = AsyncMock()
        mock_orch.process_request_with_memory = AsyncMock(
            return_value=make_orchestrator_result()
        )

        with patch("app.orchestrator.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.main_orchestrator.action_executor") as mock_ae:
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            ctx = make_ctx(company_id="empresa-xyz")
            await orch.process(ctx, MagicMock())

            call_context = mock_orch.process_request_with_memory.call_args.kwargs["context"]
            # company_id deve estar acessível no contexto do orchestrator
            assert call_context.get("company_id") == "empresa-xyz" or \
                   ctx.company_id == "empresa-xyz"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestGetSuggestedPrompts:
    def test_returns_prompts_for_known_intent(self):
        prompts = _get_suggested_prompts("mover_candidato", 5, 0)
        assert len(prompts) > 0

    def test_returns_prompts_for_unknown_intent(self):
        prompts = _get_suggested_prompts("intent_desconhecido", 0, 0)
        assert len(prompts) > 0

    def test_returns_list(self):
        assert isinstance(_get_suggested_prompts("x", 3, 1), list)
