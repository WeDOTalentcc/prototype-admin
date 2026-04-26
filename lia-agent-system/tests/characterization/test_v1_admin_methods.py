"""
Characterization tests — métodos administrativos e de plano do V1.

Cobre:
- execute_plan(conversation_id, plan)
- process_analytics_request(user_id, command, context, conversation_id=None)
- get_metrics()
- get_cache_stats()
- invalidate_cache_for_entity(entity_type, entity_id)
- get_conversation_state(conversation_id)
- process_request_with_memory(db, user_id, message, ...)

Assinaturas verificadas em /app/orchestrator/orchestrator.py 2026-04-26.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# execute_plan — public method (4 fixtures)
# Assinatura real: (conversation_id: str, plan: dict[str, Any]) -> dict[str, Any]
# Internals: usa self._plan_executor.execute(plan=ExecutionPlan, user_id, session_id, tenant_id)
# ─────────────────────────────────────────────────────────────────────────────
class TestExecutePlan:
    """Captura comportamento de execução de plano multi-step."""

    @pytest.mark.asyncio
    async def test_returns_dict_with_required_keys(self, v1_with_minimal_mocks):
        """Contract: retorna dict com 'success', 'steps_executed', 'steps_total', 'results'."""
        # Mock plan_executor.execute para retornar ExecutionPlan-like
        mock_executed = MagicMock()
        mock_executed.tasks = []
        mock_executed.all_succeeded = True
        mock_executed.get_summary = MagicMock(return_value={"steps": 0})

        v1_with_minimal_mocks._plan_executor = MagicMock()
        v1_with_minimal_mocks._plan_executor.execute = AsyncMock(return_value=mock_executed)

        result = await v1_with_minimal_mocks.execute_plan(
            conversation_id="conv-1",
            plan={"plan": []},
        )
        assert isinstance(result, dict)
        assert "success" in result
        assert "steps_executed" in result
        assert "steps_total" in result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_empty_plan_returns_zero_steps(self, v1_with_minimal_mocks):
        """Plan vazio retorna steps_total=0."""
        mock_executed = MagicMock()
        mock_executed.tasks = []
        mock_executed.all_succeeded = True
        mock_executed.get_summary = MagicMock(return_value={})

        v1_with_minimal_mocks._plan_executor = MagicMock()
        v1_with_minimal_mocks._plan_executor.execute = AsyncMock(return_value=mock_executed)

        result = await v1_with_minimal_mocks.execute_plan(
            conversation_id="conv-1",
            plan={"plan": []},
        )
        assert result["steps_total"] == 0

    @pytest.mark.asyncio
    async def test_plan_with_single_step(self, v1_with_minimal_mocks):
        """Plan com 1 step constrói AgentTask corretamente."""
        from app.shared.execution import AgentTask
        from unittest.mock import PropertyMock

        # Mock task que parece executado
        mock_task = MagicMock()
        mock_task.task_id = "task_0"
        mock_task.domain_id = "recruiter_assistant"
        mock_task.status = MagicMock()
        mock_task.status.value = "completed"
        mock_task.result = None  # Não-DomainResponse → result_data = {}

        mock_executed = MagicMock()
        mock_executed.tasks = [mock_task]
        mock_executed.all_succeeded = True
        mock_executed.get_summary = MagicMock(return_value={"steps": 1})

        v1_with_minimal_mocks._plan_executor = MagicMock()
        v1_with_minimal_mocks._plan_executor.execute = AsyncMock(return_value=mock_executed)

        result = await v1_with_minimal_mocks.execute_plan(
            conversation_id="conv-1",
            plan={"plan": [{"agent_type": "recruiter_assistant", "description": "test"}]},
        )
        assert result["steps_total"] == 1
        assert result["steps_executed"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# process_analytics_request — public method (3 fixtures)
# Assinatura: (user_id, command, context, conversation_id=None)
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessAnalyticsRequest:
    """Captura comportamento de analytics proxy."""

    @pytest.mark.asyncio
    async def test_returns_dict_with_success_key(self, v1_with_minimal_mocks):
        """Contract: sempre retorna dict com success key.

        Pos-extracao: V1 delega ao AnalyticsDispatchService.
        """
        mock_svc = MagicMock()
        mock_svc.execute_command = AsyncMock(
            return_value=MagicMock(
                command="analyze", agent_used="analytics_agent", response="ok",
                data={}, charts=[], suggestions=[], metadata={},
            )
        )
        mock_svc.analyze_natural_query = AsyncMock(
            return_value=MagicMock(
                command="natural", agent_used="analytics_agent", response="ok",
                data={}, charts=[], suggestions=[], metadata={},
            )
        )
        v1_with_minimal_mocks._analytics_dispatch_service._service = mock_svc
        v1_with_minimal_mocks._analytics_dispatch_service._templates = {"test_cmd": {}}

        result = await v1_with_minimal_mocks.process_analytics_request(
            user_id="user-1", command="natural query",
            context={"company_id": "company-a"}, conversation_id="conv-1",
        )
        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self, v1_with_minimal_mocks):
        """Exception em analytics service retorna success=False.

        Pos-extracao (Sprint IV follow-up): V1 delega ao AnalyticsDispatchService.
        Patcha o service injetado no V1 para simular falha.
        """
        # Patcha o analytics service injetado no V1 (nao mais o module-level direto)
        v1_with_minimal_mocks._analytics_dispatch_service._service = MagicMock()
        v1_with_minimal_mocks._analytics_dispatch_service._service.analyze_natural_query = (
            AsyncMock(side_effect=Exception("svc fail"))
        )
        v1_with_minimal_mocks._analytics_dispatch_service._templates = {}  # nada matches

        result = await v1_with_minimal_mocks.process_analytics_request(
            user_id="user-1", command="bad query",
            context={"company_id": "company-a"},
        )
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_command_in_templates_uses_execute_command(self, v1_with_minimal_mocks):
        """Quando command esta em COMMAND_TEMPLATES, usa execute_command (nao natural).

        Pos-extracao: V1 delega ao service. Patcha service injetado.
        """
        mock_svc = MagicMock()
        mock_svc.execute_command = AsyncMock(
            return_value=MagicMock(
                command="known_cmd", agent_used="agent", response="r",
                data={}, charts=[], suggestions=[], metadata={},
            )
        )
        mock_svc.analyze_natural_query = AsyncMock()
        # Substitui service injetado no V1
        v1_with_minimal_mocks._analytics_dispatch_service._service = mock_svc
        v1_with_minimal_mocks._analytics_dispatch_service._templates = {"known_cmd": {}}

        await v1_with_minimal_mocks.process_analytics_request(
            user_id="user-1", command="known_cmd",
            context={"company_id": "company-a"},
        )
        mock_svc.execute_command.assert_called_once()
        mock_svc.analyze_natural_query.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# get_metrics — public method (2 fixtures)
# ─────────────────────────────────────────────────────────────────────────────
class TestGetMetrics:
    """Verifica retorno de métricas internas do orchestrator."""

    def test_returns_dict(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks.get_metrics()
        assert isinstance(result, dict)

    def test_dict_is_not_none(self, v1_with_minimal_mocks):
        """Captura: get_metrics nunca retorna None."""
        result = v1_with_minimal_mocks.get_metrics()
        assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# get_cache_stats — public method (2 fixtures)
# ─────────────────────────────────────────────────────────────────────────────
class TestGetCacheStats:
    """Verifica delegação para response_cache_service."""

    def test_returns_dict(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks.get_cache_stats()
        assert isinstance(result, dict)

    def test_calls_underlying_service(self, v1_with_minimal_mocks):
        """Contract: delega para self._response_cache.get_stats()."""
        v1_with_minimal_mocks._response_cache = MagicMock()
        v1_with_minimal_mocks._response_cache.get_stats.return_value = {"hits": 42}
        result = v1_with_minimal_mocks.get_cache_stats()
        assert result == {"hits": 42}


# ─────────────────────────────────────────────────────────────────────────────
# invalidate_cache_for_entity — public method (2 fixtures)
# Assinatura: (entity_type: str, entity_id: str) -> int
# ─────────────────────────────────────────────────────────────────────────────
class TestInvalidateCacheForEntity:
    """Verifica routing de invalidação por entity_type."""

    @pytest.mark.asyncio
    async def test_job_routes_to_invalidate_for_job(self, v1_with_minimal_mocks):
        v1_with_minimal_mocks._response_cache = MagicMock()
        v1_with_minimal_mocks._response_cache.invalidate_for_job = AsyncMock(return_value=3)
        result = await v1_with_minimal_mocks.invalidate_cache_for_entity("job", "job-123")
        v1_with_minimal_mocks._response_cache.invalidate_for_job.assert_called_once_with("job-123")
        assert result == 3

    @pytest.mark.asyncio
    async def test_unknown_entity_uses_pattern_invalidation(self, v1_with_minimal_mocks):
        v1_with_minimal_mocks._response_cache = MagicMock()
        v1_with_minimal_mocks._response_cache.invalidate_by_pattern = AsyncMock(return_value=1)
        result = await v1_with_minimal_mocks.invalidate_cache_for_entity("unknown_type", "abc-123")
        v1_with_minimal_mocks._response_cache.invalidate_by_pattern.assert_called_once()
        assert result == 1


# ─────────────────────────────────────────────────────────────────────────────
# get_conversation_state — public method (2 fixtures)
# ─────────────────────────────────────────────────────────────────────────────
class TestGetConversationState:
    """Verifica delegação para state_manager."""

    def test_returns_dict_or_none(self, v1_with_minimal_mocks):
        v1_with_minimal_mocks.state_manager = MagicMock()
        v1_with_minimal_mocks.state_manager.get_state.return_value = {"foo": "bar"}
        result = v1_with_minimal_mocks.get_conversation_state("conv-1")
        assert result == {"foo": "bar"}

    def test_missing_conversation_returns_none(self, v1_with_minimal_mocks):
        v1_with_minimal_mocks.state_manager = MagicMock()
        v1_with_minimal_mocks.state_manager.get_state.return_value = None
        result = v1_with_minimal_mocks.get_conversation_state("nonexistent")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# process_request_with_memory — public method (4 fixtures)
# Assinatura: (db, user_id, message, conversation_id=None, context_type="general",
#              context_id=None, context=None)
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestWithMemory:
    """Captura wrapper que adiciona conversation memory ao process_request."""

    @pytest.mark.asyncio
    async def test_returns_dict(self, v1_with_minimal_mocks, async_db):
        """Contract: retorna dict."""
        mock_conv = MagicMock(id="new-conv-1", message_count=1)

        v1_with_minimal_mocks.conversation_memory = MagicMock()
        v1_with_minimal_mocks.conversation_memory.get_or_create_conversation = AsyncMock(return_value=mock_conv)
        v1_with_minimal_mocks.conversation_memory.add_message = AsyncMock()
        v1_with_minimal_mocks.conversation_memory.get_context_for_llm = AsyncMock(
            return_value={"messages": [], "summary": None}
        )

        v1_with_minimal_mocks.process_request = AsyncMock(
            return_value={"success": True, "message": "ok", "intent": "test"}
        )

        result = await v1_with_minimal_mocks.process_request_with_memory(
            db=async_db, user_id="user-1", message="test message",
            conversation_id=None, context_type="general",
            context={"company_id": "company-a"},
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_with_existing_conversation(self, v1_with_minimal_mocks, async_db):
        """Quando conversation_id existe, busca em vez de criar."""
        mock_conv = MagicMock(id="existing-conv", message_count=5)

        v1_with_minimal_mocks.conversation_memory = MagicMock()
        v1_with_minimal_mocks.conversation_memory.get_conversation = AsyncMock(return_value=mock_conv)
        v1_with_minimal_mocks.conversation_memory.add_message = AsyncMock()
        v1_with_minimal_mocks.conversation_memory.get_context_for_llm = AsyncMock(
            return_value={"messages": [], "summary": "prev summary"}
        )
        v1_with_minimal_mocks.process_request = AsyncMock(
            return_value={"success": True, "message": "ok"}
        )

        result = await v1_with_minimal_mocks.process_request_with_memory(
            db=async_db, user_id="user-1", message="continuing",
            conversation_id="existing-conv",
            context={"company_id": "company-a"},
        )
        assert isinstance(result, dict)
        v1_with_minimal_mocks.conversation_memory.get_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_propagates_company_id(self, v1_with_minimal_mocks, async_db):
        """P0 LGPD: company_id deve ser preservado no enhanced context."""
        mock_conv = MagicMock(id="conv-1", message_count=1)

        v1_with_minimal_mocks.conversation_memory = MagicMock()
        v1_with_minimal_mocks.conversation_memory.get_or_create_conversation = AsyncMock(return_value=mock_conv)
        v1_with_minimal_mocks.conversation_memory.add_message = AsyncMock()
        v1_with_minimal_mocks.conversation_memory.get_context_for_llm = AsyncMock(
            return_value={"messages": []}
        )
        v1_with_minimal_mocks.process_request = AsyncMock(
            return_value={"success": True, "message": "ok"}
        )

        await v1_with_minimal_mocks.process_request_with_memory(
            db=async_db, user_id="user-1", message="test",
            context={"company_id": "company-tenant-x"},
        )
        call_kwargs = v1_with_minimal_mocks.process_request.call_args.kwargs
        ctx_passed = call_kwargs.get("context", {})
        assert ctx_passed.get("company_id") == "company-tenant-x"

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self, v1_with_minimal_mocks, async_db):
        """Exception no fluxo retorna shape de erro previsível com rollback."""
        v1_with_minimal_mocks.conversation_memory = MagicMock()
        v1_with_minimal_mocks.conversation_memory.get_or_create_conversation = AsyncMock(
            side_effect=Exception("DB error")
        )

        result = await v1_with_minimal_mocks.process_request_with_memory(
            db=async_db, user_id="user-1", message="test",
            context={"company_id": "company-a"},
        )
        assert isinstance(result, dict)
        assert result.get("success") is False
        assert "error" in result
        # Rollback deve ter sido chamado
        async_db.rollback.assert_called_once()
