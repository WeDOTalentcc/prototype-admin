"""
Tests for Fase 3 — CrewAI-Style Delegation on AgentBus.

Covers:
- CrewModels (AgentCrew, CrewRole, CrewPlan, CrewTask)
- CrewContext (shared state)
- CrewPlanExecutor (DAG execution, timeouts, feature flag)
- AgentBus request-reply pattern
- Example crew (job opening + sourcing)
"""
import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.shared.agents.crew_models import (
    AgentCrew,
    CrewExecutionResult,
    CrewExecutionStatus,
    CrewPlan,
    CrewRole,
    CrewRoleType,
    CrewTask,
    CrewTaskStatus,
)
from app.shared.agents.crew_context import CrewContext
from app.shared.agents.crew_executor import CrewPlanExecutor, is_crew_delegation_enabled, is_crew_delegation_enabled_async
from app.shared.agents.agent_bus import AgentBus, AgentEvent
from app.shared.agents.crew_examples import (
    build_job_opening_sourcing_crew,
    get_production_handlers,
    handler_create_job_opening,
    handler_auto_source_candidates,
    handler_review_sourcing_results,
)


class TestCrewModels:
    def test_crew_role_creation(self):
        role = CrewRole(
            agent_name="wizard",
            role_type=CrewRoleType.LEADER,
            description="Creates jobs",
            capabilities=["create_job"],
        )
        assert role.agent_name == "wizard"
        assert role.role_type == CrewRoleType.LEADER

    def test_crew_task_defaults(self):
        task = CrewTask(
            assigned_agent="sourcing",
            action="search",
        )
        assert task.status == CrewTaskStatus.PENDING
        assert not task.is_done
        assert task.task_id
        assert task.timeout_seconds == 30.0
        assert task.is_critical is True

    def test_crew_task_is_done(self):
        task = CrewTask(assigned_agent="a", action="x")
        assert not task.is_done
        task.status = CrewTaskStatus.COMPLETED
        assert task.is_done
        task.status = CrewTaskStatus.FAILED
        assert task.is_done
        task.status = CrewTaskStatus.SKIPPED
        assert task.is_done

    def test_crew_plan_get_next_tasks_respects_dag(self):
        t1 = CrewTask(task_id="t1", assigned_agent="a", action="x")
        t2 = CrewTask(task_id="t2", assigned_agent="b", action="y", depends_on=["t1"])
        t3 = CrewTask(task_id="t3", assigned_agent="c", action="z")
        plan = CrewPlan(name="test", tasks=[t1, t2, t3])

        ready = plan.get_next_tasks()
        assert len(ready) == 2
        assert t1 in ready
        assert t3 in ready
        assert t2 not in ready

        t1.status = CrewTaskStatus.COMPLETED
        ready = plan.get_next_tasks()
        assert len(ready) == 2
        assert t2 in ready
        assert t3 in ready

    def test_crew_plan_summary(self):
        t1 = CrewTask(task_id="t1", assigned_agent="a", action="x", status=CrewTaskStatus.COMPLETED)
        t2 = CrewTask(task_id="t2", assigned_agent="b", action="y", status=CrewTaskStatus.FAILED)
        plan = CrewPlan(name="test", tasks=[t1, t2])
        summary = plan.get_summary()
        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert summary["total_tasks"] == 2

    def test_agent_crew_get_role(self):
        crew = AgentCrew(
            name="test",
            company_id="c1",
            roles=[
                CrewRole(agent_name="wizard", role_type=CrewRoleType.LEADER),
                CrewRole(agent_name="sourcing", role_type=CrewRoleType.RESEARCHER),
            ],
        )
        assert crew.get_role("wizard") is not None
        assert crew.get_role("wizard").role_type == CrewRoleType.LEADER
        assert crew.get_role("unknown") is None

    def test_agent_crew_get_agents_by_role(self):
        crew = AgentCrew(
            name="test",
            company_id="c1",
            roles=[
                CrewRole(agent_name="wizard", role_type=CrewRoleType.LEADER),
                CrewRole(agent_name="sourcing", role_type=CrewRoleType.RESEARCHER),
                CrewRole(agent_name="github_sourcing", role_type=CrewRoleType.RESEARCHER),
            ],
        )
        researchers = crew.get_agents_by_role(CrewRoleType.RESEARCHER)
        assert len(researchers) == 2
        assert "sourcing" in researchers

    def test_crew_plan_is_complete(self):
        t1 = CrewTask(task_id="t1", assigned_agent="a", action="x", status=CrewTaskStatus.COMPLETED)
        t2 = CrewTask(task_id="t2", assigned_agent="b", action="y", status=CrewTaskStatus.SKIPPED)
        plan = CrewPlan(name="test", tasks=[t1, t2])
        assert plan.is_complete

    def test_crew_plan_all_succeeded(self):
        t1 = CrewTask(task_id="t1", assigned_agent="a", action="x", status=CrewTaskStatus.COMPLETED)
        t2 = CrewTask(task_id="t2", assigned_agent="b", action="y", status=CrewTaskStatus.COMPLETED)
        plan = CrewPlan(name="test", tasks=[t1, t2])
        assert plan.all_succeeded


