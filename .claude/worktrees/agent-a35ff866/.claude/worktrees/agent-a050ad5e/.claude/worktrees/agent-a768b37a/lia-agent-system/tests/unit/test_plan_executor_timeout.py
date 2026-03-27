"""
Testes unitários para PlanExecutor — Phase 3: timeout por step.
Cobre: timeout de 15s, fallback gracioso, tarefas críticas vs não-críticas com timeout.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.execution.plan_executor import PlanExecutor, TASK_TIMEOUT_SECONDS
from app.shared.execution.execution_plan import (
    ExecutionPlan, AgentTask, TaskStatus, PlanStatus,
)
from app.domains.base import DomainResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(task_id="t1", domain_id="sourcing", action_id="search", **kwargs) -> AgentTask:
    return AgentTask(task_id=task_id, domain_id=domain_id, action_id=action_id, **kwargs)


def make_plan(tasks=None) -> ExecutionPlan:
    plan = ExecutionPlan(tasks=tasks or [])
    return plan


def make_executor(domain_workflow=None, domain_registry=None) -> PlanExecutor:
    return PlanExecutor(
        domain_registry=domain_registry,
        domain_workflow=domain_workflow,
    )


def make_domain_response(success=True, message="ok", data=None) -> DomainResponse:
    if success:
        return DomainResponse.success_response(message=message, data=data or {})
    return DomainResponse.error_response(error="fail", message=message)


# ---------------------------------------------------------------------------
# TASK_TIMEOUT_SECONDS constant
# ---------------------------------------------------------------------------

class TestTimeoutConstant:
    def test_timeout_is_15(self):
        assert TASK_TIMEOUT_SECONDS == 15


# ---------------------------------------------------------------------------
# Timeout fires → task marked FAILED with timeout message
# ---------------------------------------------------------------------------

class TestPlanExecutorTimeout:
    @pytest.mark.asyncio
    async def test_task_timeout_marks_failed(self):
        """Quando a tarefa ultrapassa 15s, deve ser marcada como FAILED com erro de timeout."""
        async def slow_workflow(domain, dc, query):
            await asyncio.sleep(100)  # vai ser interrompido pelo timeout
            return make_domain_response()

        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = MagicMock()  # domain found
        mock_workflow = MagicMock()
        mock_workflow.process = slow_workflow

        task = make_task("slow-task")
        plan = make_plan([task])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)

        with patch("app.shared.execution.plan_executor.TASK_TIMEOUT_SECONDS", 0.05):
            await executor.execute(plan, user_id="u1", session_id="s1", tenant_id="t1")

        assert task.status == TaskStatus.FAILED
        assert "timed out" in (task.error or "").lower()

    @pytest.mark.asyncio
    async def test_timeout_on_critical_task_marks_remaining_blocked(self):
        """Timeout em tarefa crítica bloqueia tarefas dependentes."""
        async def slow_workflow(domain, dc, query):
            await asyncio.sleep(100)
            return make_domain_response()

        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.process = slow_workflow

        t1 = make_task("t1", is_critical=True)
        t2 = make_task("t2", depends_on=["t1"])
        plan = make_plan([t1, t2])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)

        with patch("app.shared.execution.plan_executor.TASK_TIMEOUT_SECONDS", 0.05):
            await executor.execute(plan, user_id="u1", session_id="s1", tenant_id="t1")

        assert t1.status == TaskStatus.FAILED
        # t2 depende de t1 que falhou → deve ser bloqueada
        assert t2.status in (TaskStatus.FAILED, TaskStatus.SKIPPED)

    @pytest.mark.asyncio
    async def test_fast_task_completes_normally(self):
        """Tarefa que completa dentro do timeout deve ter status COMPLETED."""
        fast_response = make_domain_response(message="done", data={"result": 42})

        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = MagicMock()
        mock_workflow = AsyncMock()
        mock_workflow.process = AsyncMock(return_value=fast_response)

        task = make_task("fast-task")
        plan = make_plan([task])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)

        await executor.execute(plan, user_id="u1", session_id="s1", tenant_id="t1")

        assert task.status == TaskStatus.COMPLETED
        assert plan.status == PlanStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_timeout_non_critical_task_allows_continuation(self):
        """Timeout em tarefa NÃO crítica não deve bloquear o plano inteiro."""
        fast_response = make_domain_response(message="ok")

        async def sometimes_slow(domain, dc, query):
            if dc.current_data.get("task_id") == "slow":
                await asyncio.sleep(100)
            return fast_response

        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.process = sometimes_slow

        slow = make_task("slow", is_critical=False)
        fast = make_task("fast", depends_on=[])
        plan = make_plan([slow, fast])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)

        with patch("app.shared.execution.plan_executor.TASK_TIMEOUT_SECONDS", 0.05):
            await executor.execute(plan, user_id="u1", session_id="s1", tenant_id="t1")

        assert slow.status == TaskStatus.FAILED
        assert "timed out" in (slow.error or "").lower()
        # fast não depende de slow, então deve ter sido executada
        assert fast.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_plan_without_registry_executes_without_timeout_path(self):
        """Quando não há domain_registry, o caminho sem timeout deve funcionar normalmente."""
        task = make_task("t1")
        plan = make_plan([task])
        executor = make_executor()  # sem registry e sem workflow

        await executor.execute(plan, user_id="u1", session_id="s1", tenant_id="t1")

        # Sem registry → caminho de fallback (success sem domínio real)
        assert task.status == TaskStatus.COMPLETED
        assert plan.status == PlanStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_domain_not_found_marks_task_failed(self):
        """Quando get_instance retorna None, a tarefa deve ser marcada como FAILED."""
        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = None  # domain not found
        mock_workflow = AsyncMock()

        task = make_task("t1")
        plan = make_plan([task])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)

        await executor.execute(plan, user_id="u1", session_id="s1", tenant_id="t1")

        assert task.status == TaskStatus.FAILED
        assert "not found" in (task.error or "").lower()

    @pytest.mark.asyncio
    async def test_workflow_exception_handled(self):
        """Exceção no workflow (sem retry disponível) deve marcar task como FAILED."""
        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = MagicMock()
        mock_workflow = AsyncMock()
        mock_workflow.process = AsyncMock(side_effect=ValueError("DB crash"))

        task = make_task("t1", max_retries=0)
        plan = make_plan([task])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)

        await executor.execute(plan, user_id="u1", session_id="s1", tenant_id="t1")

        assert task.status == TaskStatus.FAILED
        assert "DB crash" in (task.error or "")


# ---------------------------------------------------------------------------
# build_consolidated_response — smoke test
# ---------------------------------------------------------------------------

class TestBuildConsolidatedResponse:
    @pytest.mark.asyncio
    async def test_completed_plan_returns_success_response(self):
        fast_response = make_domain_response(message="feito", data={"id": 1})

        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = MagicMock()
        mock_workflow = AsyncMock()
        mock_workflow.process = AsyncMock(return_value=fast_response)

        task = make_task("t1")
        plan = make_plan([task])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)
        await executor.execute(plan, user_id="u", session_id="s", tenant_id="t")

        response = executor.build_consolidated_response(plan)
        assert response.success is True
        assert "t1" in response.data

    @pytest.mark.asyncio
    async def test_failed_plan_returns_error_response(self):
        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = MagicMock()
        mock_workflow = AsyncMock()
        mock_workflow.process = AsyncMock(side_effect=RuntimeError("fail"))

        task = make_task("t1", max_retries=0)
        plan = make_plan([task])
        executor = make_executor(domain_workflow=mock_workflow, domain_registry=mock_registry)
        await executor.execute(plan, user_id="u", session_id="s", tenant_id="t")

        response = executor.build_consolidated_response(plan)
        assert response.success is False
