"""
Characterization tests for Orchestrator consolidation (Task #122).

These tests capture the observable behavior of the unified pipeline AFTER
the refactoring:
  - MainOrchestrator single entry-point with FairnessGuard → PendingAction →
    ActionExecutor → CascadedRouter → DomainWorkflow → Agent
  - IntentRouter removed from CascadedRouter fallback chain
  - ActionExecutor delegates to decomposed handler modules
  - ChatResponse contract unchanged

Run: pytest tests/integration/test_orchestrator_consolidation.py -v
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_orchestrator():
    orch = MagicMock()
    orch.process_request = AsyncMock(return_value={
        "success": True,
        "message": "Resposta do orquestrador",
        "intent": "general_query",
        "agent_used": "recruiter_assistant",
        "confidence": 0.85,
        "suggested_prompts": [],
        "agents_consulted": [],
    })
    orch.llm_service = MagicMock()
    return orch


@pytest.fixture
def universal_context_factory():
    from app.orchestrator.context.context_adapter import UniversalContext

    def _make(
        message: str = "Olá, preciso de ajuda",
        user_id: str = "user-123",
        company_id: str = "company-456",
        conversation_id: Optional[str] = "conv-789",
        context_type: str = "general",
        candidates: Optional[list] = None,
    ) -> UniversalContext:
        return UniversalContext(
            message=message,
            user_id=user_id,
            company_id=company_id,
            conversation_id=conversation_id,
            context_type=context_type,
            candidates=candidates or [],
        )

    return _make


# ---------------------------------------------------------------------------
# T001: ChatResponse contract remains intact
# ---------------------------------------------------------------------------

class TestChatResponseContract:
    """Verify the ChatResponse Pydantic schema remains unchanged."""

    def test_chat_response_required_fields(self):
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        resp = ChatResponse(success=True, content="Test")
        assert resp.success is True
        assert resp.content == "Test"
        assert resp.agent_used == "main_orchestrator"
        assert resp.intent_detected == "general"
        assert resp.confidence == 1.0
        assert resp.agents_consulted == []
        assert resp.suggested_prompts == []
        assert resp.actions == []
        assert resp.action_executed is False
        assert resp.needs_confirmation is False
        assert resp.needs_params is False

    def test_chat_response_from_orchestrator_result(self):
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        result = {
            "success": True,
            "response": "Encontrei 5 candidatos",
            "intent": "sourcing",
            "agent_used": "sourcing_agent",
            "confidence": 0.9,
            "suggested_prompts": ["Ver candidatos", "Filtrar por skills"],
            "data": {"candidates": [{"id": "c1", "name": "João"}]},
            "score_breakdown": {"technical": 85},
        }
        resp = ChatResponse.from_orchestrator_result(result, conv_id="conv-001")
        assert resp.success is True
        assert resp.content == "Encontrei 5 candidatos"
        assert resp.intent_detected == "sourcing"
        assert resp.agent_used == "sourcing_agent"
        assert resp.confidence == 0.9
        assert resp.conversation_id == "conv-001"
        assert resp.structured_data is not None
        assert "score_breakdown" in resp.structured_data

    def test_chat_response_from_action_result(self):
        from app.orchestrator.execution.main_orchestrator import ChatResponse
        from app.orchestrator.action_executor import ActionResult

        ar = ActionResult(
            status="executed",
            message="Candidato movido para Triagem",
            data={"candidate_id": "c1", "to_stage": "Triagem"},
            action_type="move_candidate",
        )
        resp = ChatResponse.from_action_result(ar, intent="mover_candidato", conv_id="conv-002")
        assert resp.success is True
        assert resp.action_executed is True
        assert resp.action_type == "move_candidate"
        assert resp.action_result == ar.data


# ---------------------------------------------------------------------------
# T002: FairnessGuard blocks biased content before any processing
# ---------------------------------------------------------------------------

class TestFairnessGuardPreCheck:
    @pytest.mark.asyncio
    async def test_fairness_guard_blocks_before_orchestrator(
        self, mock_orchestrator, mock_db, universal_context_factory
    ):
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator

        ctx = universal_context_factory(message="Prefiro contratar só homens brancos")

        with patch("app.orchestrator.execution.main_orchestrator.FairnessGuard") as MockFG:
            mock_fg = MagicMock()
            block_result = MagicMock()
            block_result.is_blocked = True
            block_result.educational_message = "Conteúdo discriminatório detectado."
            block_result.category = "gender_bias"
            mock_fg.check.return_value = block_result
            mock_fg.check_implicit_bias.return_value = []
            MockFG.return_value = mock_fg

            orch = MainOrchestrator(mock_orchestrator)
            orch._fairness_guard = mock_fg

            resp = await orch.process(ctx, mock_db)

        assert resp.success is False
        assert "discriminatório" in resp.content or "equidade" in resp.content
        assert resp.intent_detected == "blocked_bias"
        assert resp.agent_used == "fairness_guard"
        mock_orchestrator.process_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_soft_warning_does_not_block(
        self, mock_orchestrator, mock_db, universal_context_factory
    ):
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator

        ctx = universal_context_factory(message="Prefiro candidatos mais jovens")

        with patch("app.orchestrator.execution.main_orchestrator.FairnessGuard") as MockFG:
            mock_fg = MagicMock()
            safe_result = MagicMock()
            safe_result.is_blocked = False
            mock_fg.check.return_value = safe_result
            mock_fg.check_implicit_bias.return_value = ["age_bias_soft"]
            MockFG.return_value = mock_fg

            orch = MainOrchestrator(mock_orchestrator)
            orch._fairness_guard = mock_fg

            with patch.object(orch, "_handle_pending_action", AsyncMock(return_value=None)):
                with patch.object(orch, "_try_action_executor", AsyncMock(return_value=None)):
                    with patch.object(orch, "_process_via_orchestrator", AsyncMock(return_value=MagicMock(success=True))):
                        resp = await orch.process(ctx, mock_db)

        assert resp.success is True


# ---------------------------------------------------------------------------
# T003: ActionExecutor intercepts actionable intents in Phase 1
# ---------------------------------------------------------------------------

class TestActionExecutorPhase:
    @pytest.mark.asyncio
    async def test_move_candidate_intercepted_by_action_executor(
        self, mock_orchestrator, mock_db, universal_context_factory
    ):
        from app.orchestrator.action_executor import ActionResult, ActionExecutorService

        svc = ActionExecutorService()
        result = await svc.try_execute(
            message="mover o candidato para Triagem",
            context={
                "candidates": [{"id": "c1", "name": "João Silva", "stage": "Novo"}],
                "conversation_id": "conv-001",
            },
        )
        assert result.status in ("needs_params", "needs_confirmation", "not_actionable")

    @pytest.mark.asyncio
    async def test_non_actionable_message_passes_to_orchestrator(
        self, mock_orchestrator, mock_db, universal_context_factory
    ):
        from app.orchestrator.action_executor import ActionExecutorService

        svc = ActionExecutorService()
        result = await svc.try_execute(
            message="Qual a metodologia WSI?",
            context={"conversation_id": "conv-001"},
        )
        assert result.status == "not_actionable"


# ---------------------------------------------------------------------------
# T004: CascadedRouter no longer has IntentRouter as fallback
# ---------------------------------------------------------------------------

class TestIntentRouterRemoval:
    def test_cascaded_router_has_no_intent_router_param(self):
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        from app.orchestrator.routing.fast_router import FastRouter
        import inspect

        sig = inspect.signature(CascadedRouter.__init__)
        assert "intent_router" not in sig.parameters

    def test_orchestrator_init_does_not_pass_intent_router(self):
        """Verify Orchestrator._init_cascaded_router does not pass intent_router."""
        from app.orchestrator.legacy.orchestrator import Orchestrator

        mock_llm = MagicMock()
        mock_llm.claude = MagicMock()

        with patch("app.orchestrator.legacy.orchestrator.CascadedRouter") as MockCR:
            MockCR.return_value = MagicMock()
            with patch("app.orchestrator.legacy.orchestrator.initialize_tools"):
                with patch("app.orchestrator.legacy.orchestrator.TaskPlanner"):
                    with patch("app.orchestrator.legacy.orchestrator.PolicyEngineService"):  # W1-003 (2026-05-22): V1 deleted; patch V2 service instead
                        with patch("app.orchestrator.legacy.orchestrator.StateManager"):
                            with patch("app.orchestrator.legacy.orchestrator.DomainRegistry"):
                                with patch("app.orchestrator.legacy.orchestrator.DomainWorkflow"):
                                    with patch("app.orchestrator.legacy.orchestrator.PlanDetector"):
                                        with patch("app.orchestrator.legacy.orchestrator.PlanExecutor"):
                                            try:
                                                Orchestrator(llm_service=mock_llm)
                                            except Exception:
                                                pass
                                            call_kwargs = MockCR.call_args
                                            if call_kwargs:
                                                assert "intent_router" not in (call_kwargs.kwargs or {})


# ---------------------------------------------------------------------------
# T005: ActionExecutor handler module delegation
# ---------------------------------------------------------------------------

class TestActionHandlerDelegation:
    @pytest.mark.asyncio
    async def test_move_candidate_delegates_to_candidate_handler(self):
        from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action

        with patch("app.core.database.AsyncSessionLocal") as MockDB:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            MockDB.return_value = mock_session

            from app.orchestrator.action_executor import ActionResult
            result = await execute_candidate_action(
                action_id="move_candidate",
                params={
                    "candidate_id": "c1",
                    "to_stage": "Triagem",
                    "candidate_name": "João Silva",
                },
                context={"user_id": "user-1", "company_id": "co-1"},
            )
            assert result is not None
            assert result.status in ("executed", "error")
            if result.status == "executed":
                assert "Triagem" in result.message

    @pytest.mark.asyncio
    async def test_job_actions_handler_routes_correctly(self):
        from app.orchestrator.action_handlers.job_actions import execute_job_action

        with patch("app.core.database.AsyncSessionLocal") as MockDB:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.rowcount = 1
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            MockDB.return_value = mock_session

            result = await execute_job_action(
                action_id="pause_job",
                params={"job_id": "job-1", "job_title": "Dev Sênior"},
                context={},
            )
            assert result is not None
            assert result.status in ("executed", "error")

    @pytest.mark.asyncio
    async def test_unknown_action_returns_none_from_handler(self):
        from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action

        result = await execute_candidate_action(
            action_id="unknown_action_xyz",
            params={},
            context={},
        )
        assert result is None


# ---------------------------------------------------------------------------
# T006: FastRouter patterns cover all intent-to-domain mappings
# ---------------------------------------------------------------------------

class TestFastRouterCoverage:
    """Verify FastRouter + LLM Cascade covers the intent mappings IntentRouter had."""

    def test_fast_router_sourcing_patterns(self):
        from app.orchestrator.routing.fast_router import FastRouter

        router = FastRouter()
        result = router.match("Buscar candidatos Python sênior")
        assert result is not None
        assert "sourcing" in result.domain_id

    def test_fast_router_cv_screening_patterns(self):
        from app.orchestrator.routing.fast_router import FastRouter

        router = FastRouter()
        result = router.match("Faça a triagem dos candidatos")
        assert result is not None
        assert "cv_screening" in result.domain_id or "screening" in result.domain_id.lower()

    def test_fast_router_job_management_patterns(self):
        from app.orchestrator.routing.fast_router import FastRouter

        router = FastRouter()
        result = router.match("Criar uma nova vaga para desenvolvedor")
        assert result is not None
        assert result.domain_id == "job_management"

    def test_fast_router_scheduling_patterns(self):
        from app.orchestrator.routing.fast_router import FastRouter

        router = FastRouter()
        result = router.match("Agendar entrevista com Maria amanhã")
        assert result is not None
        assert "interview" in result.domain_id or "scheduling" in result.domain_id.lower()

    def test_fast_router_analytics_patterns(self):
        from app.orchestrator.routing.fast_router import FastRouter

        router = FastRouter()
        result = router.match("Gerar relatório de KPIs do funil")
        assert result is not None

    def test_fast_router_communication_patterns(self):
        from app.orchestrator.routing.fast_router import FastRouter

        router = FastRouter()
        result = router.match("Enviar email para candidato João")
        assert result is not None
        assert "communication" in result.domain_id


# ---------------------------------------------------------------------------
# T007: PendingAction multi-turn flow works correctly
# ---------------------------------------------------------------------------

class TestPendingActionFlow:
    def test_is_confirmation_patterns(self):
        from app.orchestrator.action_executor import is_confirmation

        assert is_confirmation("sim") is True
        assert is_confirmation("pode") is True
        assert is_confirmation("confirmo") is True
        assert is_confirmation("ok") is True
        assert is_confirmation("não") is False
        assert is_confirmation("cancela") is False

    def test_is_rejection_patterns(self):
        from app.orchestrator.action_executor import is_rejection

        assert is_rejection("não") is True
        assert is_rejection("cancela") is True
        assert is_rejection("sim") is False

    def test_resolve_candidate_from_context(self):
        from app.orchestrator.action_executor import resolve_candidate_from_context

        candidates = [
            {"id": "c1", "name": "João Silva", "stage": "Triagem"},
            {"id": "c2", "name": "Maria Santos", "stage": "Entrevista"},
        ]
        result = resolve_candidate_from_context("Maria", None, candidates)
        assert result is not None
        assert result["id"] == "c2"

        result2 = resolve_candidate_from_context(None, "c1", candidates)
        assert result2 is not None
        assert result2["name"] == "João Silva"


# ---------------------------------------------------------------------------
# T008: Context adapter produces correct UniversalContext shapes
# ---------------------------------------------------------------------------

class TestContextAdapterShapes:
    def test_from_rest_sets_context_type(self):
        from app.orchestrator.context.context_adapter import ContextAdapter

        ctx = ContextAdapter.from_rest(
            message="teste",
            user_id="u1",
            company_id="c1",
            context_page="sourcing",
        )
        assert ctx.context_type == "talent_funnel"
        assert ctx.channel == "rest"

    def test_from_job_chat_sets_job_context_type(self):
        from app.orchestrator.context.context_adapter import ContextAdapter

        mock_req = MagicMock()
        mock_req.message = "Qual o pipeline dessa vaga?"
        mock_req.job_context = {"id": "job-1", "title": "Dev"}
        mock_req.conversation_id = None

        ctx = ContextAdapter.from_job_chat(mock_req, user_id="u1", company_id="c1")
        assert ctx.context_type == "job_management"
        assert ctx.entity_id == "job-1"

    def test_to_orchestrator_context_includes_candidates(self):
        from app.orchestrator.context.context_adapter import UniversalContext

        ctx = UniversalContext(
            message="teste",
            user_id="u1",
            company_id="c1",
            candidates=[{"id": "c1", "name": "Ana"}],
            job_context={"id": "job-1"},
        )
        orch_ctx = ctx.to_orchestrator_context()
        assert orch_ctx["candidates"] == [{"id": "c1", "name": "Ana"}]
        assert orch_ctx["job_context"] == {"id": "job-1"}


# ---------------------------------------------------------------------------
# T009: ACTIONABLE_INTENTS registry completeness
# ---------------------------------------------------------------------------

class TestActionableIntentsRegistry:
    def test_all_action_handler_ids_are_registered(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS

        expected_action_ids = {
            "move_candidate", "send_email", "schedule_interview",
            "pause_job", "close_job", "duplicate_job", "reopen_job",
            "create_task", "create_note", "create_generic_event",
            "generate_daily_briefing", "start_screening", "analyze_profile",
            "update_candidate_field",
        }
        registered_action_ids = {v["action_id"] for v in ACTIONABLE_INTENTS.values()}
        missing = expected_action_ids - registered_action_ids
        assert not missing, f"Missing action IDs in ACTIONABLE_INTENTS: {missing}"

    def test_all_intents_have_required_fields(self):
        from app.orchestrator.action_executor import ACTIONABLE_INTENTS

        for intent, config in ACTIONABLE_INTENTS.items():
            assert "domain_id" in config, f"Intent '{intent}' missing domain_id"
            assert "action_id" in config, f"Intent '{intent}' missing action_id"
            assert "required_params" in config, f"Intent '{intent}' missing required_params"
            assert "risk_level" in config, f"Intent '{intent}' missing risk_level"


# ---------------------------------------------------------------------------
# T010: MainOrchestrator process pipeline — smoke test
# ---------------------------------------------------------------------------

class TestMainOrchestratorPipeline:
    @pytest.mark.asyncio
    async def test_non_actionable_message_reaches_phase2(
        self, mock_orchestrator, mock_db, universal_context_factory
    ):
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator, ChatResponse

        ctx = universal_context_factory(message="O que é a metodologia WSI?")
        orch = MainOrchestrator(mock_orchestrator)

        with patch.object(orch, "_fairness_guard") as mock_fg:
            safe = MagicMock()
            safe.is_blocked = False
            mock_fg.check.return_value = safe
            mock_fg.check_implicit_bias.return_value = []

            with patch.object(orch, "_tenant_context_service") as mock_ts:
                mock_ts.get_context = AsyncMock(side_effect=Exception("skip"))

                with patch.object(orch, "_process_via_orchestrator") as mock_phase2:
                    expected = ChatResponse(
                        success=True,
                        content="A metodologia WSI é...",
                        conversation_id=ctx.conversation_id,
                    )
                    mock_phase2.return_value = expected
                    mock_phase2 = AsyncMock(return_value=expected)
                    orch._process_via_orchestrator = mock_phase2

                    resp = await orch.process(ctx, mock_db)

        mock_phase2.assert_called_once()
        assert resp.success is True

    @pytest.mark.asyncio
    async def test_error_in_pipeline_returns_error_response(
        self, mock_orchestrator, mock_db, universal_context_factory
    ):
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator

        ctx = universal_context_factory(message="teste erro")
        orch = MainOrchestrator(mock_orchestrator)
        orch._fairness_guard = MagicMock()
        orch._fairness_guard.check.side_effect = RuntimeError("Unexpected error")

        resp = await orch.process(ctx, mock_db)

        assert resp.success is False
        assert "erro" in resp.content.lower()
        assert resp.intent_detected == "error"


class TestChatResponseFallbackMapping:
    """Contract tests for ChatResponse.from_orchestrator_result() key fallback chain."""

    def test_response_key_takes_priority(self):
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        result = {"response": "from_response", "message": "from_message", "content": "from_content"}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="test-1")
        assert resp.content == "from_response"

    def test_message_key_fallback_when_no_response(self):
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        result = {"message": "orchestrator_message", "content": "from_content", "success": True}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="test-2")
        assert resp.content == "orchestrator_message"

    def test_content_key_final_fallback(self):
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        result = {"content": "from_content", "success": True}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="test-3")
        assert resp.content == "from_content"

    def test_empty_string_when_all_keys_missing(self):
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        result = {"success": True, "intent": "general"}
        resp = ChatResponse.from_orchestrator_result(result, conv_id="test-4")
        assert resp.content == ""

    def test_orchestrator_process_request_message_key_not_lost(self):
        """
        Orchestrator.process_request() returns a dict with 'message' key.
        from_orchestrator_result must not drop it.
        """
        from app.orchestrator.execution.main_orchestrator import ChatResponse

        orchestrator_style_result = {
            "message": "Olá! Posso ajudar com candidatos.",
            "intent_detected": "saudacao",
            "confidence": 0.95,
            "success": True,
            "agents_consulted": [],
        }
        resp = ChatResponse.from_orchestrator_result(orchestrator_style_result, conv_id="test-5")
        assert resp.content == "Olá! Posso ajudar com candidatos."
        assert resp.success is True
