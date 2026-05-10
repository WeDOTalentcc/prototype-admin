"""
COMP-8: Pipeline Bypass Gate 1 para candidatos web/ATS
COMP-9: LLM feedback diferenciado por Gate
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBypassGate1:
    """COMP-8: Bypass Gate 1 para candidatos de inscrição web/ATS."""

    @pytest.mark.asyncio
    async def test_web_source_bypasses_hitl_on_first_stage(self):
        """Candidatos com source=web na primeira etapa não devem acionar HITL."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        from lia_agents_core.agent_interface import AgentInput

        agent = PipelineTransitionAgent()
        inp = AgentInput(
            message="Mover candidato para triagem",
            context={
                "action_behavior": "active",
                "source": "web",              # COMP-8: fonte web
                "from_stage": "aplicado",     # primeira etapa
                "to_stage": "triagem",
                "candidate_id": "cand-web-001",
                "candidate_name": "Maria Web",
                "job_title": "Dev Backend",
            },
            session_id="sess-bypass-001",
            company_id="co-bypass",
            user_id="user-bypass",
            conversation_history=[],
        )

        expected = MagicMock(
            message="Candidato movido", confidence=0.85, metadata={},
            actions=[], navigation=None, state_updates={}, error=None
        )

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
             patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected)), \
             patch("app.domains.cv_screening.services.hitl_service.hitl_service") as MockHITL:

            clean = MagicMock(is_blocked=False, soft_warnings=[])
            MockFG.return_value.check.return_value = clean
            MockFG.return_value.check_implicit_bias.return_value = []
            MockHITL.request_approval = AsyncMock()

            result = await agent.process(inp)

        # HITL NÃO deve ter sido chamado para source=web + from_stage=aplicado
        MockHITL.request_approval.assert_not_called()
        assert result is not None

    @pytest.mark.asyncio
    async def test_ats_source_bypasses_hitl(self):
        """Candidatos com source=ats também devem ter bypass Gate 1."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        from lia_agents_core.agent_interface import AgentInput

        agent = PipelineTransitionAgent()
        inp = AgentInput(
            message="Mover candidato ATS para triagem",
            context={
                "action_behavior": "active",
                "source": "gupy",             # ATS externo
                "from_stage": "inscrito",
                "to_stage": "triagem",
                "candidate_id": "cand-gupy-001",
            },
            session_id="sess-bypass-002",
            company_id="co-bypass",
            user_id="user-bypass",
            conversation_history=[],
        )

        expected = MagicMock(
            message="Ok", confidence=0.8, metadata={},
            actions=[], navigation=None, state_updates={}, error=None
        )

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
             patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected)), \
             patch("app.domains.cv_screening.services.hitl_service.hitl_service") as MockHITL:

            clean = MagicMock(is_blocked=False, soft_warnings=[])
            MockFG.return_value.check.return_value = clean
            MockFG.return_value.check_implicit_bias.return_value = []
            MockHITL.request_approval = AsyncMock()

            result = await agent.process(inp)

        MockHITL.request_approval.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_source_still_triggers_hitl(self):
        """Sem source= HITL deve ser acionado normalmente."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        from lia_agents_core.agent_interface import AgentInput

        agent = PipelineTransitionAgent()
        inp = AgentInput(
            message="Mover candidato para entrevista",
            context={
                "action_behavior": "active",
                # sem source= → HITL normal
                "from_stage": "triagem",
                "to_stage": "entrevista",
                "candidate_id": "cand-hitl-001",
                "candidate_name": "Carlos Normal",
            },
            session_id="sess-hitl-001",
            company_id="co-hitl",
            user_id="user-hitl",
            conversation_history=[],
        )

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
             patch("app.domains.cv_screening.services.hitl_service.hitl_service") as MockHITL, \
             patch("app.shared.compliance.audit_service.audit_service") as MockAudit:

            clean = MagicMock(is_blocked=False, soft_warnings=[])
            MockFG.return_value.check.return_value = clean
            MockFG.return_value.check_implicit_bias.return_value = []
            MockHITL.request_approval = AsyncMock(return_value="pending-hitl-123")
            MockHITL.store_resume_info = AsyncMock()
            MockAudit.log_decision = AsyncMock(return_value=MagicMock())

            result = await agent.process(inp)

        # HITL DEVE ter sido chamado para transição normal
        MockHITL.request_approval.assert_called_once()

    def test_bypass_source_list_covers_major_ats(self):
        """Lista de sources bypass deve cobrir principais ATS."""
        import inspect
        from app.domains.pipeline.agents import pipeline_transition_agent as mod
        src = inspect.getsource(mod.PipelineTransitionAgent.process)
        # Verificar que principais ATS estão na lista
        assert "gupy" in src or "ats" in src
        assert "web" in src


