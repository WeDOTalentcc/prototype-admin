"""
Extended unit tests for MainOrchestrator and ChatResponse.

Covers: ChatResponse.from_action_result, conversation_id generation,
streaming_callback passthrough, context fields passed to orchestrator,
needs_confirmation/needs_params flows, multiple phase interactions,
multi-turn message handling.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from app.orchestrator.context.context_adapter import UniversalContext
from app.orchestrator.execution.main_orchestrator import (
    MainOrchestrator,
    ChatResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ctx(**kwargs) -> UniversalContext:
    defaults = dict(
        message="listar candidatos",
        user_id="u-ext",
        company_id="comp-ext",
        conversation_id="conv-ext-1",
        context_page="talent",
        context_type="talent_funnel",
    )
    defaults.update(kwargs)
    return UniversalContext(**defaults)


def make_action_result(status="executed", message="Ok!", data=None, action_type="test_action",
                       pending_id=None):
    result = MagicMock()
    result.status = status
    result.message = message
    result.data = data or {}
    result.action_type = action_type
    result.pending_action_id = pending_id
    return result


def make_orchestrator_result(**kwargs) -> dict:
    defaults = dict(
        success=True,
        response="Resposta do orchestrator",
        agent_used="talent_react",
        intent_detected="listar_candidatos",
        confidence=0.9,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# ChatResponse.from_action_result
# ---------------------------------------------------------------------------

class TestChatResponseFromActionResult:
    def test_executed_status_sets_action_executed_true(self):
        ar = make_action_result(status="executed")
        resp = ChatResponse.from_action_result(ar, intent="mover", conv_id="c1")
        assert resp.action_executed is True

    def test_non_executed_status_sets_action_executed_false(self):
        ar = make_action_result(status="needs_confirmation")
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert resp.action_executed is False

    def test_needs_confirmation_sets_flag(self):
        ar = make_action_result(status="needs_confirmation")
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert resp.needs_confirmation is True

    def test_needs_params_sets_flag(self):
        ar = make_action_result(status="needs_params")
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert resp.needs_params is True

    def test_intent_detected_set(self):
        ar = make_action_result()
        resp = ChatResponse.from_action_result(ar, intent="buscar_candidato", conv_id="c1")
        assert resp.intent_detected == "buscar_candidato"

    def test_agent_used_is_action_executor(self):
        ar = make_action_result()
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert resp.agent_used == "ActionExecutor"

    def test_agents_consulted_contains_action_executor(self):
        ar = make_action_result()
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert "ActionExecutor" in resp.agents_consulted

    def test_suggested_prompts_passed_through(self):
        ar = make_action_result()
        suggestions = ["Próximo candidato?", "Ver todos os candidatos"]
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1", suggested_prompts=suggestions)
        assert resp.suggested_prompts == suggestions

    def test_pending_action_id_set_when_provided(self):
        ar = make_action_result(status="needs_confirmation", pending_id="p-abc")
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert resp.pending_action_id == "p-abc"

    def test_action_type_set(self):
        ar = make_action_result(action_type="enviar_email")
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert resp.action_type == "enviar_email"

    def test_content_from_message(self):
        ar = make_action_result(message="Candidato movido com sucesso para Entrevista!")
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert "Candidato movido" in resp.content

    def test_data_set_as_structured_data(self):
        ar = make_action_result(data={"candidate_id": "c-1", "new_stage": "entrevista"})
        resp = ChatResponse.from_action_result(ar, intent="x", conv_id="c1")
        assert resp.structured_data["candidate_id"] == "c-1"


# ---------------------------------------------------------------------------
# ChatResponse default values
# ---------------------------------------------------------------------------

class TestChatResponseDefaults:
    def test_default_success_true(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.success is True

    def test_default_agent_used(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.agent_used == "main_orchestrator"

    def test_default_intent_detected(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.intent_detected == "general"

    def test_default_confidence(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.confidence == 1.0

    def test_default_agents_consulted_empty(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.agents_consulted == []

    def test_default_suggested_prompts_empty(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.suggested_prompts == []

    def test_default_action_executed_false(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.action_executed is False

    def test_default_needs_confirmation_false(self):
        resp = ChatResponse(success=True, content="test")
        assert resp.needs_confirmation is False


# ---------------------------------------------------------------------------
# MainOrchestrator — conversation_id generation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestConversationIdGeneration:
    async def test_uses_context_conversation_id_when_provided(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(
            return_value=make_orchestrator_result()
        )
        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=make_action_result(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            ctx = make_ctx(conversation_id="specific-conv-id")
            result = await orch.process(ctx, MagicMock())

        assert result.conversation_id == "specific-conv-id"

    async def test_generates_uuid_when_no_conversation_id(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(
            return_value=make_orchestrator_result()
        )
        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=make_action_result(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            ctx = make_ctx(conversation_id=None)
            result = await orch.process(ctx, MagicMock())

        assert result.conversation_id is not None
        assert len(result.conversation_id) > 0


# ---------------------------------------------------------------------------
# MainOrchestrator — streaming callback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestStreamingCallback:
    async def test_streaming_callback_passed_to_orchestrator(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(
            return_value=make_orchestrator_result()
        )
        streaming_cb = AsyncMock()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=make_action_result(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            await orch.process(make_ctx(), MagicMock(), streaming_callback=streaming_cb)

        call_kwargs = mock_orch.process_request.call_args.kwargs
        ctx_passed = call_kwargs.get("context", {})
        assert "streaming_callback" in ctx_passed, "streaming_callback must be passed in orchestrator context"
        assert ctx_passed["streaming_callback"] is streaming_cb

    async def test_none_streaming_callback_does_not_raise(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(
            return_value=make_orchestrator_result()
        )
        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=make_action_result(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock(), streaming_callback=None)

        assert result.success is True


# ---------------------------------------------------------------------------
# Phase 1 — needs_confirmation short-circuit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestPhase1NeedsConfirmation:
    async def test_needs_confirmation_returns_chat_response(self):
        mock_orch = AsyncMock()
        mock_exec_result = make_action_result(
            status="needs_confirmation",
            message="Confirmar movimentação de candidato João para Entrevista?",
            pending_id="pa-123"
        )

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=mock_exec_result)

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(message="mover João para entrevista"), MagicMock())

        mock_orch.process_request.assert_not_called()
        assert result.needs_confirmation is True
        assert result.pending_action_id == "pa-123"

    async def test_needs_params_returns_chat_response(self):
        mock_orch = AsyncMock()
        mock_exec_result = make_action_result(
            status="needs_params",
            message="Para qual etapa deseja mover o candidato?",
        )

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store, \
             patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=mock_exec_result)

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(message="mover candidato"), MagicMock())

        mock_orch.process_request.assert_not_called()
        assert result.needs_params is True


# ---------------------------------------------------------------------------
# Phase 2 — from_orchestrator_result mappings
# ---------------------------------------------------------------------------

class TestFromOrchestratorResultMappings:
    def test_maps_domain_id_as_agent_used_fallback(self):
        result = {"success": True, "response": "ok", "domain_id": "sourcing_agent"}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.agent_used == "sourcing_agent"

    def test_maps_intent_from_intent_key(self):
        result = {"success": True, "response": "ok", "intent": "buscar_vagas"}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.intent_detected == "buscar_vagas"

    def test_maps_suggestions_key(self):
        result = {"success": True, "response": "ok", "suggestions": ["Sugestão 1"]}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert "Sugestão 1" in resp.suggested_prompts

    def test_maps_data_key_to_structured_data(self):
        result = {"success": True, "response": "ok", "data": {"count": 42}}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.structured_data["count"] == 42

    def test_ui_action_set(self):
        result = {"success": True, "response": "ok", "ui_action": "navigate_to_funnel"}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.ui_action == "navigate_to_funnel"

    def test_ui_action_params_set(self):
        result = {
            "success": True, "response": "ok",
            "ui_action": "filter", "ui_action_params": {"job_id": "j-1"}
        }
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.ui_action_params["job_id"] == "j-1"

    def test_success_false_mapped(self):
        result = {"success": False, "response": "Erro interno", "agent_used": "x"}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="c1")
        assert resp.success is False