class TestCrewContext:
    @pytest.mark.asyncio
    async def test_local_cache_fallback(self):
        ctx = CrewContext(
            crew_execution_id="exec1",
            company_id="c1",
        )
        with patch.object(ctx, "_get_redis", side_effect=Exception("no redis")):
            await ctx.set("key1", "value1")
            result = await ctx.get("key1")
            assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_default(self):
        ctx = CrewContext(crew_execution_id="exec1", company_id="c1")
        with patch.object(ctx, "_get_redis", side_effect=Exception("no redis")):
            result = await ctx.get("missing", "default_val")
            assert result == "default_val"

    @pytest.mark.asyncio
    async def test_merge(self):
        ctx = CrewContext(crew_execution_id="exec1", company_id="c1")
        with patch.object(ctx, "_get_redis", side_effect=Exception("no redis")):
            await ctx.merge({"a": 1, "b": 2})
            assert await ctx.get("a") == 1
            assert await ctx.get("b") == 2

    @pytest.mark.asyncio
    async def test_get_all(self):
        ctx = CrewContext(crew_execution_id="exec1", company_id="c1")
        with patch.object(ctx, "_get_redis", side_effect=Exception("no redis")):
            await ctx.set("x", 10)
            await ctx.set("y", 20)
            all_data = await ctx.get_all()
            assert all_data == {"x": 10, "y": 20}

    @pytest.mark.asyncio
    async def test_delete(self):
        ctx = CrewContext(crew_execution_id="exec1", company_id="c1")
        with patch.object(ctx, "_get_redis", side_effect=Exception("no redis")):
            await ctx.set("k", "v")
            await ctx.delete()
            result = await ctx.get("k")
            assert result is None

    def test_redis_key_format(self):
        ctx = CrewContext(crew_execution_id="exec123", company_id="company_abc")
        assert ctx._redis_key == "lia:crew_ctx:company_abc:exec123"


