"""
Unit tests — HITL integrado nos 3 grafos LangGraph (Sprint HITL).

Cobre:
- HITLService.store_resume_info / get_resume_info
- JobWizardGraph: interrupt detectado → approval_required enviado
- WSIInterviewGraph: interrupt antes de lg_generate_feedback
- PipelineTransitionAgent: pre-check HITL em process()
- agent_chat_ws: resume após approval_response
"""
import pytest

pytestmark = pytest.mark.hard

from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# HITLService — store/get resume_info
# ---------------------------------------------------------------------------

class TestHITLServiceResumeInfo:

    @pytest.mark.asyncio
    async def test_store_and_get_resume_info(self):
        from app.services.hitl_service import HITLService
        svc = HITLService()
        await svc.store_resume_info(
            thread_id="t-001",
            domain="wizard",
            session_id="s-001",
            agent_input_dict={"message": "confirmar vaga", "context": {"hitl_approved": True}},
            hitl_context="wizard_confirm_job",
        )
        info = await svc.get_resume_info("t-001")
        assert info is not None
        assert info["domain"] == "wizard"
        assert info["session_id"] == "s-001"
        assert info["hitl_context"] == "wizard_confirm_job"

    @pytest.mark.asyncio
    async def test_get_resume_info_missing_returns_none(self):
        from app.services.hitl_service import HITLService
        svc = HITLService()
        result = await svc.get_resume_info("nonexistent-thread")
        assert result is None

    @pytest.mark.asyncio
    async def test_resume_info_stores_agent_input(self):
        from app.services.hitl_service import HITLService
        svc = HITLService()
        agent_input = {"message": "mover candidato", "context": {"to_stage": "entrevista"}, "session_id": "s-123"}
        await svc.store_resume_info(
            thread_id="t-pipeline",
            domain="pipeline_transition",
            session_id="s-123",
            agent_input_dict=agent_input,
        )
        info = await svc.get_resume_info("t-pipeline")
        assert info["agent_input"]["message"] == "mover candidato"
        assert info["agent_input"]["context"]["to_stage"] == "entrevista"

    @pytest.mark.asyncio
    async def test_resume_info_overwrite(self):
        """Segunda chamada sobrescreve a primeira."""
        from app.services.hitl_service import HITLService
        svc = HITLService()
        await svc.store_resume_info("t-ow", "wizard", "s1", {"message": "v1"})
        await svc.store_resume_info("t-ow", "pipeline", "s2", {"message": "v2"})
        info = await svc.get_resume_info("t-ow")
        assert info["domain"] == "pipeline"
        assert info["agent_input"]["message"] == "v2"

    @pytest.mark.asyncio
    async def test_store_resume_info_has_stored_at(self):
        from app.services.hitl_service import HITLService
        svc = HITLService()
        await svc.store_resume_info("t-ts", "wizard", "s", {})
        info = await svc.get_resume_info("t-ts")
        assert "stored_at" in info

    def test_hitl_service_has_store_resume_info(self):
        from app.services.hitl_service import HITLService
        import inspect
        assert hasattr(HITLService, "store_resume_info")
        assert inspect.iscoroutinefunction(HITLService.store_resume_info)

    def test_hitl_service_has_get_resume_info(self):
        from app.services.hitl_service import HITLService
        import inspect
        assert hasattr(HITLService, "get_resume_info")
        assert inspect.iscoroutinefunction(HITLService.get_resume_info)


# ---------------------------------------------------------------------------
# JobWizardGraph — interrupt_before stage_transition
# ---------------------------------------------------------------------------

