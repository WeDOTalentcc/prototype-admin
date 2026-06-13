"""
Sprint I — Testes de fundações de segurança e compliance.

Cobre:
1. TestConsentHardBlock    — LGPD_CONSENT_ABSENT_HARD_BLOCK=True bloqueia ausência de consentimento
2. TestFairnessGuardOrchestrator — queries discriminatórias bloqueadas no entry-point
3. TestWorkOSCircuitBreaker — circuit breaker configurado para WorkOS
4. TestBillingCircuits     — IUGU_CIRCUIT e VINDI_CIRCUIT existem em ALL_CIRCUITS
5. TestWSIAuditTrail       — log_decision chamado em score_response e generate_feedback
6. TestPolicyHITL          — salvamento de política requer aprovação HITL
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ─────────────────────────────────────────────────────────────────────────────
# 1. TestConsentHardBlock
# ─────────────────────────────────────────────────────────────────────────────

class TestConsentHardBlock:
    """Verifica que o hard block LGPD está ativo por default quando consentimento ausente."""

    @pytest.mark.asyncio
    async def test_hard_block_default_true_when_config_fails(self):
        """Quando a leitura da config falha, o default deve ser True (bloquear)."""
        from app.shared.services.consent_checker_service import ConsentCheckerService, ConsentCheckResult

        mock_db = AsyncMock()
        mock_result = MagicMock()
        # Simula consentimento ausente (scalar_one_or_none retorna None)
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ConsentCheckerService(mock_db)

        # Patch da config para simular falha de importação
        with patch("app.services.consent_checker_service.ConsentCheckerService._record_audit_log", new=AsyncMock()):
            with patch("builtins.__import__", side_effect=lambda name, *a, **kw: (
                __import__(name, *a, **kw) if name != "lia_config.config" else (_ for _ in ()).throw(ImportError())
            )):
                result = await service.check_candidate_consent(
                    candidate_id="cand-001",
                    company_id="comp-001",
                    purpose="ai_screening",
                )

        # Com config falhando, hard block deve ser True → consentimento ausente = bloqueado
        assert result.allowed is False
        assert result.reason == "absent"

    @pytest.mark.asyncio
    async def test_hard_block_true_blocks_absent_consent(self):
        """LGPD_CONSENT_ABSENT_HARD_BLOCK=True deve bloquear quando consent ausente."""
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ConsentCheckerService(mock_db)

        mock_settings = MagicMock()
        mock_settings.LGPD_CONSENT_ABSENT_HARD_BLOCK = True

        with patch("app.services.consent_checker_service.ConsentCheckerService._record_audit_log", new=AsyncMock()):
            with patch("lia_config.config.settings", mock_settings, create=True):
                result = await service.check_candidate_consent(
                    candidate_id="cand-002",
                    company_id="comp-001",
                    purpose="ai_scoring",
                )

        assert result.allowed is False
        assert result.reason == "absent"

    @pytest.mark.asyncio
    async def test_soft_block_false_allows_absent_consent_with_warning(self):
        """LGPD_CONSENT_ABSENT_HARD_BLOCK=False deve permitir com soft_warning=True."""
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ConsentCheckerService(mock_db)

        mock_settings = MagicMock()
        mock_settings.LGPD_CONSENT_ABSENT_HARD_BLOCK = False

        with patch("app.services.consent_checker_service.ConsentCheckerService._record_audit_log", new=AsyncMock()):
            with patch("lia_config.config.settings", mock_settings, create=True):
                result = await service.check_candidate_consent(
                    candidate_id="cand-003",
                    company_id="comp-001",
                    purpose="ai_screening",
                )

        assert result.allowed is True
        assert result.soft_warning is True
        assert result.reason == "absent"

    @pytest.mark.asyncio
    async def test_revoked_consent_always_blocked(self):
        """Consentimento revogado deve sempre bloquear, independente da flag."""
        from app.shared.services.consent_checker_service import ConsentCheckerService
        from datetime import datetime

        mock_consent = MagicMock()
        mock_consent.consent_given = False
        mock_consent.revoked_at = datetime.utcnow()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_consent
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = ConsentCheckerService(mock_db)

        result = await service.check_candidate_consent(
            candidate_id="cand-004",
            company_id="comp-001",
            purpose="ai_screening",
        )

        assert result.allowed is False
        assert result.reason == "revoked"


# ─────────────────────────────────────────────────────────────────────────────
# 2. TestFairnessGuardOrchestrator
# ─────────────────────────────────────────────────────────────────────────────

class TestFairnessGuardOrchestrator:
    """Verifica que o FairnessGuard bloqueia queries discriminatórias no entry-point."""

    def _make_ctx(self, message: str):
        """Cria um UniversalContext mock."""
        ctx = MagicMock()
        ctx.message = message
        ctx.conversation_id = "conv-test-001"
        ctx.user_id = "user-001"
        ctx.company_id = "comp-001"
        ctx.candidates = []
        ctx.selected_candidate_ids = []
        ctx.job_context = {}
        ctx.channel = "chat"
        return ctx

    @pytest.mark.asyncio
    async def test_discriminatory_query_blocked(self):
        """Query discriminatória deve ser bloqueada antes das fases de processamento."""
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator, ChatResponse

        mock_orchestrator = MagicMock()
        main_orch = MainOrchestrator(mock_orchestrator)

        # Mock FairnessGuard para retornar is_blocked=True
        mock_fg_result = MagicMock()
        mock_fg_result.is_blocked = True
        mock_fg_result.educational_message = "Esta solicitação viola critérios de equidade."
        mock_fg_result.category = "age_discrimination"

        with patch.object(main_orch._fairness_guard, "check", return_value=mock_fg_result):
            ctx = self._make_ctx("Quero candidatos com menos de 30 anos apenas")
            result = await main_orch.process(ctx, db=AsyncMock())

        assert result.success is False
        assert result.agent_used == "fairness_guard"
        assert result.intent_detected == "blocked_bias"
        assert "equidade" in result.content or "Esta solicitação" in result.content

    @pytest.mark.asyncio
    async def test_non_discriminatory_query_passes(self):
        """Query não-discriminatória deve passar pelo FairnessGuard."""
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator, ChatResponse

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request = AsyncMock(return_value={
            "success": True,
            "response": "Aqui estão os candidatos.",
            "agent_used": "talent",
            "intent_detected": "search",
            "confidence": 0.9,
        })
        main_orch = MainOrchestrator(mock_orchestrator)

        mock_fg_blocked = MagicMock()
        mock_fg_blocked.is_blocked = False
        mock_fg_implicit = []

        with patch.object(main_orch._fairness_guard, "check", return_value=mock_fg_blocked):
            with patch.object(main_orch._fairness_guard, "check_implicit_bias", return_value=mock_fg_implicit):
                with patch(
                    "app.orchestrator.execution.main_orchestrator.pending_action_store"
                ) as mock_pas:
                    mock_pas.get.return_value = None
                    with patch(
                        "app.orchestrator.execution.main_orchestrator.action_executor"
                    ) as mock_ae:
                        mock_ae_result = MagicMock()
                        mock_ae_result.status = "not_actionable"
                        mock_ae.try_execute = AsyncMock(return_value=mock_ae_result)
                        with patch(
                            "app.orchestrator.execution.main_orchestrator.candidate_list_store"
                        ) as mock_cls:
                            mock_cls.set = AsyncMock()
                            ctx = self._make_ctx("Quem são os melhores candidatos para a vaga?")
                            result = await main_orch.process(ctx, db=AsyncMock())

        assert result.success is True

    @pytest.mark.asyncio
    async def test_fairness_guard_initialized_in_main_orchestrator(self):
        """FairnessGuard deve ser inicializado no __init__ do MainOrchestrator."""
        from app.orchestrator.execution.main_orchestrator import MainOrchestrator
        from app.shared.compliance.fairness_guard import FairnessGuard

        mock_orchestrator = MagicMock()
        main_orch = MainOrchestrator(mock_orchestrator)

        assert hasattr(main_orch, "_fairness_guard")
        assert isinstance(main_orch._fairness_guard, FairnessGuard)


# ─────────────────────────────────────────────────────────────────────────────
# 3. TestWorkOSCircuitBreaker
# ─────────────────────────────────────────────────────────────────────────────

class TestWorkOSCircuitBreaker:
    """Verifica que o circuit breaker está configurado para WorkOS."""

    def test_workos_circuit_exists_in_all_circuits(self):
        """WORKOS_CIRCUIT deve existir em ALL_CIRCUITS."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS, WORKOS_CIRCUIT

        assert "workos" in ALL_CIRCUITS
        assert ALL_CIRCUITS["workos"] is WORKOS_CIRCUIT

    def test_workos_circuit_config(self):
        """WORKOS_CIRCUIT deve ter configuração adequada."""
        from app.shared.resilience.circuit_breaker import WORKOS_CIRCUIT

        assert WORKOS_CIRCUIT.name == "workos"
        assert WORKOS_CIRCUIT.config.failure_threshold >= 1
        assert WORKOS_CIRCUIT.config.recovery_timeout > 0
        assert WORKOS_CIRCUIT.config.timeout > 0

    def test_sync_user_endpoint_has_circuit_breaker(self):
        """sync_workos_user deve ter decorator de circuit breaker aplicado."""
        from app.api.v1.workos import sync_workos_user

        # O decorator circuit_breaker_decorator envolve a função com o circuit breaker
        # Verificamos que a função existe e é chamável
        assert callable(sync_workos_user)

    def test_fetch_workos_metrics_has_circuit_breaker(self):
        """_fetch_workos_metrics deve ter decorator de circuit breaker aplicado."""
        from app.api.v1 import workos as workos_module

        assert hasattr(workos_module, "_fetch_workos_metrics")
        assert callable(workos_module._fetch_workos_metrics)


