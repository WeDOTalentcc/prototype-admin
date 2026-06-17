"""
Testes unitários para MainOrchestrator.
Cobre: fluxo completo das 3 fases, PendingAction, ActionExecutor,
fallback para Orchestrator, tratamento de erros.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from app.orchestrator.context.context_adapter import UniversalContext
from app.orchestrator.execution.main_orchestrator import (
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


def _patch_conversation_memory():
    """Patch conversation_memory para evitar chamadas reais ao DB."""
    mock_mem = AsyncMock()
    mock_mem.get_conversation = AsyncMock(return_value=None)
    mock_mem.get_or_create_conversation = AsyncMock(return_value=MagicMock(id="conv-123", message_count=0))
    mock_mem.add_message = AsyncMock(return_value=None)
    mock_mem.get_context_for_llm = AsyncMock(return_value={"messages": [], "summary": None})
    return mock_mem


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
# Autouse fixture: LIA_PHASE_2_V1_ENABLED kill-switch
# Phase 2 V1 is disabled via env var in Replit (LIA_PHASE_2_V1_ENABLED=false).
# Unit tests exercise the Phase 2 path — patch the function to always return
# True so tests are not gated by production env var state.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _enable_phase_2_v1_for_tests():
    from unittest.mock import patch as _patch
    with _patch(
        "app.orchestrator.execution.main_orchestrator._is_phase_2_v1_enabled",
        return_value=True,
    ):
        yield


# ---------------------------------------------------------------------------
# Phase 2 — process_via_orchestrator (happy path)
# ---------------------------------------------------------------------------

class TestMainOrchestratorPhase2:
    @pytest.mark.asyncio
    async def test_calls_process_request(self):
        """Phase 2 chama orchestrator.process_request (não process_request_with_memory)."""
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(
            return_value=make_orchestrator_result()
        )
        mock_mem = _patch_conversation_memory()
        orch = MainOrchestrator(mock_orch)
        ctx = make_ctx()
        mock_db = MagicMock()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            result = await orch.process(ctx, mock_db)

            mock_orch.process_request.assert_called_once()
            call_kwargs = mock_orch.process_request.call_args.kwargs
            assert call_kwargs["user_id"] == "user-1"
            assert call_kwargs["message"] == "quem são os top 5 candidatos?"

    @pytest.mark.asyncio
    async def test_returns_chat_response(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(
            return_value=make_orchestrator_result(response="resultado final")
        )
        mock_mem = _patch_conversation_memory()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            assert isinstance(result, ChatResponse)
            assert result.content == "resultado final"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_error_returns_graceful_response(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(side_effect=Exception("DB timeout"))
        mock_mem = _patch_conversation_memory()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            assert result.success is False
            # graceful error uses "dificuldade", not "erro" — UX-friendly message
            assert result.content  # non-empty graceful message
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

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.is_confirmation", return_value=True),              patch("app.orchestrator.execution.main_orchestrator.ACTIONABLE_INTENTS", {"mover_candidato": {}}),              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:

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

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.is_confirmation", return_value=False),              patch("app.orchestrator.execution.main_orchestrator.is_rejection", return_value=True):

            mock_store.get.return_value = mock_pending
            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(message="não, cancela"), MagicMock())

            mock_store.remove.assert_called_once()
            assert result.intent_detected == "cancelamento"
            assert "cancelada" in result.content.lower()

    @pytest.mark.asyncio
    async def test_no_pending_action_skips_phase_0(self):
        """Sem pending action → vai direto para Phase 2 (process_request)."""
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
        mock_mem = _patch_conversation_memory()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            mock_orch.process_request.assert_called_once()
            assert result.success is True


# ---------------------------------------------------------------------------
# Phase 1 — ActionExecutor
# ---------------------------------------------------------------------------

class TestMainOrchestratorActionExecutor:
    @pytest.mark.asyncio
    async def test_not_actionable_falls_through_to_phase2(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
        mock_mem = _patch_conversation_memory()

        mock_exec_result = MagicMock()
        mock_exec_result.status = "not_actionable"

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=mock_exec_result)

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            mock_orch.process_request.assert_called_once()
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

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae:

            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=mock_exec_result)

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            # Phase 2 NÃO deve ser chamada
            mock_orch.process_request.assert_not_called()
            assert result.action_executed is True
            assert result.content == "Ação executada!"

    @pytest.mark.asyncio
    async def test_action_executor_exception_falls_through(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
        mock_mem = _patch_conversation_memory()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(side_effect=Exception("AE failed"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            # Deve fazer fallback para Phase 2
            mock_orch.process_request.assert_called_once()


# ---------------------------------------------------------------------------
# Multi-tenant isolation
# ---------------------------------------------------------------------------

class TestMainOrchestratorMultiTenant:
    @pytest.mark.asyncio
    async def test_company_id_passed_in_context(self):
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
        mock_mem = _patch_conversation_memory()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            ctx = make_ctx(company_id="empresa-xyz")
            await orch.process(ctx, MagicMock())

            mock_orch.process_request.assert_called_once()
            call_kwargs = mock_orch.process_request.call_args.kwargs
            # company_id deve estar no context passado para o orchestrator
            context = call_kwargs.get("context", {})
            assert context.get("company_id") == "empresa-xyz"


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


# ---------------------------------------------------------------------------
# FairnessGuard soft_warnings propagation
# ---------------------------------------------------------------------------

class TestFairnessSoftWarnings:
    def test_chat_response_has_fairness_warnings_field(self):
        """ChatResponse deve ter campo fairness_warnings vazio por padrão."""
        r = ChatResponse(success=True, content="ok")
        assert hasattr(r, "fairness_warnings")
        assert r.fairness_warnings == []

    @pytest.mark.asyncio
    async def test_soft_warnings_propagated_to_phase2_response(self):
        """Soft warnings do FairnessGuard devem aparecer no response final."""
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
        mock_mem = _patch_conversation_memory()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem),              patch("app.orchestrator.execution.main_orchestrator.FairnessGuard") as MockFG:

            mock_fg_instance = MagicMock()
            mock_fg_result = MagicMock()
            mock_fg_result.is_blocked = False
            mock_fg_result.soft_warnings = ["May indicate age bias."]
            mock_fg_instance.check.return_value = mock_fg_result
            mock_fg_instance.check_implicit_bias.return_value = ["Additional implicit bias warning."]
            MockFG.return_value = mock_fg_instance

            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            assert result.fairness_warnings != []
            assert any("age bias" in w for w in result.fairness_warnings)

    @pytest.mark.asyncio
    async def test_no_warnings_when_clean_query(self):
        """Query limpa não deve ter fairness_warnings."""
        mock_orch = AsyncMock()
        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
        mock_mem = _patch_conversation_memory()

        with patch("app.orchestrator.execution.main_orchestrator.pending_action_store") as mock_store,              patch("app.orchestrator.execution.main_orchestrator.action_executor") as mock_ae,              patch("app.domains.recruiter_assistant.services.conversation_memory.conversation_memory", mock_mem),              patch("app.orchestrator.execution.main_orchestrator.FairnessGuard") as MockFG:

            mock_fg_instance = MagicMock()
            mock_fg_result = MagicMock()
            mock_fg_result.is_blocked = False
            mock_fg_result.soft_warnings = []
            mock_fg_instance.check.return_value = mock_fg_result
            mock_fg_instance.check_implicit_bias.return_value = []
            MockFG.return_value = mock_fg_instance

            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))

            orch = MainOrchestrator(mock_orch)
            result = await orch.process(make_ctx(), MagicMock())

            assert result.fairness_warnings == []