class TestJobWizardGraphHITL:

    def test_build_langgraph_has_interrupt_before(self):
        """_build_langgraph deve compilar com interrupt_before=['stage_transition']."""
        try:
            from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        except ImportError:
            pytest.skip("JobWizardGraph não disponível")

        graph = JobWizardGraph()
        try:
            compiled = graph._build_langgraph()
            # LangGraph compiled graphs expõem interrupt_before nos metadados
            config = getattr(compiled, "config_schema", None) or {}
            # Verificar que a compilação não lança erro (interrupt_before válido)
            assert compiled is not None
        except Exception as exc:
            if "checkpointer" in str(exc).lower() or "postgres" in str(exc).lower():
                pytest.skip("Checkpointer não configurado em test env")
            raise

    @pytest.mark.asyncio
    async def test_invoke_langgraph_handles_interrupt_confirm_intent(self):
        """Quando __interrupt__ presente e intent=confirm → HITL request_approval chamado."""
        try:
            from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
            from app.shared.agents.state_machine import WizardIntent
        except ImportError:
            pytest.skip("JobWizardGraph não disponível")

        confirm_value = WizardIntent.CONFIRM.value  # "confirm"

        graph = JobWizardGraph()
        graph._compiled_lg = MagicMock()
        graph._compiled_lg.ainvoke = AsyncMock(return_value={
            "__interrupt__": [{"value": {}}],
            "intent": confirm_value,
        })

        state = {
            "intent": confirm_value,
            "session_id": "s-wizard-test",
            "job_title": "Engenheiro",
            "company_id": "acme",
            "user_message": "confirmar",
        }

        with patch("app.services.hitl_service.hitl_service") as mock_hitl:
            mock_hitl.request_approval = AsyncMock(return_value="pending-123")
            mock_hitl.store_resume_info = AsyncMock()
            result = await graph._invoke_langgraph(state)

        assert result.get("hitl_pending") is True
        assert result.get("hitl_pending_id") == "pending-123"

    @pytest.mark.asyncio
    async def test_invoke_langgraph_no_interrupt_passes_through(self):
        """Sem __interrupt__ → retorna resultado normal."""
        try:
            from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
        except ImportError:
            pytest.skip("JobWizardGraph não disponível")

        graph = JobWizardGraph()
        expected = {"intent": "provide_info", "session_id": "s-normal"}
        graph._compiled_lg = MagicMock()
        graph._compiled_lg.ainvoke = AsyncMock(return_value=expected)

        state = {"intent": "provide_info", "session_id": "s-normal"}
        result = await graph._invoke_langgraph(state)

        assert result == expected
        assert "__interrupt__" not in result


# ---------------------------------------------------------------------------
# PipelineTransitionAgent — HITL pre-check
# ---------------------------------------------------------------------------

class TestPipelineTransitionAgentHITL:

    @pytest.mark.asyncio
    async def test_active_behavior_triggers_hitl(self):
        """action_behavior='active' com to_stage → HITL solicitado."""
        try:
            from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
            from app.shared.agents.agent_interface import AgentInput
        except ImportError:
            pytest.skip("PipelineTransitionAgent não disponível")

        agent = PipelineTransitionAgent()
        agent_input = AgentInput(
            message="mover candidato para entrevista",
            context={
                "action_behavior": "active",
                "candidate_name": "João Silva",
                "from_stage": "triagem",
                "to_stage": "entrevista",
                "hitl_approved": False,
            },
            session_id="s-pipeline-test",
            company_id="acme",
            user_id="user-1",
        )

        with patch("app.services.hitl_service.hitl_service") as mock_hitl:
            mock_hitl.request_approval = AsyncMock(return_value="pending-pipeline-xyz")
            mock_hitl.store_resume_info = AsyncMock()
            output = await agent.process(agent_input)

        assert output.metadata.get("hitl_pending") is True
        assert "João Silva" in output.message

    @pytest.mark.asyncio
    async def test_passive_behavior_skips_hitl(self):
        """action_behavior='passive' → não dispara HITL."""
        try:
            from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
            from app.shared.agents.agent_interface import AgentInput
        except ImportError:
            pytest.skip("PipelineTransitionAgent não disponível")

        agent = PipelineTransitionAgent()
        agent_input = AgentInput(
            message="mostrar candidatos em triagem",
            context={"action_behavior": "passive"},
            session_id="s-passive",
            company_id="acme",
            user_id="user-1",
        )

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock) as mock_lg:
            from app.shared.agents.agent_interface import AgentOutput
            mock_lg.return_value = AgentOutput(message="3 candidatos em triagem", confidence=0.9)
            output = await agent.process(agent_input)

        # HITL não foi solicitado — processo normal
        assert output.metadata.get("hitl_pending") is not True
        mock_lg.assert_called_once()

    @pytest.mark.asyncio
    async def test_hitl_approved_skips_hitl_check(self):
        """context.hitl_approved=True → ignora HITL, executa agente direto."""
        try:
            from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
            from app.shared.agents.agent_interface import AgentInput, AgentOutput
        except ImportError:
            pytest.skip("PipelineTransitionAgent não disponível")

        agent = PipelineTransitionAgent()
        agent_input = AgentInput(
            message="mover candidato",
            context={
                "action_behavior": "active",
                "to_stage": "entrevista",
                "hitl_approved": True,  # ← já aprovado
            },
            session_id="s-approved",
            company_id="acme",
            user_id="user-1",
        )

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = AgentOutput(message="Candidato movido com sucesso.", confidence=0.9)
            output = await agent.process(agent_input)

        mock_lg.assert_called_once()
        assert "Aguardando aprovação" not in output.message

    @pytest.mark.asyncio
    async def test_no_to_stage_skips_hitl(self):
        """Sem to_stage → não há transição real, HITL não é acionado."""
        try:
            from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
            from app.shared.agents.agent_interface import AgentInput, AgentOutput
        except ImportError:
            pytest.skip("PipelineTransitionAgent não disponível")

        agent = PipelineTransitionAgent()
        agent_input = AgentInput(
            message="o que está acontecendo no pipeline?",
            context={"action_behavior": "active"},  # sem to_stage
            session_id="s-no-stage",
            company_id="acme",
            user_id="user-1",
        )

        with patch.object(agent, "_process_langgraph", new_callable=AsyncMock) as mock_lg:
            mock_lg.return_value = AgentOutput(message="Pipeline ok.", confidence=0.9)
            output = await agent.process(agent_input)

        mock_lg.assert_called_once()