class TestCrewPlanExecutor:
    @pytest.mark.asyncio
    async def test_simple_sequential_execution(self):
        async def handler_a(params, ctx):
            return {"result_a": "done"}

        async def handler_b(params, ctx):
            return {"result_b": "done"}

        executor = CrewPlanExecutor(task_handlers={
            "action_a": handler_a,
            "action_b": handler_b,
        })

        plan = CrewPlan(
            name="test",
            tasks=[
                CrewTask(task_id="t1", assigned_agent="a", action="action_a"),
                CrewTask(task_id="t2", assigned_agent="b", action="action_b", depends_on=["t1"]),
            ],
        )
        crew = AgentCrew(name="test", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.COMPLETED
        assert plan.tasks[0].status == CrewTaskStatus.COMPLETED
        assert plan.tasks[1].status == CrewTaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_parallel_task_execution(self):
        call_order = []

        async def handler_a(params, ctx):
            call_order.append("a")
            return {"a": True}

        async def handler_b(params, ctx):
            call_order.append("b")
            return {"b": True}

        async def handler_c(params, ctx):
            call_order.append("c")
            return {"c": True}

        executor = CrewPlanExecutor(task_handlers={
            "act_a": handler_a,
            "act_b": handler_b,
            "act_c": handler_c,
        })

        plan = CrewPlan(
            name="parallel",
            tasks=[
                CrewTask(task_id="t1", assigned_agent="a", action="act_a"),
                CrewTask(task_id="t2", assigned_agent="b", action="act_b"),
                CrewTask(task_id="t3", assigned_agent="c", action="act_c", depends_on=["t1", "t2"]),
            ],
        )
        crew = AgentCrew(name="parallel", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.COMPLETED
        assert "a" in call_order
        assert "b" in call_order
        assert "c" in call_order

    @pytest.mark.asyncio
    async def test_task_failure_blocks_dependents(self):
        async def handler_fail(params, ctx):
            raise RuntimeError("boom")

        async def handler_ok(params, ctx):
            return {"ok": True}

        executor = CrewPlanExecutor(task_handlers={
            "fail_action": handler_fail,
            "ok_action": handler_ok,
        })

        plan = CrewPlan(
            name="fail_test",
            tasks=[
                CrewTask(task_id="t1", assigned_agent="a", action="fail_action", max_retries=0),
                CrewTask(task_id="t2", assigned_agent="b", action="ok_action", depends_on=["t1"]),
            ],
        )
        crew = AgentCrew(name="fail_test", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.FAILED
        assert plan.tasks[0].status == CrewTaskStatus.FAILED
        assert plan.tasks[1].status == CrewTaskStatus.FAILED
        assert "Blocked" in (plan.tasks[1].error or "")

    @pytest.mark.asyncio
    async def test_task_timeout(self):
        async def slow_handler(params, ctx):
            await asyncio.sleep(10)
            return {}

        executor = CrewPlanExecutor(task_handlers={"slow": slow_handler})

        plan = CrewPlan(
            name="timeout_test",
            tasks=[
                CrewTask(
                    task_id="t1", assigned_agent="a", action="slow",
                    timeout_seconds=0.1, max_retries=0,
                ),
            ],
        )
        crew = AgentCrew(name="timeout_test", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert plan.tasks[0].status == CrewTaskStatus.TIMED_OUT
        assert "timed out" in (plan.tasks[0].error or "").lower()

    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self):
        executor = CrewPlanExecutor()
        plan = CrewPlan(name="test", tasks=[CrewTask(task_id="t1", assigned_agent="a", action="x")])
        crew = AgentCrew(name="test", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=False):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.FAILED
        assert "disabled" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_no_handler_registered(self):
        executor = CrewPlanExecutor(task_handlers={})

        plan = CrewPlan(
            name="test",
            tasks=[CrewTask(task_id="t1", assigned_agent="a", action="unknown_action")],
        )
        crew = AgentCrew(name="test", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert plan.tasks[0].status == CrewTaskStatus.FAILED
        assert "No handler" in (plan.tasks[0].error or "")

    @pytest.mark.asyncio
    async def test_empty_plan_fails(self):
        executor = CrewPlanExecutor()
        crew = AgentCrew(name="test", company_id="c1", plan=None)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_non_critical_failure_partial(self):
        async def handler_fail(params, ctx):
            raise RuntimeError("boom")

        async def handler_ok(params, ctx):
            return {"ok": True}

        executor = CrewPlanExecutor(task_handlers={
            "act_ok": handler_ok,
            "act_fail": handler_fail,
        })

        plan = CrewPlan(
            name="partial",
            tasks=[
                CrewTask(task_id="t1", assigned_agent="a", action="act_ok"),
                CrewTask(
                    task_id="t2", assigned_agent="b", action="act_fail",
                    is_critical=False, max_retries=0,
                ),
            ],
        )
        crew = AgentCrew(name="partial", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.PARTIAL


class TestAgentBusRequestReply:
    def test_agent_event_correlation_id(self):
        event = AgentEvent(
            from_agent="a",
            to_agent="b",
            event_type="test",
            payload={},
            company_id="c1",
            correlation_id="corr123",
            reply_to="reply_chan",
        )
        d = event.to_dict()
        assert d["correlation_id"] == "corr123"
        assert d["reply_to"] == "reply_chan"

        restored = AgentEvent.from_dict(d)
        assert restored.correlation_id == "corr123"
        assert restored.reply_to == "reply_chan"

    def test_agent_event_no_correlation(self):
        event = AgentEvent(
            from_agent="a",
            to_agent="b",
            event_type="test",
            payload={},
            company_id="c1",
        )
        d = event.to_dict()
        assert "correlation_id" not in d
        assert "reply_to" not in d

    def test_reply_channel_format(self):
        bus = AgentBus()
        chan = bus.reply_channel("abc123")
        assert chan == "lia:agent_bus:reply:abc123"

    @pytest.mark.asyncio
    async def test_reply_local_resolves_future(self):
        bus = AgentBus()
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        bus._pending_replies[("company_x", "corr_test")] = future

        resolved = await bus.reply_local("corr_test", {"answer": 42}, "agent_b", company_id="company_x")
        assert resolved is True
        assert future.result() == {"answer": 42}

    @pytest.mark.asyncio
    async def test_reply_local_no_future(self):
        bus = AgentBus()
        resolved = await bus.reply_local("nonexistent", {}, "agent_b")
        assert resolved is False

    @pytest.mark.asyncio
    async def test_reply_local_tenant_isolation(self):
        bus = AgentBus()
        loop = asyncio.get_running_loop()
        f1 = loop.create_future()
        f2 = loop.create_future()
        bus._pending_replies[("tenant_a", "same_corr")] = f1
        bus._pending_replies[("tenant_b", "same_corr")] = f2

        await bus.reply_local("same_corr", {"v": "a"}, "x", company_id="tenant_a")
        assert f1.result() == {"v": "a"}
        assert not f2.done()

    def test_reply_uses_event_reply_to(self):
        bus = AgentBus()
        event = AgentEvent(
            from_agent="a", to_agent="b", event_type="t",
            payload={}, company_id="c1",
            correlation_id="corr1",
            reply_to="lia:agent_bus:reply:c1:corr1",
        )
        assert event.reply_to == "lia:agent_bus:reply:c1:corr1"

    @pytest.mark.asyncio
    async def test_reply_without_reply_to_returns_false(self):
        bus = AgentBus()
        event = AgentEvent(
            from_agent="a", to_agent="b", event_type="t",
            payload={}, company_id="c1",
        )
        result = await bus.reply(event, {"x": 1}, "agent_b")
        assert result is False


class TestExampleCrew:
    def test_build_job_opening_sourcing_crew(self):
        crew = build_job_opening_sourcing_crew(
            company_id="c1",
            job_title="Senior Engineer",
        )
        assert crew.company_id == "c1"
        assert len(crew.roles) == 3
        assert crew.plan is not None
        assert len(crew.plan.tasks) == 3

        leaders = crew.get_agents_by_role(CrewRoleType.LEADER)
        assert "job_wizard" in leaders

        plan = crew.plan
        t_create = plan.get_task("create_job")
        t_source = plan.get_task("source_candidates")
        t_review = plan.get_task("review_sourcing")

        assert t_create is not None
        assert t_source.depends_on == ["create_job"]
        assert t_review.depends_on == ["source_candidates"]

    @pytest.mark.asyncio
    @patch("app.shared.agents.crew_examples._JOB_DOMAIN_AVAILABLE", False)
    async def test_handler_create_job_opening(self):
        ctx_mock = MagicMock()
        result = await handler_create_job_opening(
            {"job_title": "Test Job"}, ctx_mock
        )
        assert "job_id" in result
        assert result["job_title"] == "Test Job"
        assert result["source"] == "stub"

    @pytest.mark.asyncio
    @patch("app.shared.agents.crew_examples._SOURCING_DOMAIN_AVAILABLE", False)
    async def test_handler_auto_source_candidates(self):
        ctx_mock = MagicMock()
        result = await handler_auto_source_candidates(
            {"job_id": "j1"}, ctx_mock
        )
        assert result["job_id"] == "j1"
        assert isinstance(result["candidates"], list)
        assert result["source"] == "stub"

    @pytest.mark.asyncio
    async def test_handler_review_sourcing_results(self):
        ctx_mock = MagicMock()
        result = await handler_review_sourcing_results(
            {"candidates": [{"id": "c1"}]}, ctx_mock
        )
        assert result["reviewed"] == 1

    @pytest.mark.asyncio
    @patch("app.shared.agents.crew_examples._SOURCING_DOMAIN_AVAILABLE", False)
    @patch("app.shared.agents.crew_examples._JOB_DOMAIN_AVAILABLE", False)
    async def test_full_example_crew_execution(self):
        crew = build_job_opening_sourcing_crew(
            company_id="test_company",
            job_title="Frontend Developer",
        )

        executor = CrewPlanExecutor(task_handlers={
            "create_job_opening": handler_create_job_opening,
            "auto_source_candidates": handler_auto_source_candidates,
            "review_sourcing_results": handler_review_sourcing_results,
        })

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.COMPLETED
        assert result.crew_id == crew.crew_id
        assert result.company_id == "test_company"


class TestDAGValidation:
    def test_valid_dag(self):
        plan = CrewPlan(name="test", tasks=[
            CrewTask(task_id="t1", assigned_agent="a", action="x"),
            CrewTask(task_id="t2", assigned_agent="b", action="y", depends_on=["t1"]),
        ])
        assert plan.validate_dag() == []

    def test_missing_dependency(self):
        plan = CrewPlan(name="test", tasks=[
            CrewTask(task_id="t1", assigned_agent="a", action="x", depends_on=["nonexistent"]),
        ])
        errors = plan.validate_dag()
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_cyclic_dependency(self):
        plan = CrewPlan(name="test", tasks=[
            CrewTask(task_id="t1", assigned_agent="a", action="x", depends_on=["t2"]),
            CrewTask(task_id="t2", assigned_agent="b", action="y", depends_on=["t1"]),
        ])
        errors = plan.validate_dag()
        assert any("Cyclic" in e for e in errors)

    @pytest.mark.asyncio
    async def test_executor_rejects_invalid_dag(self):
        executor = CrewPlanExecutor()
        plan = CrewPlan(name="bad", tasks=[
            CrewTask(task_id="t1", assigned_agent="a", action="x", depends_on=["t2"]),
            CrewTask(task_id="t2", assigned_agent="b", action="y", depends_on=["t1"]),
        ])
        crew = AgentCrew(name="bad", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.FAILED
        assert "Cyclic" in (result.error or "")

    def test_has_failures_includes_timed_out(self):
        plan = CrewPlan(name="test", tasks=[
            CrewTask(task_id="t1", assigned_agent="a", action="x", status=CrewTaskStatus.TIMED_OUT),
        ])
        assert plan.has_failures is True


class TestTenantScopedReplyChannel:
    def test_reply_channel_with_company_id(self):
        bus = AgentBus()
        chan = bus.reply_channel("corr123", company_id="company_abc")
        assert chan == "lia:agent_bus:reply:company_abc:corr123"

    def test_reply_channel_without_company_id(self):
        bus = AgentBus()
        chan = bus.reply_channel("corr123")
        assert chan == "lia:agent_bus:reply:corr123"


class TestDelegationAuditLogging:
    @pytest.mark.asyncio
    async def test_log_delegation_called_for_each_task(self):
        async def handler_a(params, ctx):
            return {"a": True}

        mock_log_delegation = AsyncMock()

        executor = CrewPlanExecutor(task_handlers={"action_a": handler_a})
        plan = CrewPlan(
            name="test",
            tasks=[CrewTask(task_id="t1", assigned_agent="agent_a", action="action_a")],
        )
        crew = AgentCrew(name="test", company_id="c1", plan=plan)

        with patch("app.shared.agents.crew_executor.is_crew_delegation_enabled_async", new_callable=AsyncMock, return_value=True), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_started", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_task_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_crew_completed", new_callable=AsyncMock), \
             patch("app.shared.agents.crew_audit.crew_audit_service.log_delegation", mock_log_delegation), \
             patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            result = await executor.execute(crew)

        assert result.status == CrewExecutionStatus.COMPLETED
        mock_log_delegation.assert_called_once()
        call_kwargs = mock_log_delegation.call_args
        assert call_kwargs[1]["to_agent"] == "agent_a"
        assert call_kwargs[1]["from_agent"] == "crew_orchestrator"


class TestPlanExecutorCrewIntegration:
    @pytest.mark.asyncio
    async def test_execute_crew_via_plan_executor(self):
        from app.shared.execution.plan_executor import PlanExecutor

        crew = build_job_opening_sourcing_crew("c1", "Test Job")

        mock_crew_executor = AsyncMock()
        mock_crew_executor.execute.return_value = CrewExecutionResult(
            crew_id=crew.crew_id,
            company_id="c1",
            status=CrewExecutionStatus.COMPLETED,
        )

        mock_cls = MagicMock(return_value=mock_crew_executor)
        with patch("app.shared.agents.crew_executor.CrewPlanExecutor", mock_cls), \
             patch("app.shared.agents.crew_examples.get_production_handlers", return_value={}):
            plan_executor = PlanExecutor()
            result = await plan_executor.execute_crew(crew)

        assert result.status == CrewExecutionStatus.COMPLETED
        mock_crew_executor.execute.assert_called_once()
        mock_cls.assert_called_once_with(task_handlers={}, use_bus_delegation=True)


class TestFeatureFlag:
    def test_enabled_by_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CREW_DELEGATION_ENABLED", None)
            assert is_crew_delegation_enabled() is True

    def test_disabled_via_env(self):
        with patch.dict(os.environ, {"CREW_DELEGATION_ENABLED": "false"}):
            assert is_crew_delegation_enabled() is False

    def test_enabled_via_env(self):
        with patch.dict(os.environ, {"CREW_DELEGATION_ENABLED": "true"}):
            assert is_crew_delegation_enabled() is True

    def test_enabled_via_1(self):
        with patch.dict(os.environ, {"CREW_DELEGATION_ENABLED": "1"}):
            assert is_crew_delegation_enabled() is True

    @pytest.mark.asyncio
    async def test_async_flag_falls_back_to_sync_when_service_unavailable(self):
        with patch.dict("sys.modules", {"app.shared.governance.feature_flag_service": None}):
            with patch.dict(os.environ, {"CREW_DELEGATION_ENABLED": "false"}):
                result = await is_crew_delegation_enabled_async(db=None)
        assert result is False

    @pytest.mark.asyncio
    async def test_async_flag_uses_env_when_db_none(self):
        result = await is_crew_delegation_enabled_async(db=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_async_flag_respects_env_false_when_db_none(self):
        with patch.dict(os.environ, {"CREW_DELEGATION_ENABLED": "false"}):
            result = await is_crew_delegation_enabled_async(db=None)
        assert result is False


class TestProductionHandlers:
    def test_get_production_handlers_returns_all_actions(self):
        handlers = get_production_handlers()
        assert "create_job_opening" in handlers
        assert "auto_source_candidates" in handlers
        assert "review_sourcing_results" in handlers
        assert callable(handlers["create_job_opening"])

    @pytest.mark.asyncio
    @patch("app.shared.agents.crew_examples._JOB_DOMAIN_AVAILABLE", False)
    async def test_handler_create_job_opening_returns_source_field(self):
        from app.shared.agents.crew_context import CrewContext
        with patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            ctx = CrewContext(crew_execution_id="e", company_id="c")
            result = await handler_create_job_opening({"job_title": "SRE"}, ctx)
        assert "job_id" in result
        assert result["job_title"] == "SRE"
        assert result["source"] == "stub"

    @pytest.mark.asyncio
    async def test_handler_review_with_scored_candidates(self):
        from app.shared.agents.crew_context import CrewContext
        with patch("app.shared.agents.crew_context.CrewContext._get_redis", side_effect=Exception("no redis")):
            ctx = CrewContext(crew_execution_id="e", company_id="c")
            candidates = [
                {"name": "Alice", "match_score": 0.8},
                {"name": "Bob", "match_score": 0.3},
            ]
            result = await handler_review_sourcing_results(
                {"candidates": candidates, "job_id": "j1"}, ctx
            )
        assert result["reviewed"] == 2
        assert result["approved"] == 1
        assert result["rejected"] == 1


class TestCrewContextAtomicPipeline:
    @pytest.mark.asyncio
    async def test_set_uses_pipeline_for_hset_and_expire(self):
        from app.shared.agents.crew_context import CrewContext

        mock_pipe = AsyncMock()
        mock_pipe.hset = MagicMock(return_value=mock_pipe)
        mock_pipe.expire = MagicMock(return_value=mock_pipe)
        mock_pipe.execute = AsyncMock(return_value=[1, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)

        ctx = CrewContext(crew_execution_id="e1", company_id="c1")

        with patch.object(ctx, "_get_redis", return_value=mock_redis):
            await ctx.set("foo", "bar")

        mock_redis.pipeline.assert_called_once_with(transaction=True)
        mock_pipe.hset.assert_called_once()
        mock_pipe.expire.assert_called_once()
        mock_pipe.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_merge_uses_pipeline_for_hset_and_expire(self):
        from app.shared.agents.crew_context import CrewContext

        mock_pipe = AsyncMock()
        mock_pipe.hset = MagicMock(return_value=mock_pipe)
        mock_pipe.expire = MagicMock(return_value=mock_pipe)
        mock_pipe.execute = AsyncMock(return_value=[2, True])

        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)

        ctx = CrewContext(crew_execution_id="e2", company_id="c2")

        with patch.object(ctx, "_get_redis", return_value=mock_redis):
            await ctx.merge({"a": 1, "b": 2})

        mock_redis.pipeline.assert_called_once_with(transaction=True)
        mock_pipe.hset.assert_called_once()
        mock_pipe.expire.assert_called_once()
        mock_pipe.execute.assert_awaited_once()


class TestProductionHandlerExceptionPropagation:
    @pytest.mark.asyncio
    @patch("app.shared.agents.crew_examples._JOB_DOMAIN_AVAILABLE", True)
    async def test_job_handler_propagates_domain_exception(self):
        mock_wizard = AsyncMock()
        mock_wizard.invoke = AsyncMock(side_effect=RuntimeError("DB connection lost"))

        with patch("app.shared.agents.crew_examples.JobWizardGraph", mock_wizard), \
             patch("app.shared.agents.crew_examples._job_wizard_graph", mock_wizard):
            with pytest.raises(RuntimeError, match="DB connection lost"):
                await handler_create_job_opening(
                    {"job_title": "Failing Job"}, MagicMock()
                )

    @pytest.mark.asyncio
    @patch("app.shared.agents.crew_examples._SOURCING_DOMAIN_AVAILABLE", True)
    async def test_sourcing_handler_propagates_domain_exception(self):
        mock_agent = MagicMock()
        mock_agent.process = AsyncMock(side_effect=RuntimeError("Sourcing API down"))

        mock_agent_input_cls = MagicMock()

        with patch("app.shared.agents.crew_examples.SourcingReActAgent", return_value=mock_agent), \
             patch("app.shared.agents.crew_examples._AgentInput", mock_agent_input_cls):
            with pytest.raises(RuntimeError, match="Sourcing API down"):
                await handler_auto_source_candidates(
                    {"job_id": "j1", "company_id": "c1"}, MagicMock()
                )


class TestDAGSkippedDependencyResolution:
    def test_skipped_dependency_unblocks_downstream(self):
        plan = CrewPlan(name="test", tasks=[
            CrewTask(task_id="t1", assigned_agent="a", action="step1"),
            CrewTask(task_id="t2", assigned_agent="b", action="step2", depends_on=["t1"]),
        ])
        plan.tasks[0].status = CrewTaskStatus.SKIPPED

        next_tasks = plan.get_next_tasks()
        assert len(next_tasks) == 1
        assert next_tasks[0].task_id == "t2"

    def test_failed_dependency_does_not_unblock_downstream(self):
        plan = CrewPlan(name="test", tasks=[
            CrewTask(task_id="t1", assigned_agent="a", action="step1"),
            CrewTask(task_id="t2", assigned_agent="b", action="step2", depends_on=["t1"]),
        ])
        plan.tasks[0].status = CrewTaskStatus.FAILED

        next_tasks = plan.get_next_tasks()
        assert len(next_tasks) == 0