class TestGateFeedback:
    """COMP-9: LLM feedback diferenciado por Gate."""

    def test_feedback_tool_exists(self):
        """Módulo pipeline_feedback_tool deve existir."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import send_gate_feedback
        import asyncio
        assert asyncio.iscoroutinefunction(send_gate_feedback)

    def test_remove_score_references(self):
        """_remove_score_references deve remover scores numéricos."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import _remove_score_references
        text = "Você obteve score de 75 pontos e nota 8.5 no processo."
        cleaned = _remove_score_references(text)
        assert "75" not in cleaned or "pontos" not in cleaned

    def test_ensure_review_link_adds_link(self):
        """_ensure_review_link deve adicionar link se ausente."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import (
            _ensure_review_link, HUMAN_REVIEW_LINK
        )
        text = "Infelizmente não podemos prosseguir."
        result = _ensure_review_link(text)
        assert HUMAN_REVIEW_LINK in result

    def test_ensure_review_link_not_duplicate(self):
        """_ensure_review_link não deve duplicar link se já presente."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import (
            _ensure_review_link, HUMAN_REVIEW_LINK
        )
        text = f"Acesse: {HUMAN_REVIEW_LINK} para revisão."
        result = _ensure_review_link(text)
        assert result.count(HUMAN_REVIEW_LINK) == 1

    def test_fallback_gate1_returns_string(self):
        """Fallback Gate 1 deve retornar string não vazia."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import _get_safe_fallback_feedback
        result = _get_safe_fallback_feedback(1, "João", "Dev Senior")
        assert isinstance(result, str)
        assert len(result) > 50
        assert "João" in result

    def test_fallback_gate2_includes_review_link(self):
        """Fallback Gate 2 deve incluir link de revisão humana (LGPD Art. 20)."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import (
            _get_safe_fallback_feedback, HUMAN_REVIEW_LINK
        )
        result = _get_safe_fallback_feedback(2, "Maria", "Dev Backend")
        assert HUMAN_REVIEW_LINK in result

    @pytest.mark.asyncio
    async def test_send_gate_feedback_returns_dict_on_llm_failure(self):
        """send_gate_feedback deve retornar dict mesmo com falha no LLM."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import send_gate_feedback

        # llm_service é importado lazy, patch no módulo de origem
        with patch("app.services.llm.llm_service") as MockLLM:
            MockLLM.claude.side_effect = Exception("LLM unavailable")
            result = await send_gate_feedback(
                gate_number=1,
                candidate_id="cand-001",
                company_id="co-001",
                candidate_name="Test",
                job_title="Dev",
            )

            assert isinstance(result, dict)
            assert "feedback_text" in result
            assert "gate_number" in result

    def test_gate1_prompt_constructive_tone(self):
        """Prompt Gate 1 deve ter tom construtivo."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import _build_gate1_prompt
        prompt = _build_gate1_prompt("João", {"strengths": ["Python"], "gaps": []}, "Dev", "triagem")
        assert "construtiv" in prompt.lower() or "positiv" in prompt.lower() or "encorajad" in prompt.lower()

    def test_gate2_prompt_includes_review_link(self):
        """Prompt Gate 2 deve referenciar link de revisão humana."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import (
            _build_gate2_prompt, HUMAN_REVIEW_LINK
        )
        prompt = _build_gate2_prompt("Maria", {"recommendation_level": "potential"}, "Dev", "triagem")
        assert HUMAN_REVIEW_LINK in prompt

    def test_human_review_link_is_wedotalent_domain(self):
        """Link de revisão humana deve ser domínio wedotalent."""
        from app.domains.pipeline.agents.pipeline_feedback_tool import HUMAN_REVIEW_LINK
        assert "wedotalent" in HUMAN_REVIEW_LINK