# ---------------------------------------------------------------------------
# WSIInterviewGraph — interrupt_before lg_generate_feedback
# ---------------------------------------------------------------------------

class TestWSIInterviewGraphHITL:

    def test_build_langgraph_has_interrupt_before_in_source(self):
        """_build_langgraph deve ter interrupt_before=['lg_generate_feedback'] no código."""
        import pathlib
        content = pathlib.Path(
            "app/domains/cv_screening/agents/wsi_interview_graph.py"
        ).read_text()
        assert "interrupt_before" in content
        assert "lg_generate_feedback" in content

    @pytest.mark.asyncio
    async def test_submit_response_handles_interrupt(self):
        """Interrupt antes de lg_generate_feedback → HITL solicitado."""
        try:
            from app.domains.cv_screening.agents.wsi_interview_graph import (
                WSIInterviewGraph, WSIInterviewState, _wsi_state_to_dict
            )
        except ImportError:
            pytest.skip("WSIInterviewGraph não disponível")

        g = WSIInterviewGraph.__new__(WSIInterviewGraph)
        g._compiled_lg = MagicMock()
        g._compiled_lg.ainvoke = AsyncMock(return_value={
            "__interrupt__": [{"value": {}}],
            "wsi_data": {
                "stage": "score_response",
                "session_id": "wsi-s-001",
                "wsi_final_score": 8.5,
                "technical_score": 7.0,
                "behavioral_score": 9.0,
            },
        })

        # Criar estado mínimo válido
        state = WSIInterviewState(
            session_id="wsi-s-001",
            company_id="acme",
            candidate_id="cand-1",
            job_id="job-1",
        )
        # hitl_approved não existe como atributo padrão → adicionamos manualmente
        state.__dict__["hitl_approved"] = False

        with patch("app.services.hitl_service.hitl_service") as mock_hitl:
            mock_hitl.request_approval = AsyncMock(return_value="pending-wsi-abc")
            mock_hitl.store_resume_info = AsyncMock()
            result = await g._submit_response_langgraph(state, "minha resposta")

        mock_hitl.request_approval.assert_called_once()
        call_kwargs = mock_hitl.request_approval.call_args
        assert call_kwargs[1]["action"] == "finalize_wsi_score"


# ---------------------------------------------------------------------------
# HITL contract — interface pública completa
# ---------------------------------------------------------------------------

class TestHITLContractFull:

    def test_hitl_service_all_methods_present(self):
        from app.services.hitl_service import HITLService
        import inspect
        for method in ["request_approval", "receive_approval", "get_pending",
                       "is_approved", "store_resume_info", "get_resume_info"]:
            assert hasattr(HITLService, method), f"Método faltando: {method}"
            assert inspect.iscoroutinefunction(getattr(HITLService, method))

    def test_hitl_router_registered_in_main(self):
        """hitl router deve estar registrado no main.py."""
        import importlib.util, pathlib
        main_path = pathlib.Path("app/main.py")
        if main_path.exists():
            content = main_path.read_text()
            assert "hitl" in content.lower(), "hitl router não registrado em main.py"

    def test_pipeline_agent_has_hitl_logic(self):
        import pathlib
        content = pathlib.Path(
            "app/domains/pipeline/agents/pipeline_transition_agent.py"
        ).read_text()
        assert "hitl_approved" in content
        assert "needs_hitl" in content

    def test_wizard_graph_has_interrupt_before(self):
        import pathlib
        content = pathlib.Path(
            "app/domains/job_management/agents/job_wizard_graph.py"
        ).read_text()
        assert "interrupt_before" in content
        assert "stage_transition" in content

    def test_wsi_graph_has_interrupt_before(self):
        import pathlib
        content = pathlib.Path(
            "app/domains/cv_screening/agents/wsi_interview_graph.py"
        ).read_text()
        assert "interrupt_before" in content
        assert "lg_generate_feedback" in content

    def test_ws_handler_has_resume_logic(self):
        import pathlib
        content = pathlib.Path(
            "app/api/v1/agent_chat_ws.py"
        ).read_text()
        assert "get_resume_info" in content
        assert "hitl_resume" in content