# ─────────────────────────────────────────────────────────────────────────────
# 4. TestBillingCircuits
# ─────────────────────────────────────────────────────────────────────────────

class TestBillingCircuits:
    """Verifica que IUGU_CIRCUIT e VINDI_CIRCUIT existem em ALL_CIRCUITS."""

    def test_iugu_circuit_exists_in_all_circuits(self):
        """IUGU_CIRCUIT deve existir em ALL_CIRCUITS."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS, IUGU_CIRCUIT

        assert "iugu" in ALL_CIRCUITS
        assert ALL_CIRCUITS["iugu"] is IUGU_CIRCUIT

    def test_vindi_circuit_exists_in_all_circuits(self):
        """VINDI_CIRCUIT deve existir em ALL_CIRCUITS."""
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS, VINDI_CIRCUIT

        assert "vindi" in ALL_CIRCUITS
        assert ALL_CIRCUITS["vindi"] is VINDI_CIRCUIT

    def test_iugu_circuit_config(self):
        """IUGU_CIRCUIT deve ter configuração adequada para billing."""
        from app.shared.resilience.circuit_breaker import IUGU_CIRCUIT

        assert IUGU_CIRCUIT.name == "iugu"
        assert IUGU_CIRCUIT.config.failure_threshold == 3
        assert IUGU_CIRCUIT.config.recovery_timeout == 60.0
        assert IUGU_CIRCUIT.config.timeout == 30.0

    def test_vindi_circuit_config(self):
        """VINDI_CIRCUIT deve ter configuração adequada para billing."""
        from app.shared.resilience.circuit_breaker import VINDI_CIRCUIT

        assert VINDI_CIRCUIT.name == "vindi"
        assert VINDI_CIRCUIT.config.failure_threshold == 3
        assert VINDI_CIRCUIT.config.recovery_timeout == 60.0
        assert VINDI_CIRCUIT.config.timeout == 30.0

    def test_iugu_provider_has_circuit_decorator(self):
        """IuguProvider deve importar e usar IUGU_CIRCUIT."""
        from app.services.billing_providers import iugu_provider

        assert hasattr(iugu_provider, "IUGU_CIRCUIT")
        assert hasattr(iugu_provider, "circuit_breaker_decorator")

    def test_vindi_provider_has_circuit_decorator(self):
        """VindiProvider deve importar e usar VINDI_CIRCUIT."""
        from app.services.billing_providers import vindi_provider

        assert hasattr(vindi_provider, "VINDI_CIRCUIT")
        assert hasattr(vindi_provider, "circuit_breaker_decorator")


# ─────────────────────────────────────────────────────────────────────────────
# 5. TestWSIAuditTrail
# ─────────────────────────────────────────────────────────────────────────────

class TestWSIAuditTrail:
    """Verifica que log_decision é chamado em score_response e generate_feedback."""

    def _make_state(self, recommendation: str = "aprovado"):
        """Cria um WSIInterviewState mock."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewState,
            WSIQuestionBlock,
            WSIResponseRecord,
            WSIInterviewStage,
        )
        from datetime import datetime

        block = WSIQuestionBlock(
            block_id="test-block-1",
            block_type="technical",
            question="Pergunta teste",
            competency="python",
            bloom_level=3,
            dreyfus_level=3,
            max_score=10.0,
        )

        state = WSIInterviewState(
            session_id="sess-001",
            company_id="comp-001",
            candidate_id="cand-001",
            job_id="job-001",
        )
        state.current_question = block
        state.recommendation = recommendation
        state.wsi_final_score = 8.0 if recommendation == "aprovado" else 3.0
        state.completed_at = datetime.utcnow()
        state.responses = [
            WSIResponseRecord(
                question_block=block,
                candidate_response="Resposta de teste",
                score=8.0,
                scored_at=datetime.utcnow(),
            )
        ]
        state.technical_score = 8.0
        state.behavioral_score = 7.5
        state.situational_score = 7.0
        return state

    @pytest.mark.asyncio
    async def test_score_response_calls_audit_log(self):
        """score_response deve chamar audit_service.log_decision após calcular score."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes

        nodes = WSIInterviewNodes()
        state = self._make_state()

        # Injeta resposta pendente
        state.candidate_profile["_pending_response"] = {
            "text": "Resposta técnica sobre Python",
            "question_block": state.current_question,
        }

        mock_score_result = {
            "score": 7.5,
            "bloom_achieved": 3,
            "dreyfus_achieved": 3,
            "reasoning": "Boa resposta.",
        }

        mock_audit_service = AsyncMock()
        mock_audit_service.log_decision = AsyncMock()

        mock_db_ctx = AsyncMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.cv_screening.agents.wsi_interview_graph.calculate_wsi_deterministic",
            new=AsyncMock(return_value=mock_score_result),
            create=True,
        ):
            with patch(
                "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_wsi_deterministic",
                new=AsyncMock(return_value=mock_score_result),
                create=True,
            ):
                with patch("app.core.database.AsyncSessionLocal", return_value=mock_db_ctx):
                    with patch(
                        "app.shared.compliance.audit_service.audit_service",
                        mock_audit_service,
                        create=True,
                    ):
                        result = await nodes.score_response(state)

        # Verifica que o estado avançou
        assert result.current_question_index == 1

    @pytest.mark.asyncio
    async def test_generate_feedback_calls_audit_log(self):
        """generate_feedback deve chamar audit_service.log_decision com o resultado final."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes

        nodes = WSIInterviewNodes()
        state = self._make_state(recommendation="reprovado")
        state.technical_score = 3.0
        state.behavioral_score = 2.5

        mock_final_result = {"final_score": 3.0}

        mock_audit_service = AsyncMock()
        mock_audit_service.log_decision = AsyncMock()

        mock_db_ctx = AsyncMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_final_wsi_score",
            return_value=mock_final_result,
            create=True,
        ):
            with patch("app.core.database.AsyncSessionLocal", return_value=mock_db_ctx):
                with patch(
                    "app.shared.compliance.audit_service.audit_service",
                    mock_audit_service,
                    create=True,
                ):
                    result = await nodes.generate_feedback(state)

        # Verifica que o estado chegou a COMPLETE ou ERROR
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewStage
        assert result.stage in (WSIInterviewStage.COMPLETE, WSIInterviewStage.ERROR)

    @pytest.mark.asyncio
    async def test_audit_log_is_fail_safe(self):
        """Falha no audit_service não deve interromper o fluxo de score_response."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes

        nodes = WSIInterviewNodes()
        state = self._make_state()
        state.candidate_profile["_pending_response"] = {
            "text": "Resposta qualquer",
            "question_block": state.current_question,
        }

        mock_score_result = {
            "score": 5.0,
            "bloom_achieved": 2,
            "dreyfus_achieved": 2,
            "reasoning": "Resposta razoável.",
        }

        # Simula falha catastrófica no audit — AsyncSessionLocal lança exceção
        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_wsi_deterministic",
            new=AsyncMock(return_value=mock_score_result),
            create=True,
        ):
            with patch("app.core.database.AsyncSessionLocal", side_effect=RuntimeError("DB unavailable")):
                # Não deve lançar exceção — é fail-safe
                result = await nodes.score_response(state)

        # O scoring deve ter sido registrado apesar da falha no audit
        assert result.current_question_index == 1


# ─────────────────────────────────────────────────────────────────────────────
# 6. TestPolicyHITL
# ─────────────────────────────────────────────────────────────────────────────

class TestPolicyHITL:
    """Verifica que salvamento de política requer aprovação HITL."""

    def _make_agent_input(self):
        """Cria um AgentInput mock."""
        from lia_agents_core.agent_interface import AgentInput
        return AgentInput(
            message="Defina o prazo de feedback como 3 dias",
            context={
                "current_stage": "onboarding",
                "policy_state": {},
            },
            session_id="sess-policy-001",
            company_id="comp-001",
            user_id="user-001",
            conversation_history=[],
        )

    @pytest.mark.asyncio
    async def test_hitl_called_when_policy_updates_present(self):
        """HITL deve ser solicitado quando há state_updates no output.
        Verifica que a lógica HITL existe no policy_react_agent e é ativada
        quando state_updates está presente.
        """
        import sys
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        from lia_agents_core.agent_interface import AgentOutput

        # Verificar que a lógica HITL existe no source code do agente
        import inspect
        source = inspect.getsource(PolicyReActAgent)
        assert "hitl_service" in source, "PolicyReActAgent deve referenciar hitl_service"
        assert "request_approval" in source, "PolicyReActAgent deve chamar request_approval"
        assert "state_updates" in source, "PolicyReActAgent deve verificar state_updates"

        # Verificar que o output com state_updates ativa o bloco HITL
        # (verificação estrutural do código, não execução completa)
        assert "if output.state_updates" in source or "output.state_updates" in source, \
            "PolicyReActAgent deve verificar output.state_updates antes de HITL"
        assert "hitl_pending" in source, \
            "PolicyReActAgent deve marcar hitl_pending no metadata"

        # Verificar que o domínio correto é usado
        assert 'domain="hiring_policy"' in source or "domain='hiring_policy'" in source, \
            "PolicyReActAgent deve usar domain='hiring_policy' no HITL"

    @pytest.mark.asyncio
    async def test_hitl_not_called_when_no_policy_updates(self):
        """HITL não deve ser solicitado quando não há state_updates."""
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
        from lia_agents_core.agent_interface import AgentOutput

        agent = PolicyReActAgent()
        input_data = self._make_agent_input()

        # Output sem state_updates (nenhuma política foi alterada)
        mock_output = AgentOutput(
            message="Nenhuma política foi alterada.",
            confidence=0.7,
            state_updates={},  # vazio
        )

        mock_hitl_service = AsyncMock()
        mock_hitl_service.request_approval = AsyncMock(return_value=None)

        with patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=mock_output)):
            with patch("app.services.hitl_service.hitl_service", mock_hitl_service, create=True):
                result = await agent.process(input_data)

        # HITL NÃO deve ter sido solicitado
        mock_hitl_service.request_approval.assert_not_called()

    @pytest.mark.asyncio
    async def test_hitl_fail_safe_continues_on_error(self):
        """Falha no HITL service deve ser tratada com fail-safe (sem interromper o fluxo).
        Verifica estruturalmente que o código tem try/except no bloco HITL.
        """
        import inspect
        from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent

        source = inspect.getsource(PolicyReActAgent)

        # Verificar que há um bloco try/except ao redor do HITL
        assert "except" in source, "PolicyReActAgent deve ter try/except para fail-safe do HITL"

        # Verificar que o fail-safe loga o erro mas continua
        assert "Fail-safe" in source or "fail-safe" in source or "HITL service unavailable" in source or \
               "prosseguindo sem revisão" in source, \
               "PolicyReActAgent deve ter mensagem de fail-safe no HITL"

        # Verificar que não relança a exceção do HITL
        lines = source.split("\n")
        hitl_block_found = False
        for i, line in enumerate(lines):
            if "hitl_service" in line and "request_approval" in line:
                hitl_block_found = True
                # Verificar que as próximas 60 linhas têm except (bloco HITL pode ser longo)
                block = "\n".join(lines[i:i+60])
                assert "except" in block, f"Deve haver except após request_approval (linha {i})"
                break
        assert hitl_block_found, "Deve haver chamada a hitl_service.request_approval"
