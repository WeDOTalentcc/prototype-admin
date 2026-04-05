"""
Tests for IntentRouter (unit — no real LLM calls)
Target: intent_router.py (24% → ~70%)
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


def _make_router():
    from app.orchestrator.intent_router import IntentRouter
    mock_llm_service = MagicMock()
    mock_llm_service.claude = MagicMock()
    router = IntentRouter(llm_service=mock_llm_service)
    return router


class TestIntentToAgentTypeMapping:
    def setup_method(self):
        self.router = _make_router()

    def test_job_planner_intent(self):
        from app.agents.base_agent import AgentType
        agent_type = self.router.INTENT_TO_AGENT_TYPE.get("job_planner")
        assert agent_type == AgentType.JOB_PLANNER

    def test_sourcing_intent(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("sourcing") == AgentType.SOURCING

    def test_cv_screening_intent(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("cv_screening") == AgentType.CV_SCREENING

    def test_scheduling_intent(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("scheduling") == AgentType.SCHEDULING

    def test_ats_integrator_intent(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("ats_integrator") == AgentType.ATS_INTEGRATOR

    def test_wsi_evaluator_intent(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("wsi_evaluator") == AgentType.WSI_EVALUATOR

    def test_recruiter_assistant_intent(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("recruiter_assistant") == AgentType.RECRUITER_ASSISTANT

    def test_analyst_feedback_intent(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("analyst_feedback") == AgentType.ANALYST_FEEDBACK

    def test_general_query_maps_to_orchestrator(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("general_query") == AgentType.ORCHESTRATOR

    def test_pt_br_intents(self):
        from app.agents.base_agent import AgentType
        assert self.router.INTENT_TO_AGENT_TYPE.get("buscar_candidatos") == AgentType.SOURCING
        assert self.router.INTENT_TO_AGENT_TYPE.get("triagem_curricular") == AgentType.CV_SCREENING
        assert self.router.INTENT_TO_AGENT_TYPE.get("agendar_entrevista") == AgentType.SCHEDULING


class TestGetAgentTypeForIntent:
    def setup_method(self):
        self.router = _make_router()

    def test_known_intent_returns_correct_type(self):
        from app.agents.base_agent import AgentType
        result = self.router.get_agent_type_for_intent("sourcing")
        assert result == AgentType.SOURCING

    def test_unknown_intent_returns_orchestrator(self):
        from app.agents.base_agent import AgentType
        result = self.router.get_agent_type_for_intent("totally_unknown_xyz")
        assert result == AgentType.ORCHESTRATOR

    def test_create_job_intent(self):
        from app.agents.base_agent import AgentType
        result = self.router.get_agent_type_for_intent("create_job")
        assert result == AgentType.JOB_PLANNER

    def test_disparar_triagem(self):
        from app.agents.base_agent import AgentType
        result = self.router.get_agent_type_for_intent("disparar_triagem")
        assert result == AgentType.CV_SCREENING


class TestGetAgentName:
    def setup_method(self):
        self.router = _make_router()

    def test_known_type_returns_name(self):
        from app.agents.base_agent import AgentType
        name = self.router.get_agent_name(AgentType.SOURCING)
        assert isinstance(name, str)
        assert len(name) > 0

    def test_orchestrator_name(self):
        from app.agents.base_agent import AgentType
        name = self.router.get_agent_name(AgentType.ORCHESTRATOR)
        assert "Orchestrator" in name or "LIA" in name

    def test_unknown_type_returns_unknown(self):
        name = self.router.get_agent_name("completely_unknown_type")
        assert "Unknown" in name


class TestFallbackResponse:
    def setup_method(self):
        self.router = _make_router()

    def test_fallback_structure(self):
        result = self.router._fallback_response(context=None, reason="test")
        assert "intent" in result
        assert "target_agent" in result
        assert "agent_type" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "requires_planning" in result
        assert "entities" in result
        assert "model_used" in result

    def test_fallback_intent(self):
        result = self.router._fallback_response(context=None)
        assert result["intent"] == "recruiter_assistant"

    def test_fallback_low_confidence(self):
        result = self.router._fallback_response(context=None)
        assert result["confidence"] < 0.5

    def test_fallback_with_context(self):
        ctx = {"last_agent": "sourcing"}
        result = self.router._fallback_response(context=ctx)
        assert result["context"] == ctx

    def test_fallback_model_used_fallback(self):
        result = self.router._fallback_response(context=None, reason="cascade_exhausted")
        assert result["model_used"] == "fallback"


class TestRouteWithMockedCascade:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _make_router_with_cascade(self, content, confidence=0.9, model="haiku"):
        from app.orchestrator.intent_router import IntentRouter
        mock_llm_service = MagicMock()
        mock_llm_service.claude = MagicMock()

        cascade_result = MagicMock()
        cascade_result.content = content
        cascade_result.confidence = confidence
        cascade_result.model_used = model
        cascade_result.requires_human = False

        mock_llm_service.generate_with_cascade = AsyncMock(return_value=cascade_result)
        router = IntentRouter(llm_service=mock_llm_service)
        return router

    def test_route_sourcing_intent(self):
        import json
        content = json.dumps({
            "intent": "sourcing",
            "confidence": 0.95,
            "reasoning": "Busca de candidatos",
            "requires_planning": False,
            "entities": {},
        })
        router = self._make_router_with_cascade(content)
        result = self._run(router.route("Buscar candidatos Python sênior"))
        assert result["intent"] == "sourcing"
        assert result["confidence"] == 0.95

    def test_route_cascade_failure_returns_fallback(self):
        from app.orchestrator.intent_router import IntentRouter
        mock_llm_service = MagicMock()
        mock_llm_service.claude = MagicMock()
        mock_llm_service.generate_with_cascade = AsyncMock(side_effect=Exception("cascade failed"))
        router = IntentRouter(llm_service=mock_llm_service)
        result = self._run(router.route("Olá"))
        assert result["model_used"] == "fallback"

    def test_route_json_embedded_in_text(self):
        import json
        payload = {
            "intent": "scheduling",
            "confidence": 0.88,
            "reasoning": "Agendamento",
            "requires_planning": False,
            "entities": {},
        }
        content = f"Resultado: {json.dumps(payload)} fim."
        router = self._make_router_with_cascade(content)
        result = self._run(router.route("Agendar entrevista"))
        assert result["intent"] == "scheduling"

    def test_route_requires_human_returns_fallback(self):
        from app.orchestrator.intent_router import IntentRouter
        mock_llm_service = MagicMock()
        mock_llm_service.claude = MagicMock()
        cascade_result = MagicMock()
        cascade_result.requires_human = True
        cascade_result.content = ""
        mock_llm_service.generate_with_cascade = AsyncMock(return_value=cascade_result)
        router = IntentRouter(llm_service=mock_llm_service)
        result = self._run(router.route("mensagem complexa"))
        assert result["model_used"] == "fallback"
