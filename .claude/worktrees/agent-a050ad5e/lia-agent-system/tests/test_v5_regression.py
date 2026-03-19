import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.memory.reference_resolver import ReferenceResolver, ResolvedReference
from app.shared.memory.conversation_state import ConversationState
from app.shared.execution.plan_detector import PlanDetector
from app.shared.execution.plan_executor import PlanExecutor
from app.shared.execution.execution_plan import ExecutionPlan, AgentTask, TaskStatus, PlanStatus
from app.shared.async_processing.task_queue import DomainTaskQueue, AsyncTask, TaskPriority, TaskState
from app.shared.async_processing.task_manager import DomainTaskManager
from app.domains.base import DomainContext, DomainResponse


class TestReferenceResolverRegression:
    def setup_method(self):
        self.resolver = ReferenceResolver()
        self.state = ConversationState()

    def test_shortlist_show_empty(self):
        result = self.resolver.resolve("mostre meus favoritos", self.state)
        assert result.resolved is True
        assert result.reference_type == "shortlist"
        assert result.action == "show_shortlist"
        assert result.resolved_ids == []

    def test_shortlist_remove_no_detailed_candidate(self):
        result = self.resolver.resolve("remover dos favoritos", self.state)
        assert result.resolved is True
        assert result.reference_type == "shortlist"
        assert result.action == "remove_shortlist"
        assert result.resolved_id is None

    def test_continuation_empty_results(self):
        result = self.resolver.resolve("dentre eles quem tem java", self.state)
        assert result.resolved is True
        assert result.reference_type == "continuation"
        assert result.resolved_ids == []

    def test_pronoun_with_multiple_candidates(self):
        self.state.last_candidates_shown = [100, 200, 300]
        result = self.resolver.resolve("conte sobre dele", self.state)
        assert result.resolved is True
        assert result.reference_type == "pronoun"
        assert result.resolved_id == 100

    def test_name_fuzzy_below_threshold(self):
        self.state.mentioned_candidates = {"João Carlos da Silva Neto": 42}
        result = self.resolver.resolve("xyz abc", self.state)
        assert result.resolved is False

    def test_position_out_of_range(self):
        self.state.last_candidates_shown = [10, 20]
        result = self.resolver.resolve("mostre o quinto", self.state)
        assert result.resolved is False
        assert result.reference_type == "position"


class TestPlanDetectorFallback:
    def setup_method(self):
        self.detector = PlanDetector()

    def test_detect_no_match(self):
        result = self.detector.detect("olá, como posso ajudar?")
        assert result is None

    def test_detect_simple_query(self):
        result = self.detector.detect("buscar candidatos python")
        assert result is None

    def test_detect_partial_pattern(self):
        result = self.detector.detect("avaliar o candidato agora")
        assert result is None


class TestPlanExecutorConversationState:
    @pytest.mark.asyncio
    async def test_plan_executor_passes_conversation_state(self):
        mock_domain = MagicMock()
        mock_domain.domain_id = "sourcing"

        mock_registry = MagicMock()
        mock_registry.get_instance.return_value = mock_domain

        mock_workflow = MagicMock()
        mock_response = DomainResponse.success_response(message="ok", data={"result": "test"})
        mock_workflow.process = AsyncMock(return_value=mock_response)

        executor = PlanExecutor(domain_registry=mock_registry, domain_workflow=mock_workflow)

        plan = ExecutionPlan(plan_id="test_cs")
        plan.add_task(AgentTask(task_id="task_0", domain_id="sourcing", action_id="search"))

        conv_state = ConversationState()
        conv_state.last_search_term = "python developer"
        base_context = {"conversation_state": conv_state}

        await executor.execute(
            plan=plan,
            user_id="user1",
            session_id="sess1",
            tenant_id="tenant1",
            base_context=base_context,
        )

        mock_workflow.process.assert_called_once()
        call_args = mock_workflow.process.call_args
        domain_context = call_args[0][1]
        assert isinstance(domain_context, DomainContext)
        assert domain_context.conversation_state is conv_state

    @pytest.mark.asyncio
    async def test_plan_executor_without_conversation_state(self):
        executor = PlanExecutor()

        plan = ExecutionPlan(plan_id="test_no_cs")
        plan.add_task(AgentTask(task_id="task_0", domain_id="sourcing", action_id="search"))

        result = await executor.execute(
            plan=plan,
            user_id="user1",
            session_id="sess1",
            tenant_id="tenant1",
            base_context={"some_key": "some_value"},
        )

        assert result.status == PlanStatus.COMPLETED
        assert result.tasks[0].status == TaskStatus.COMPLETED


class TestDomainTaskQueueLifecycle:
    @pytest.mark.asyncio
    async def test_queue_stop_awaits_workers(self):
        queue = DomainTaskQueue(domain_id="test", max_concurrent=2)
        await queue.start()
        assert queue._running is True
        assert len(queue._workers) == 2

        await queue.stop()
        assert queue._running is False
        assert len(queue._workers) == 0
        for worker in queue._workers:
            assert worker.done()

    @pytest.mark.asyncio
    async def test_queue_drain(self):
        queue = DomainTaskQueue(domain_id="test_drain", max_concurrent=2)
        results = []

        async def handler(task):
            await asyncio.sleep(0.05)
            results.append(task.task_id)
            return {"done": True}

        queue.register_handler("action", handler)
        await queue.start()

        for i in range(3):
            task = AsyncTask(task_id=f"drain-{i}", domain_id="test_drain", action_id="action")
            await queue.enqueue(task)

        await queue.drain()
        assert len(results) == 3
        assert queue._running is False

    @pytest.mark.asyncio
    async def test_manager_shutdown(self):
        DomainTaskManager.reset_instance()
        manager = DomainTaskManager(max_concurrent_per_domain=1)

        async def handler(task):
            return {"ok": True}

        manager.register_handler("sourcing", "test_action", handler)
        await manager.submit_task(domain_id="sourcing", action_id="test_action")
        await asyncio.sleep(0.3)

        await manager.shutdown()
        assert manager._started is False
        assert DomainTaskManager._instance is None
        DomainTaskManager.reset_instance()
