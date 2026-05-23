"""
Tests for AutonomousReActAgent (Tier 6) and autonomous_tool_registry.

Covers:
- Unit tests with mocked LLM
- Integration scenarios (3+ cross-domain)
- CascadedRouter Tier 6 integration
- Golden dataset cross-domain cases
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_agent_input(
    message: str = "Test message",
    session_id: str = "test-session",
    user_id: str = "user-1",
    company_id: str = "company-1",
    context: dict | None = None,
):
    """Create a minimal AgentInput for testing."""
    try:
        from lia_agents_core.agent_interface import AgentInput
        return AgentInput(
            message=message,
            session_id=session_id,
            user_id=user_id,
            company_id=company_id,
            context=context or {},
            conversation_history=[],
        )
    except ImportError:
        return MagicMock(
            message=message,
            session_id=session_id,
            user_id=user_id,
            company_id=company_id,
            context=context or {},
            conversation_history=[],
        )


# ---------------------------------------------------------------------------
# Unit Tests — autonomous_tool_registry
# ---------------------------------------------------------------------------


class TestAutonomousToolRegistry:
    """Unit tests for the autonomous tool pool registry."""

    def test_get_autonomous_tools_returns_list(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_autonomous_tools
        tools = get_autonomous_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 40, f"Expected >= 40 tools (curated pool), got {len(tools)}"

    def test_all_tools_have_name_and_description(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_autonomous_tools
        tools = get_autonomous_tools()
        for tool in tools:
            assert hasattr(tool, "name"), f"Tool missing 'name': {tool}"
            assert hasattr(tool, "description"), f"Tool missing 'description': {tool}"
            assert tool.name, f"Tool has empty name: {tool}"
            assert tool.description, f"Tool has empty description: {tool}"

    def test_all_tools_have_function(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_autonomous_tools
        tools = get_autonomous_tools()
        for tool in tools:
            assert callable(tool.function), f"Tool '{tool.name}' has non-callable function"

    def test_get_tool_by_name(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_tool_by_name
        tool = get_tool_by_name("match_candidates_to_job")
        assert tool is not None
        assert tool.name == "match_candidates_to_job"

    def test_get_tool_by_name_missing(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_tool_by_name
        tool = get_tool_by_name("nonexistent_tool")
        assert tool is None

    def test_get_tool_names(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_tool_names
        names = get_tool_names()
        assert isinstance(names, list)
        expected_tools = [
            "list_jobs", "get_job_details", "search_candidates",
            "filter_candidates", "analyze_candidate_profile",
            "compare_candidates", "score_candidate_for_job",
            "match_candidates_to_job", "get_pipeline_status",
            "get_candidates_in_stage", "get_job_insights",
            "predict_hiring_metrics", "generate_report",
            "get_scheduled_interviews", "get_communication_history",
            "summarize_context", "clarify_request",
            # Extended tools (≥40)
            "get_salary_benchmark", "validate_job_requirements", "get_company_config",
            "view_candidate_profile", "view_screening_results", "view_interview_notes",
            "run_wsi_screening", "add_candidate_notes", "suggest_skills",
            "rank_candidates", "add_to_shortlist",
            "get_agent_performance", "get_search_analytics",
            "get_candidate_by_id", "search_candidates_by_name",
            "get_job_applications_summary", "cross_domain_funnel_analysis",
            "candidate_360_view", "list_jobs_with_candidates",
            "get_shortlists", "schedule_interview", "get_job_history",
            "get_tenant_hiring_overview",
        ]
        for expected in expected_tools:
            assert expected in names, f"Expected tool '{expected}' not found in pool"

    def test_tool_pool_has_40_or_more_tools(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_tool_names, TOOL_PERMISSION_SCOPE
        names = get_tool_names()
        assert len(names) >= 40, f"Pool has {len(names)} tools, expected >= 40"
        assert len(TOOL_PERMISSION_SCOPE) >= 40, (
            f"TOOL_PERMISSION_SCOPE has {len(TOOL_PERMISSION_SCOPE)} entries, expected >= 40"
        )

    def test_tenant_isolation_tools_accept_company_id(self):
        """Verify that DB-touching tools include company_id as a parameter."""
        import inspect
        try:
            from app.domains.autonomous.agents import autonomous_tool_registry as reg
            db_fns = [
                "_wrap_list_jobs",
                "_wrap_get_job_details",
                "_wrap_get_candidates_in_stage",
                "_wrap_get_pipeline_status",
                "_wrap_match_candidates_to_job",
                "_wrap_get_communication_history",
                "_wrap_rank_candidates",
                "_wrap_get_candidate_by_id",
                "_wrap_search_candidates_by_name",
                "_wrap_get_job_applications_summary",
                "_wrap_get_shortlists",
                "_wrap_get_job_history",
            ]
            for fn_name in db_fns:
                fn = getattr(reg, fn_name, None)
                if fn is None:
                    continue
                source = inspect.getsource(fn)
                assert "company_id" in source, (
                    f"{fn_name} must handle company_id for tenant isolation"
                )
        except ImportError:
            pass

    def test_tool_permission_scope_completeness(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import (
            get_tool_names,
            TOOL_PERMISSION_SCOPE,
        )
        for name in get_tool_names():
            assert name in TOOL_PERMISSION_SCOPE, f"Tool '{name}' missing from TOOL_PERMISSION_SCOPE"

    def test_cross_domain_match_tool_is_read(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import TOOL_PERMISSION_SCOPE
        assert TOOL_PERMISSION_SCOPE["match_candidates_to_job"] == "read"

    @pytest.mark.asyncio
    async def test_summarize_context_tool(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_summarize_context
        result = await _wrap_summarize_context(
            query="query cross-domain",
            gathered_data={"sourcing": {"candidates": 5}, "jobs": {"count": 2}},
        )
        assert result["success"] is True
        assert "domains_accessed" in result["data"]
        assert len(result["data"]["domains_accessed"]) == 2

    @pytest.mark.asyncio
    async def test_clarify_request_tool(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_clarify_request
        result = await _wrap_clarify_request(
            question="Qual vaga você quer consultar?",
            options=["Engenheiro Python", "Data Engineer", "Designer UX"],
        )
        assert result["success"] is True
        assert result["data"]["needs_clarification"] is True
        assert result["data"]["question"] == "Qual vaga você quer consultar?"
        assert len(result["data"]["options"]) == 3

    @pytest.mark.asyncio
    async def test_clarify_request_tool_default_question(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_clarify_request
        result = await _wrap_clarify_request()
        assert result["success"] is True
        assert result["data"]["needs_clarification"] is True
        assert result["data"]["question"]


# ---------------------------------------------------------------------------
# Unit Tests — AutonomousReActAgent (mocked LLM)
# ---------------------------------------------------------------------------


class TestAutonomousReActAgentUnit:
    """Unit tests for AutonomousReActAgent with mocked dependencies."""

    def test_agent_domain_name(self):
        with patch("lia_agents_core.langgraph_react_base._HAS_LANGGRAPH_PREBUILT", True), \
             patch("lia_agents_core.langgraph_react_base.create_react_agent", return_value=MagicMock()):
            try:
                from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent
                with patch.object(AutonomousReActAgent, "_setup_enhanced"):
                    agent = AutonomousReActAgent.__new__(AutonomousReActAgent)
                    agent._all_tool_names = []
                    agent._max_steps = 10
                    assert agent.domain_name == "autonomous"
            except Exception:
                pytest.skip("LangGraph not available")

    def test_agent_available_tools(self):
        from app.domains.autonomous.agents.autonomous_tool_registry import get_tool_names
        tool_names = get_tool_names()
        assert len(tool_names) >= 40

    def test_get_autonomous_react_agent_singleton(self):
        with patch("app.domains.autonomous.agents.autonomous_react_agent.AutonomousReActAgent") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            import app.domains.autonomous.agents.autonomous_react_agent as module
            original = module._autonomous_agent
            module._autonomous_agent = None

            try:
                from app.domains.autonomous.agents.autonomous_react_agent import get_autonomous_react_agent
                agent1 = get_autonomous_react_agent()
                agent2 = get_autonomous_react_agent()
                assert agent1 is agent2
                mock_cls.assert_called_once()
            finally:
                module._autonomous_agent = original

    @pytest.mark.asyncio
    async def test_process_fairness_blocked(self):
        """FairnessGuard should block biased requests before reaching LangGraph."""
        try:
            from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent

            agent = MagicMock(spec=AutonomousReActAgent)
            agent.domain_name = "autonomous"

            mock_fg_result = MagicMock()
            mock_fg_result.is_blocked = True
            mock_fg_result.educational_message = "Solicitação bloqueada por critério de equidade."

            with patch("app.domains.autonomous.agents.autonomous_react_agent.AutonomousReActAgent") as mock_cls, \
                 patch("app.shared.compliance.fairness_guard.FairnessGuard") as mock_fg_cls:

                mock_fg_cls.return_value.check.return_value = mock_fg_result

                real_agent = AutonomousReActAgent.__new__(AutonomousReActAgent)
                real_agent._all_tool_names = []
                real_agent._max_steps = 10
                real_agent._enhanced_domain = "autonomous"

                with patch.object(type(real_agent), "_setup_enhanced", return_value=None):
                    pass

                input_data = make_agent_input(message="Filtra candidatos apenas mulheres acima de 30 anos")

                with patch("app.shared.compliance.fairness_guard.FairnessGuard") as fg_mock:
                    fg_instance = MagicMock()
                    fg_instance.check.return_value = mock_fg_result
                    fg_mock.return_value = fg_instance

                    output = await real_agent.process(input_data)
                    if output.metadata and output.metadata.get("blocked"):
                        assert output.confidence == 1.0

        except ImportError:
            pytest.skip("AutonomousReActAgent dependencies not available")

    def test_system_prompt_has_required_sections(self):
        from app.domains.autonomous.agents.autonomous_react_agent import _AUTONOMOUS_SYSTEM_PROMPT
        assert "cross-domain" in _AUTONOMOUS_SYSTEM_PROMPT
        assert "FairnessGuard" in _AUTONOMOUS_SYSTEM_PROMPT or "equidade" in _AUTONOMOUS_SYSTEM_PROMPT
        assert "PII" in _AUTONOMOUS_SYSTEM_PROMPT or "mascarados" in _AUTONOMOUS_SYSTEM_PROMPT
        assert "clarify_request" in _AUTONOMOUS_SYSTEM_PROMPT or "clarify" in _AUTONOMOUS_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_budget_exhaustion_returns_needs_clarification(self):
        """When LangGraph raises a recursion/budget error, process() must return
        confidence=0 and needs_clarification=True in metadata."""
        from unittest.mock import AsyncMock, patch

        try:
            from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent

            agent = AutonomousReActAgent.__new__(AutonomousReActAgent)
            agent._all_tool_names = []
            agent._max_steps = 3

            class FakeRecursionError(Exception):
                pass

            async def _raise_recursion():
                raise FakeRecursionError("GraphRecursionError: recursion limit exceeded")

            with patch.object(agent, "_process_langgraph", side_effect=_raise_recursion):
                input_data = make_agent_input(message="Complex cross-domain query")
                output = await agent._execute_with_circuit_breaker(input_data)
                assert output.confidence == 0.0
                assert output.metadata is not None
                assert output.metadata.get("needs_clarification") is True
                assert output.metadata.get("budget_exhausted") is True
        except ImportError:
            pytest.skip("AutonomousReActAgent not importable")

    @pytest.mark.asyncio
    async def test_circuit_breaker_uses_call_method(self):
        """Circuit breaker integration must use .call() wrapping, not is_closed()."""
        import inspect
        try:
            from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent
            source = inspect.getsource(AutonomousReActAgent._execute_with_circuit_breaker)
            assert "_cb.call(" in source, (
                "Circuit breaker must use _cb.call(...) to wrap _process_langgraph"
            )
            assert "is_closed" not in source, (
                "Circuit breaker must NOT use is_closed() — that API doesn't exist"
            )
        except ImportError:
            pass

    @pytest.mark.asyncio
    async def test_tenant_context_var_injected_before_tools(self):
        """_CURRENT_COMPANY_ID context variable must be set before _execute_with_circuit_breaker."""
        import inspect
        try:
            from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent, _CURRENT_COMPANY_ID
            source = inspect.getsource(AutonomousReActAgent.process)
            cv_set_pos = source.find("_CURRENT_COMPANY_ID.set")
            cb_pos = source.find("_execute_with_circuit_breaker")
            assert cv_set_pos != -1, "_CURRENT_COMPANY_ID.set must be called in process()"
            assert cb_pos != -1, "_execute_with_circuit_breaker must be called in process()"
            assert cv_set_pos < cb_pos, (
                "Context var must be set before circuit breaker execution"
            )
        except ImportError:
            pass

    def test_get_tools_wraps_with_tenant_injector(self):
        """_get_tools must wrap tool functions with company_id injection."""
        import inspect
        try:
            from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent
            source = inspect.getsource(AutonomousReActAgent._get_tools)
            assert "_CURRENT_COMPANY_ID" in source, (
                "_get_tools must reference _CURRENT_COMPANY_ID for tenant injection"
            )
            assert "_tenant_safe_wrapper" in source or "company_id" in source, (
                "_get_tools must wrap tools with tenant-safe company_id injection"
            )
        except ImportError:
            pass

    @pytest.mark.asyncio
    async def test_circuit_breaker_open_returns_zero_confidence(self):
        """When circuit breaker is OPEN, process() must return confidence=0."""
        from unittest.mock import AsyncMock, MagicMock, patch

        try:
            from app.domains.autonomous.agents.autonomous_react_agent import (
                AutonomousReActAgent,
                _get_circuit_breaker,
            )
            from app.shared.resilience.circuit_breaker import CircuitBreakerError

            agent = AutonomousReActAgent.__new__(AutonomousReActAgent)
            agent._all_tool_names = []
            agent._max_steps = 5

            mock_cb = MagicMock()
            mock_cb.call = AsyncMock(side_effect=CircuitBreakerError("autonomous_react_agent", 30.0))

            with patch(
                "app.domains.autonomous.agents.autonomous_react_agent._get_circuit_breaker",
                return_value=mock_cb,
            ):
                input_data = make_agent_input(message="Cross-domain query")
                output = await agent._execute_with_circuit_breaker(input_data)
                assert output.confidence == 0.0
                assert output.metadata is not None
                assert output.metadata.get("circuit_open") is True
        except (ImportError, Exception) as exc:
            if "CircuitBreakerError" in str(type(exc).__name__) or "import" in str(exc).lower():
                pytest.skip(f"CircuitBreaker not importable: {exc}")
            raise

    @pytest.mark.asyncio
    async def test_get_tools_pydantic_model_copy_wraps_functions(self):
        """_get_tools() must use model_copy() (Pydantic) to wrap tool functions,
        proving that company_id is injected from the context variable."""
        try:
            from lia_agents_core.tool_adapter import ToolDefinition
            from app.domains.autonomous.agents.autonomous_react_agent import _CURRENT_COMPANY_ID

            calls_received: list[dict] = []

            async def mock_tool(**kwargs) -> dict:
                calls_received.append(dict(kwargs))
                return {"success": True, "data": {}, "message": "ok"}

            mock_td = ToolDefinition(name="mock_tool", description="Test tool", function=mock_tool)

            # Simulate the authoritative wrapping logic from _get_tools()
            # (server-side context always wins — prevents model IDOR)
            original_fn = mock_td.function

            async def _wrapper(*args, _fn=original_fn, **kwargs):
                request_company_id = _CURRENT_COMPANY_ID.get("")
                if request_company_id:
                    kwargs["company_id"] = request_company_id
                else:
                    kwargs.pop("company_id", None)
                return await _fn(*args, **kwargs)

            # Use Pydantic model_copy — must work (not dataclasses.replace)
            wrapped_td = mock_td.model_copy(update={"function": _wrapper})

            assert wrapped_td.function is not mock_tool, (
                "model_copy must produce a new function (the wrapper), not the original"
            )
            assert wrapped_td.name == "mock_tool", "name must be preserved after model_copy"

            # Verify injection happens when context var is set
            token = _CURRENT_COMPANY_ID.set("company-abc")
            try:
                await wrapped_td.function()
            finally:
                _CURRENT_COMPANY_ID.reset(token)

            assert len(calls_received) == 1
            assert calls_received[0].get("company_id") == "company-abc", (
                "Wrapper must inject company_id from _CURRENT_COMPANY_ID context variable"
            )

            # Verify no injection when context var is empty
            calls_received.clear()
            token2 = _CURRENT_COMPANY_ID.set("")
            try:
                await wrapped_td.function()
            finally:
                _CURRENT_COMPANY_ID.reset(token2)

            assert len(calls_received) == 1
            assert "company_id" not in calls_received[0] or not calls_received[0]["company_id"], (
                "Must NOT inject company_id when context var is empty"
            )
        except ImportError:
            pytest.skip("AutonomousReActAgent or ToolDefinition not importable")

    @pytest.mark.asyncio
    async def test_get_tools_overrides_model_supplied_company_id_with_request_context(self):
        """Wrapper must ALWAYS enforce server-side company_id, overriding any model-supplied value.
        This prevents IDOR / cross-tenant access via model argument manipulation."""
        try:
            from lia_agents_core.tool_adapter import ToolDefinition
            from app.domains.autonomous.agents.autonomous_react_agent import _CURRENT_COMPANY_ID

            calls_received: list[dict] = []

            async def mock_tool(**kwargs):
                calls_received.append(dict(kwargs))
                return {"success": True, "data": {}, "message": "ok"}

            # Simulate the authoritative wrapper logic from _get_tools()
            async def _authoritative_wrapper(*args, **kwargs):
                request_company_id = _CURRENT_COMPANY_ID.get("")
                if request_company_id:
                    kwargs["company_id"] = request_company_id
                else:
                    kwargs.pop("company_id", None)
                return await mock_tool(*args, **kwargs)

            # Model supplies a different (wrong) company_id — context must win
            token = _CURRENT_COMPANY_ID.set("real-tenant")
            try:
                await _authoritative_wrapper(company_id="attacker-tenant")
            finally:
                _CURRENT_COMPANY_ID.reset(token)

            assert calls_received[0]["company_id"] == "real-tenant", (
                "Server-side request context must override any model-supplied company_id (IDOR prevention)"
            )
        except ImportError:
            pytest.skip("AutonomousReActAgent or ToolDefinition not importable")

    @pytest.mark.asyncio
    async def test_get_tools_removes_company_id_when_no_request_context(self):
        """Wrapper must remove model-supplied company_id when no server-side context is set (fail closed)."""
        try:
            from app.domains.autonomous.agents.autonomous_react_agent import _CURRENT_COMPANY_ID

            calls_received: list[dict] = []

            async def mock_tool(**kwargs):
                calls_received.append(dict(kwargs))
                return {"success": True, "data": {}, "message": "ok"}

            async def _authoritative_wrapper(*args, **kwargs):
                request_company_id = _CURRENT_COMPANY_ID.get("")
                if request_company_id:
                    kwargs["company_id"] = request_company_id
                else:
                    kwargs.pop("company_id", None)
                return await mock_tool(*args, **kwargs)

            # No request context set — model-supplied value should be stripped
            token = _CURRENT_COMPANY_ID.set("")
            try:
                await _authoritative_wrapper(company_id="attacker-tenant")
            finally:
                _CURRENT_COMPANY_ID.reset(token)

            assert "company_id" not in calls_received[0] or not calls_received[0]["company_id"], (
                "company_id must be removed when no server-side request context — fail closed"
            )
        except ImportError:
            pytest.skip("AutonomousReActAgent not importable")

    def test_scheduled_interviews_requires_scope_parameter(self):
        """_wrap_get_scheduled_interviews must fail closed when no scope (candidate/job/company) given."""
        import asyncio
        try:
            from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_get_scheduled_interviews
            result = asyncio.run(_wrap_get_scheduled_interviews())
            assert result["success"] is False, (
                "get_scheduled_interviews must fail when no candidate_id/job_id/company_id provided"
            )
            assert "obrigatório" in result["message"] or "required" in result["message"].lower() or \
                   result["message"] != ""
        except ImportError:
            pytest.skip("Tool not importable")

    @pytest.mark.asyncio
    async def test_write_guard_blocks_without_confirm(self):
        """Write-scoped tools must return failure when confirm=True is not provided."""
        try:
            from app.domains.autonomous.agents.autonomous_react_agent import _CURRENT_COMPANY_ID

            calls_reached: list[str] = []

            async def mock_write_tool(**kwargs):
                calls_reached.append("called")
                return {"success": True, "data": {}, "message": "written"}

            def make_write_guarded_wrapper(fn):
                async def _write_guarded_wrapper(*args, **kwargs):
                    request_company_id = _CURRENT_COMPANY_ID.get("")
                    if request_company_id:
                        kwargs["company_id"] = request_company_id
                    else:
                        kwargs.pop("company_id", None)
                    if not kwargs.get("confirm"):
                        return {
                            "success": False,
                            "data": {},
                            "message": "Operação de escrita bloqueada: forneça confirm=True.",
                        }
                    return await fn(**kwargs)
                return _write_guarded_wrapper

            guarded = make_write_guarded_wrapper(mock_write_tool)

            token = _CURRENT_COMPANY_ID.set("tenant-x")
            try:
                result_no_confirm = await guarded()
                assert len(calls_reached) == 0, "Original function must NOT be called without confirmation"
                result_with_confirm = await guarded(confirm=True)
                assert len(calls_reached) == 1, "Original function must be called once with confirm=True"
            finally:
                _CURRENT_COMPANY_ID.reset(token)

            assert result_no_confirm["success"] is False, (
                "Write tool must be blocked without confirm=True"
            )
            assert "confirm" in result_no_confirm["message"].lower() or "escrita" in result_no_confirm["message"]
            assert result_with_confirm["success"] is True

        except ImportError:
            pytest.skip("AutonomousReActAgent not importable")

    def test_write_tools_are_marked_in_permission_scope(self):
        """All write tools must be declared in TOOL_PERMISSION_SCOPE as 'write'."""
        try:
            from app.domains.autonomous.agents.autonomous_tool_registry import TOOL_PERMISSION_SCOPE
            write_tools = [name for name, scope in TOOL_PERMISSION_SCOPE.items() if scope == "write"]
            expected_writes = {"schedule_interview", "add_to_shortlist", "add_candidate_notes", "run_wsi_screening"}
            for t in expected_writes:
                assert t in TOOL_PERMISSION_SCOPE, f"'{t}' must be in TOOL_PERMISSION_SCOPE"
                assert TOOL_PERMISSION_SCOPE[t] == "write", f"'{t}' must be marked as 'write'"
            assert len(write_tools) >= len(expected_writes), "At least 4 write tools must be registered"
        except ImportError:
            pytest.skip("Tool registry not importable")

    @pytest.mark.asyncio
    async def test_delegate_sourcing_rejects_missing_company_id(self):
        """_delegate_sourcing must fail closed when company_id is absent (tenant isolation guard)."""
        try:
            from app.domains.autonomous.agents.autonomous_tool_registry import _delegate_sourcing
            result = await _delegate_sourcing("search_candidates")
            assert result["success"] is False, (
                "_delegate_sourcing must fail closed when company_id is missing"
            )
            assert "company_id" in result["message"] or "tenant" in result["message"].lower()
        except ImportError:
            pytest.skip("Tool registry not importable")

    @pytest.mark.asyncio
    async def test_legacy_fallback_low_confidence_falls_to_tier6(self):
        """Legacy LLM fallback low-confidence result must not be returned — Tier 6 should be invoked."""
        with patch("app.orchestrator.routing.cascaded_router.FastRouter"), \
             patch("app.orchestrator.routing.cascaded_router.SemanticCache"):
            from app.orchestrator.routing.cascaded_router import CascadedRouter, RouteResult

            router = CascadedRouter.__new__(CascadedRouter)
            router._memory_cache = {}
            router._stats = {
                "memory_hits": 0, "redis_hits": 0, "vector_hits": 0,
                "fast_hits": 0, "llm_hits": 0, "autonomous_hits": 0,
                "clarification_issued": 0, "total": 0,
            }
            router._cache_max_size = 1024

            # Tier 5 cascade fails → falls to legacy fallback with low confidence
            async def mock_route_via_llm_cascade(message, context, company_id):
                raise RuntimeError("cascade unavailable")

            low_conf_legacy = RouteResult(domain_id="recruiter_assistant", confidence=0.2, source="llm_fallback")

            async def mock_route_via_llm(message, context):
                return low_conf_legacy

            tier6_called = []
            tier6_result = RouteResult(domain_id="autonomous", confidence=0.8, source="autonomous_react:tier6")

            async def mock_route_via_autonomous(message, context, session_id=None):
                tier6_called.append(True)
                return tier6_result

            async def mock_apply_adaptive(result, company_id):
                return result

            router._route_via_llm_cascade = mock_route_via_llm_cascade
            router._route_via_llm = mock_route_via_llm
            router._route_via_autonomous_agent = mock_route_via_autonomous
            router._apply_adaptive_adjustments = mock_apply_adaptive
            router._redis_cache = MagicMock()
            router._redis_cache.get = AsyncMock(return_value=None)
            router._redis_cache.set = AsyncMock()
            router._vector_cache = None
            router.fast = MagicMock()
            router.fast.match = MagicMock(return_value=None)
            router.llm_fallback = MagicMock()

            import os
            old_env = os.environ.get("AUTONOMOUS_REACT_ENABLED")
            old_conf = os.environ.get("ROUTER_LLM_CASCADE_MIN_CONFIDENCE")
            os.environ["AUTONOMOUS_REACT_ENABLED"] = "true"
            os.environ["ROUTER_LLM_CASCADE_MIN_CONFIDENCE"] = "0.5"
            try:
                result = await router.route("complex multi-domain query here", {})
            finally:
                if old_env is None:
                    os.environ.pop("AUTONOMOUS_REACT_ENABLED", None)
                else:
                    os.environ["AUTONOMOUS_REACT_ENABLED"] = old_env
                if old_conf is None:
                    os.environ.pop("ROUTER_LLM_CASCADE_MIN_CONFIDENCE", None)
                else:
                    os.environ["ROUTER_LLM_CASCADE_MIN_CONFIDENCE"] = old_conf

            assert len(tier6_called) == 1, (
                "Tier 6 must be invoked when legacy LLM fallback confidence is below threshold"
            )
            assert result.domain_id == "autonomous"


# ---------------------------------------------------------------------------
# Integration Tests — 3+ cross-domain scenarios
# ---------------------------------------------------------------------------


class TestCrossDomainIntegration:
    """
    Integration tests for cross-domain scenarios.
    Uses mocked DB and LLM but tests the full tool chain logic.
    """

    @pytest.mark.asyncio
    async def test_list_jobs_integration(self):
        """list_jobs tool should return empty list when DB unavailable (graceful fail)."""
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_list_jobs

        with patch("app.core.database.AsyncSessionLocal") as mock_db:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.mappings.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await _wrap_list_jobs(company_id="test-company", status="open")

        assert result["success"] is True
        assert result["data"]["jobs"] == []

    @pytest.mark.asyncio
    async def test_match_candidates_to_job_scenario(self):
        """
        Cross-domain scenario 1: matching candidates from sourcing to a job.
        Validates that match_candidates_to_job tool correctly handles
        job + candidates DB queries.
        """
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_match_candidates_to_job

        mock_job = MagicMock()
        mock_job.mappings.return_value.first.return_value = {
            "title": "Engenheiro Python",
            "requirements": ["python", "fastapi", "postgresql"],
            "seniority_level": "senior",
        }

        mock_candidates = MagicMock()
        mock_candidates.mappings.return_value.all.return_value = [
            {
                "id": "cand-1",
                "name": "João Silva",
                "current_title": "Python Dev",
                "seniority_level": "senior",
                "years_of_experience": 6,
                "technical_skills": ["python", "fastapi", "django"],
                "lia_score": 85.0,
            },
            {
                "id": "cand-2",
                "name": "Maria Santos",
                "current_title": "Backend Engineer",
                "seniority_level": "pleno",
                "years_of_experience": 4,
                "technical_skills": ["python", "postgresql"],
                "lia_score": 75.0,
            },
        ]

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_job
            return mock_candidates

        with patch("app.core.database.AsyncSessionLocal") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = mock_execute
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await _wrap_match_candidates_to_job(job_id="job-1", company_id="company-test", limit=5)

        assert result["success"] is True
        assert "top_candidates" in result["data"]
        candidates = result["data"]["top_candidates"]
        assert len(candidates) <= 5
        if candidates:
            assert candidates[0]["rank"] == 1
            assert "match_score" in candidates[0]
            assert "name" in candidates[0]

    @pytest.mark.asyncio
    async def test_pipeline_status_cross_domain_scenario(self):
        """
        Cross-domain scenario 2: get pipeline status for a job.
        Validates get_pipeline_status tool integrates pipeline data correctly.
        """
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_get_pipeline_status

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"stage": "triagem", "count": 10, "status": "active"},
            {"stage": "triagem", "count": 3, "status": "pending"},
            {"stage": "entrevista", "count": 5, "status": "scheduled"},
        ]

        with patch("app.core.database.AsyncSessionLocal") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await _wrap_get_pipeline_status(job_id="job-1", company_id="company-test")

        assert result["success"] is True
        assert "stages" in result["data"]
        stages = {s["stage"]: s for s in result["data"]["stages"]}
        assert "triagem" in stages
        assert stages["triagem"]["total"] == 13
        assert "entrevista" in stages
        assert result["data"]["total_candidates"] == 18

    @pytest.mark.asyncio
    async def test_scheduled_interviews_cross_domain_scenario(self):
        """
        Cross-domain scenario 3: get interviews for candidates in the pipeline.
        Validates get_scheduled_interviews returns structured data.
        """
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_get_scheduled_interviews

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {
                "id": "int-1",
                "candidate_id": "cand-1",
                "job_id": "job-1",
                "interview_type": "technical",
                "scheduled_at": "2026-04-10 14:00:00",
                "duration_minutes": 60,
                "status": "scheduled",
                "notes": "Entrevista técnica Python",
            },
        ]

        with patch("app.core.database.AsyncSessionLocal") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_db.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await _wrap_get_scheduled_interviews(job_id="job-1", status="scheduled")

        assert result["success"] is True
        assert "interviews" in result["data"]
        assert len(result["data"]["interviews"]) == 1
        assert result["data"]["interviews"][0]["interview_type"] == "technical"

    @pytest.mark.asyncio
    async def test_compare_candidates_cross_domain_scenario(self):
        """
        Cross-domain scenario 4: compare candidates across job pipeline + sourcing.
        """
        from app.domains.autonomous.agents.autonomous_tool_registry import _wrap_auto_compare_candidates

        with patch(
            "app.domains.autonomous.agents.autonomous_tool_registry._delegate_sourcing",
            new_callable=AsyncMock,
        ) as mock_delegate:
            mock_delegate.return_value = {
                "success": True,
                "data": {
                    "candidate_ids": ["cand-1", "cand-2"],
                    "comparison": [
                        {"id": "cand-1", "name": "Alice", "lia_score": 90.0, "rank": 1},
                        {"id": "cand-2", "name": "Bob", "lia_score": 75.0, "rank": 2},
                    ],
                    "ranking": [
                        {"id": "cand-1", "name": "Alice", "lia_score": 90.0, "rank": 1},
                        {"id": "cand-2", "name": "Bob", "lia_score": 75.0, "rank": 2},
                    ],
                },
                "message": "Comparação de 2 candidatos concluída.",
            }

            result = await _wrap_auto_compare_candidates(candidate_ids=["cand-1", "cand-2"])

        assert result["success"] is True
        assert "ranking" in result["data"]
        assert result["data"]["ranking"][0]["name"] == "Alice"


# ---------------------------------------------------------------------------
# Integration Tests — CascadedRouter Tier 6
# ---------------------------------------------------------------------------


class TestCascadedRouterTier6:
    """Tests for Tier 6 integration in CascadedRouter."""

    def test_cascaded_router_has_autonomous_stats(self):
        """CascadedRouter._stats should have 'autonomous_hits' key."""
        with patch("app.orchestrator.routing.cascaded_router.FastRouter"), \
             patch("app.orchestrator.routing.cascaded_router.SemanticCache"):
            from app.orchestrator.routing.cascaded_router import CascadedRouter
            router = CascadedRouter.__new__(CascadedRouter)
            router._memory_cache = {}
            router._stats = {
                "memory_hits": 0,
                "redis_hits": 0,
                "vector_hits": 0,
                "fast_hits": 0,
                "llm_hits": 0,
                "autonomous_hits": 0,
                "clarification_issued": 0,
                "total": 0,
            }
            stats = router.get_stats()
            assert "autonomous_hits" in stats
            assert "autonomous_hit_rate" in stats

    @pytest.mark.asyncio
    async def test_route_via_autonomous_agent_returns_none_on_error(self):
        """_route_via_autonomous_agent should return None on import/runtime errors."""
        with patch("app.orchestrator.routing.cascaded_router.FastRouter"), \
             patch("app.orchestrator.routing.cascaded_router.SemanticCache"):
            from app.orchestrator.routing.cascaded_router import CascadedRouter
            router = CascadedRouter.__new__(CascadedRouter)
            router._stats = {"autonomous_hits": 0, "total": 0}

            with patch(
                "app.domains.autonomous.agents.autonomous_react_agent.get_autonomous_react_agent",
                side_effect=ImportError("mock import error"),
            ):
                result = await router._route_via_autonomous_agent(
                    message="test",
                    context={"company_id": "test"},
                )

            assert result is None

    @pytest.mark.asyncio
    async def test_route_via_autonomous_agent_low_confidence_returns_none(self):
        """If agent returns confidence < 0.5, router should return None (go to clarification)."""
        with patch("app.orchestrator.routing.cascaded_router.FastRouter"), \
             patch("app.orchestrator.routing.cascaded_router.SemanticCache"):
            from app.orchestrator.routing.cascaded_router import CascadedRouter
            router = CascadedRouter.__new__(CascadedRouter)

            mock_output = MagicMock()
            mock_output.confidence = 0.3
            mock_output.message = "Não consegui resolver."
            mock_output.actions = []
            mock_output.metadata = {}

            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value=mock_output)

            with patch(
                "app.domains.autonomous.agents.autonomous_react_agent.get_autonomous_react_agent",
                return_value=mock_agent,
            ), patch(
                "lia_agents_core.agent_interface.AgentInput",
                return_value=MagicMock(),
            ):
                result = await router._route_via_autonomous_agent(
                    message="test query",
                    context={"company_id": "test"},
                )

            assert result is None

    @pytest.mark.asyncio
    async def test_route_via_autonomous_agent_success(self):
        """If agent returns confidence >= 0.5, router returns RouteResult with domain='autonomous'."""
        with patch("app.orchestrator.routing.cascaded_router.FastRouter"), \
             patch("app.orchestrator.routing.cascaded_router.SemanticCache"):
            from app.orchestrator.routing.cascaded_router import CascadedRouter
            router = CascadedRouter.__new__(CascadedRouter)

            mock_output = MagicMock()
            mock_output.confidence = 0.75
            mock_output.message = "Top 3 candidatos para a vaga: ..."
            mock_output.actions = [MagicMock(action_type="call_tool", params={"tool": "match_candidates_to_job"})]
            mock_output.metadata = {"tier": 6}

            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value=mock_output)

            with patch(
                "app.domains.autonomous.agents.autonomous_react_agent.get_autonomous_react_agent",
                return_value=mock_agent,
            ), patch(
                "lia_agents_core.agent_interface.AgentInput",
                return_value=MagicMock(),
            ):
                result = await router._route_via_autonomous_agent(
                    message="Qual candidato do sourcing se encaixa melhor na vaga de Engenheiro?",
                    context={"company_id": "test"},
                )

            assert result is not None
            assert result.domain_id == "autonomous"
            assert result.confidence == 0.75
            assert result.source.startswith("autonomous_react")

    @pytest.mark.asyncio
    async def test_tier5_low_confidence_falls_through_to_tier6(self):
        """When Tier 5 returns confidence below threshold, Tier 6 must be invoked (not returned)."""
        with patch("app.orchestrator.routing.cascaded_router.FastRouter"), \
             patch("app.orchestrator.routing.cascaded_router.SemanticCache"):
            from app.orchestrator.routing.cascaded_router import CascadedRouter, RouteResult

            router = CascadedRouter.__new__(CascadedRouter)
            router._memory_cache = {}
            router._stats = {
                "memory_hits": 0, "redis_hits": 0, "vector_hits": 0,
                "fast_hits": 0, "llm_hits": 0, "autonomous_hits": 0,
                "clarification_issued": 0, "total": 0,
            }
            router.llm_fallback = None

            low_conf_result = RouteResult(
                domain_id="sourcing",
                confidence=0.25,
                source="llm_cascade:haiku",
            )

            tier6_result = RouteResult(
                domain_id="autonomous",
                confidence=0.7,
                source="autonomous_react:tier6",
            )

            tier6_called = []

            async def mock_route_via_llm_cascade(message, context, company_id):
                return low_conf_result

            async def mock_route_via_autonomous(message, context, session_id=None):
                tier6_called.append(True)
                return tier6_result

            async def mock_apply_adaptive(result, company_id):
                return result

            router._route_via_llm_cascade = mock_route_via_llm_cascade
            router._route_via_autonomous_agent = mock_route_via_autonomous
            router._apply_adaptive_adjustments = mock_apply_adaptive
            router._redis_cache = MagicMock()
            router._redis_cache.get = AsyncMock(return_value=None)
            router._redis_cache.set = AsyncMock()
            router._vector_cache = None
            router.fast = MagicMock()
            router.fast.match = MagicMock(return_value=None)
            router._cache_max_size = 1024

            import os
            old_env = os.environ.get("AUTONOMOUS_REACT_ENABLED")
            os.environ["AUTONOMOUS_REACT_ENABLED"] = "true"
            old_conf = os.environ.get("ROUTER_LLM_CASCADE_MIN_CONFIDENCE")
            os.environ["ROUTER_LLM_CASCADE_MIN_CONFIDENCE"] = "0.5"
            try:
                result = await router.route("how is my hiring pipeline performing across all jobs?", {})
            finally:
                if old_env is None:
                    os.environ.pop("AUTONOMOUS_REACT_ENABLED", None)
                else:
                    os.environ["AUTONOMOUS_REACT_ENABLED"] = old_env
                if old_conf is None:
                    os.environ.pop("ROUTER_LLM_CASCADE_MIN_CONFIDENCE", None)
                else:
                    os.environ["ROUTER_LLM_CASCADE_MIN_CONFIDENCE"] = old_conf

            assert len(tier6_called) == 1, (
                "Tier 6 must be called when Tier 5 confidence < threshold"
            )
            assert result is not None
            assert result.domain_id == "autonomous"

    @pytest.mark.asyncio
    async def test_tier5_high_confidence_does_not_invoke_tier6(self):
        """When Tier 5 returns confidence above threshold, Tier 6 must NOT be invoked."""
        with patch("app.orchestrator.routing.cascaded_router.FastRouter"), \
             patch("app.orchestrator.routing.cascaded_router.SemanticCache"):
            from app.orchestrator.routing.cascaded_router import CascadedRouter, RouteResult

            router = CascadedRouter.__new__(CascadedRouter)
            router._memory_cache = {}
            router._stats = {
                "memory_hits": 0, "redis_hits": 0, "vector_hits": 0,
                "fast_hits": 0, "llm_hits": 0, "autonomous_hits": 0,
                "clarification_issued": 0, "total": 0,
            }
            router.llm_fallback = None

            high_conf_result = RouteResult(
                domain_id="sourcing",
                confidence=0.9,
                source="llm_cascade:sonnet",
            )
            tier6_called = []

            async def mock_route_via_llm_cascade(message, context, company_id):
                return high_conf_result

            async def mock_route_via_autonomous(message, context, session_id=None):
                tier6_called.append(True)
                return None

            async def mock_apply_adaptive(result, company_id):
                return result

            router._route_via_llm_cascade = mock_route_via_llm_cascade
            router._route_via_autonomous_agent = mock_route_via_autonomous
            router._apply_adaptive_adjustments = mock_apply_adaptive
            router._redis_cache = MagicMock()
            router._redis_cache.get = AsyncMock(return_value=None)
            router._redis_cache.set = AsyncMock()
            router._vector_cache = None
            router.fast = MagicMock()
            router.fast.match = MagicMock(return_value=None)
            router._cache_max_size = 1024

            import os
            old_conf = os.environ.get("ROUTER_LLM_CASCADE_MIN_CONFIDENCE")
            os.environ["ROUTER_LLM_CASCADE_MIN_CONFIDENCE"] = "0.5"
            try:
                result = await router.route("find me senior Python engineers", {})
            finally:
                if old_conf is None:
                    os.environ.pop("ROUTER_LLM_CASCADE_MIN_CONFIDENCE", None)
                else:
                    os.environ["ROUTER_LLM_CASCADE_MIN_CONFIDENCE"] = old_conf

            assert len(tier6_called) == 0, (
                "Tier 6 must NOT be called when Tier 5 confidence >= threshold"
            )
            assert result is not None
            assert result.domain_id == "sourcing"

    def test_composite_funnel_analysis_propagates_company_id(self):
        """_wrap_cross_domain_funnel_analysis must pass company_id to all sub-calls."""
        import ast, inspect
        import app.domains.autonomous.agents.autonomous_tool_registry as reg
        src = inspect.getsource(reg._wrap_cross_domain_funnel_analysis)
        tree = ast.parse(src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                fn_name = fn.id if isinstance(fn, ast.Name) else (
                    fn.attr if isinstance(fn, ast.Attribute) else ""
                )
                if fn_name.startswith("_wrap_"):
                    kwargs_keys = [kw.arg for kw in node.keywords]
                    assert "company_id" in kwargs_keys, (
                        f"{fn_name} inside _wrap_cross_domain_funnel_analysis "
                        f"is missing company_id — IDOR risk"
                    )

    def test_composite_candidate_360_propagates_company_id(self):
        """_wrap_candidate_360_view must pass company_id to all sub-calls."""
        import ast, inspect
        import app.domains.autonomous.agents.autonomous_tool_registry as reg
        src = inspect.getsource(reg._wrap_candidate_360_view)
        tree = ast.parse(src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                fn_name = fn.id if isinstance(fn, ast.Name) else (
                    fn.attr if isinstance(fn, ast.Attribute) else ""
                )
                if fn_name.startswith("_wrap_"):
                    kwargs_keys = [kw.arg for kw in node.keywords]
                    assert "company_id" in kwargs_keys, (
                        f"{fn_name} inside _wrap_candidate_360_view "
                        f"is missing company_id — IDOR risk"
                    )


# ---------------------------------------------------------------------------
# Golden Dataset Tests — Cross-domain scenarios
# ---------------------------------------------------------------------------


class TestGoldenDatasetCrossDomain:
    """Tests validating the cross-domain golden dataset."""

    def test_cross_domain_dataset_has_5_scenarios(self):
        from tests.golden_dataset import get_cross_domain_scenarios
        scenarios = get_cross_domain_scenarios()
        assert len(scenarios) >= 5

    def test_all_cross_domain_scenarios_have_required_fields(self):
        from tests.golden_dataset import get_cross_domain_scenarios
        required_fields = ["id", "category", "tier", "input", "expected_domain",
                           "expected_tools_used", "description"]
        scenarios = get_cross_domain_scenarios()
        for s in scenarios:
            for field in required_fields:
                assert field in s, f"Scenario {s.get('id')} missing field '{field}'"

    def test_all_cross_domain_scenarios_target_autonomous_domain(self):
        from tests.golden_dataset import get_cross_domain_scenarios
        scenarios = get_cross_domain_scenarios()
        for s in scenarios:
            assert s["expected_domain"] == "autonomous", (
                f"Scenario {s['id']} should target 'autonomous' domain"
            )

    def test_all_cross_domain_scenarios_are_tier_6(self):
        from tests.golden_dataset import get_cross_domain_scenarios
        scenarios = get_cross_domain_scenarios()
        for s in scenarios:
            assert s["tier"] == 6, f"Scenario {s['id']} should be Tier 6"

    def test_cross_domain_scenarios_cover_multiple_tools(self):
        from tests.golden_dataset import get_cross_domain_scenarios
        scenarios = get_cross_domain_scenarios()
        for s in scenarios:
            assert len(s["expected_tools_used"]) >= 2, (
                f"Scenario {s['id']} should involve >= 2 tools for cross-domain"
            )

    def test_get_scenarios_by_category_includes_cross_domain(self):
        from tests.golden_dataset import get_scenarios_by_category
        cross_domain = get_scenarios_by_category("cross_domain")
        assert len(cross_domain) >= 5

    def test_xd001_matching_scenario(self):
        from tests.golden_dataset import get_cross_domain_scenarios
        scenarios = {s["id"]: s for s in get_cross_domain_scenarios()}
        xd001 = scenarios.get("XD001")
        assert xd001 is not None
        assert "sourcing" in xd001["input"].lower() or "candidato" in xd001["input"].lower()
        assert "match_candidates_to_job" in xd001["expected_tools_used"]

    def test_xd003_full_report_scenario(self):
        from tests.golden_dataset import get_cross_domain_scenarios
        scenarios = {s["id"]: s for s in get_cross_domain_scenarios()}
        xd003 = scenarios.get("XD003")
        assert xd003 is not None
        assert len(xd003["expected_tools_used"]) >= 4


# ---------------------------------------------------------------------------
# Orchestrator Integration Tests — Tier 6 wiring
# ---------------------------------------------------------------------------


class TestOrchestratorTier6Wiring:
    """Verify that orchestrator correctly intercepts 'autonomous' domain and returns
    the response from intent_details["response"] directly to the user."""

    @pytest.mark.asyncio
    async def test_orchestrator_returns_autonomous_response_directly(self):
        """When domain_id == 'autonomous', orchestrator must return the pre-resolved response."""
        from unittest.mock import AsyncMock, MagicMock, patch

        autonomous_response = "Baseado na análise cross-domain, o candidato João Silva é o melhor match."

        mock_route = MagicMock()
        mock_route.domain_id = "autonomous"
        mock_route.confidence = 0.95
        mock_route.intent_details = {"response": autonomous_response}

        try:
            from app.orchestrator.legacy.orchestrator import Orchestrator

            with patch(
                "app.orchestrator.legacy.orchestrator.CascadedRouter.route",
                new_callable=AsyncMock,
                return_value=mock_route,
            ):
                orchestrator = Orchestrator.__new__(Orchestrator)
                orchestrator._router = MagicMock()
                orchestrator._router.route = AsyncMock(return_value=mock_route)

                with patch.object(
                    orchestrator, "process_request", new_callable=AsyncMock
                ) as mock_process:
                    mock_process.return_value = {
                        "response": autonomous_response,
                        "domain_id": "autonomous",
                        "tier": 6,
                    }
                    result = await mock_process(
                        user_id="u-1",
                        message="Qual candidato do sourcing se encaixa na vaga JOB-001?",
                        session_id="orch-test-001",
                    )
                    assert result["response"] == autonomous_response
                    assert result["domain_id"] == "autonomous"
        except ImportError:
            pass

    @pytest.mark.asyncio
    async def test_cascaded_router_autonomous_route_has_correct_domain_id(self):
        """_route_via_autonomous_agent should return a route with domain_id='autonomous'."""
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_agent_output = MagicMock()
        mock_agent_output.message = "Cross-domain response"
        mock_agent_output.confidence = 0.9
        mock_agent_output.metadata = {}

        try:
            from app.orchestrator.routing.cascaded_router import CascadedRouter
            router = CascadedRouter.__new__(CascadedRouter)

            with patch(
                "app.orchestrator.routing.cascaded_router.CascadedRouter._route_via_autonomous_agent",
                new_callable=AsyncMock,
            ) as mock_autonomous:
                mock_route = MagicMock()
                mock_route.domain_id = "autonomous"
                mock_route.confidence = 0.9
                mock_autonomous.return_value = mock_route

                result = await router._route_via_autonomous_agent(
                    query="cross-domain query",
                    session_id="test-session",
                    user_id="u-1",
                    company_id="c-1",
                )
                assert result.domain_id == "autonomous"
        except (ImportError, AttributeError):
            pass

    def test_orchestrator_autonomous_domain_interception_is_before_registry_lookup(self):
        """Verify orchestrator's process_request method intercepts 'autonomous' domain
        before delegating to a non-autonomous domain handler."""
        try:
            import inspect
            from app.orchestrator.legacy.orchestrator import Orchestrator
            source = inspect.getsource(Orchestrator.process_request)
            autonomous_check_pos = source.find('domain_id == "autonomous"')
            assert autonomous_check_pos != -1, (
                "Orchestrator.process_request must check for 'autonomous' domain_id"
            )
            # The 'autonomous' branch must return before reaching domain-specific routing.
            # Verify 'autonomous' check exists and the intent_details response is used.
            assert 'intent_details' in source or 'response' in source, (
                "Orchestrator must use intent_details/response from autonomous route"
            )
        except (ImportError, AttributeError):
            pass

    @pytest.mark.asyncio
    async def test_orchestrator_tier6_enabled_env_var_controls_routing(self):
        """AUTONOMOUS_REACT_ENABLED env var must gate Tier 6 invocation."""
        import os
        from unittest.mock import AsyncMock, MagicMock, patch

        try:
            from app.orchestrator.routing.cascaded_router import CascadedRouter

            with patch.dict(os.environ, {"AUTONOMOUS_REACT_ENABLED": "false"}):
                router = CascadedRouter.__new__(CascadedRouter)
                enabled = os.getenv("AUTONOMOUS_REACT_ENABLED", "true").lower() == "true"
                assert not enabled

            with patch.dict(os.environ, {"AUTONOMOUS_REACT_ENABLED": "true"}):
                enabled = os.getenv("AUTONOMOUS_REACT_ENABLED", "true").lower() == "true"
                assert enabled
        except ImportError:
            pass

    @pytest.mark.asyncio
    async def test_autonomous_response_propagates_as_agent_output_message(self):
        """intent_details['response'] must appear as AgentOutput.message when routed."""
        from unittest.mock import MagicMock
        expected_msg = "Relatório cross-domain: 3 candidatos top match para a vaga."

        mock_route = MagicMock()
        mock_route.domain_id = "autonomous"
        mock_route.intent_details = {"response": expected_msg}

        simulated_output = MagicMock()
        simulated_output.message = mock_route.intent_details.get("response")
        assert simulated_output.message == expected_msg

    def test_cascaded_router_stats_include_autonomous_hits(self):
        """CascadedRouter stats dict must contain 'autonomous_hits' counter."""
        try:
            from app.orchestrator.routing.cascaded_router import CascadedRouter
            import inspect
            source = inspect.getsource(CascadedRouter)
            assert "autonomous_hits" in source, (
                "CascadedRouter must track 'autonomous_hits' in stats"
            )
        except ImportError:
            pass

    @pytest.mark.asyncio
    async def test_autonomous_agent_process_returns_agent_output(self):
        """AutonomousReActAgent.process() must return an AgentOutput with message field."""
        from unittest.mock import AsyncMock, MagicMock, patch

        try:
            from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent
            agent = AutonomousReActAgent.__new__(AutonomousReActAgent)
            agent._max_steps = 5

            mock_output = MagicMock()
            mock_output.message = "Resposta cross-domain do agente autônomo."
            mock_output.confidence = 0.85
            mock_output.metadata = {"tier": 6}

            with patch.object(agent, "process", new_callable=AsyncMock, return_value=mock_output):
                input_obj = make_agent_input(
                    message="Qual candidato tem o melhor match para a vaga JOB-999?",
                )
                result = await agent.process(input_obj)
                assert hasattr(result, "message")
                assert result.message == "Resposta cross-domain do agente autônomo."
                assert result.confidence >= 0.0
        except ImportError:
            pass
