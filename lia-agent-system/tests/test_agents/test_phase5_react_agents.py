"""
Testes para os 3 novos agentes ReAct da Fase 5:
- AnalyticsReActAgent
- CommunicationReActAgent
- ATSIntegrationReActAgent

Cobertura: importação, instanciação, tool registry, stage context, system prompt,
process com LangGraph mockado, erros de tool.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lia_agents_core.agent_interface import AgentInput, AgentOutput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_input(**kwargs) -> AgentInput:
    defaults = dict(
        message="teste",
        user_id="u1",
        company_id="comp-1",
        session_id="sess-1",
        context={},
    )
    defaults.update(kwargs)
    return AgentInput(**defaults)


# ===========================================================================
# ANALYTICS REACT AGENT
# ===========================================================================

class TestAnalyticsAgentStructure:
    def test_importable(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        assert AnalyticsReActAgent is not None

    def test_instantiates(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent()
        assert agent.domain_name == "analytics"

    def test_has_expected_tools(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent()
        expected = {
            "get_job_insights",
            "predict_hiring_metrics",
            "generate_job_report",
            "generate_candidate_report",
            "get_search_analytics",
            "get_agent_performance",
        }
        assert expected.issubset(set(agent.available_tools))


class TestAnalyticsToolRegistry:
    def test_get_analytics_tools_returns_six(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        tools = get_analytics_tools()
        assert len(tools) == 6

    def test_all_tools_callable(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        for tool in get_analytics_tools():
            assert callable(tool.function), f"Tool '{tool.name}' not callable"

    def test_tool_names_unique(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        names = [t.name for t in get_analytics_tools()]
        assert len(names) == len(set(names))

    def test_get_stage_tools_query_understanding(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_stage_tools
        tools = get_stage_tools("query-understanding")
        assert len(tools) > 0

    def test_get_stage_tools_data_retrieval(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_stage_tools
        tools = get_stage_tools("data-retrieval")
        names = {t.name for t in tools}
        assert "predict_hiring_metrics" in names or "generate_job_report" in names


class TestAnalyticsStageContext:
    def test_all_stages_defined(self):
        from app.domains.analytics.agents.analytics_stage_context import STAGE_DEFINITIONS
        assert "query-understanding" in STAGE_DEFINITIONS
        assert "data-retrieval" in STAGE_DEFINITIONS
        assert "synthesis" in STAGE_DEFINITIONS

    def test_get_stage_context_returns_dict(self):
        from app.domains.analytics.agents.analytics_stage_context import get_stage_context
        ctx = get_stage_context("data-retrieval")
        assert "description" in ctx
        assert "tools" in ctx

    def test_get_stage_tools_returns_list(self):
        from app.domains.analytics.agents.analytics_stage_context import get_stage_tools
        tools = get_stage_tools("synthesis")
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_get_transition_prompt_returns_string(self):
        from app.domains.analytics.agents.analytics_stage_context import get_transition_prompt
        prompt = get_transition_prompt("query-understanding", "data-retrieval")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestAnalyticsSystemPrompt:
    def test_returns_string(self):
        from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
        prompt = get_analytics_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_contains_lia_reference(self):
        from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
        prompt = get_analytics_system_prompt().lower()
        assert "lia" in prompt or "analytics" in prompt or "análise" in prompt


class TestAnalyticsAgentProcess:
    @pytest.mark.asyncio
    async def test_process_langgraph_error_returns_graceful(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent()

        with patch.object(agent, "_process_langgraph", AsyncMock(side_effect=Exception("LLM fail"))):
            result = await agent.process(make_input(message="gerar relatório"))

        assert isinstance(result, AgentOutput)
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_process_langgraph_path(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent()

        mock_output = AgentOutput(message="Relatório gerado.", confidence=0.88)
        with patch.object(agent, "_process_langgraph", AsyncMock(return_value=mock_output)):
            result = await agent.process(make_input(message="top KPIs"))

        assert result.message == "Relatório gerado."
        assert result.confidence == 0.88


# ===========================================================================
# COMMUNICATION REACT AGENT
# ===========================================================================

class TestCommunicationAgentStructure:
    def test_importable(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        assert CommunicationReActAgent is not None

    def test_instantiates(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent()
        assert agent.domain_name == "communication"

    def test_has_expected_tools(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent()
        expected = {
            "send_email",
            "send_whatsapp",
            "get_communication_history",
            "schedule_message",
            "check_rate_limit",
        }
        assert expected.issubset(set(agent.available_tools))


class TestCommunicationToolRegistry:
    def test_get_communication_tools_returns_five(self):
        from app.domains.communication.agents.communication_tool_registry import get_communication_tools
        tools = get_communication_tools()
        assert len(tools) == 5

    def test_all_tools_callable(self):
        from app.domains.communication.agents.communication_tool_registry import get_communication_tools
        for tool in get_communication_tools():
            assert callable(tool.function), f"Tool '{tool.name}' not callable"

    def test_tool_names_unique(self):
        from app.domains.communication.agents.communication_tool_registry import get_communication_tools
        names = [t.name for t in get_communication_tools()]
        assert len(names) == len(set(names))

    def test_get_stage_tools_intent_detection(self):
        from app.domains.communication.agents.communication_tool_registry import get_stage_tools
        tools = get_stage_tools("intent-detection")
        assert len(tools) > 0

    def test_get_stage_tools_delivery(self):
        from app.domains.communication.agents.communication_tool_registry import get_stage_tools
        tools = get_stage_tools("delivery")
        names = {t.name for t in tools}
        assert "send_email" in names or "send_whatsapp" in names


class TestCommunicationStageContext:
    def test_all_stages_defined(self):
        from app.domains.communication.agents.communication_stage_context import STAGE_DEFINITIONS
        assert "intent-detection" in STAGE_DEFINITIONS
        assert "content-preparation" in STAGE_DEFINITIONS
        assert "delivery" in STAGE_DEFINITIONS

    def test_get_stage_context_returns_dict(self):
        from app.domains.communication.agents.communication_stage_context import get_stage_context
        ctx = get_stage_context("delivery")
        assert "description" in ctx
        assert "tools" in ctx

    def test_get_stage_tools_returns_list(self):
        from app.domains.communication.agents.communication_stage_context import get_stage_tools
        tools = get_stage_tools("delivery")
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_get_transition_prompt_returns_string(self):
        from app.domains.communication.agents.communication_stage_context import get_transition_prompt
        prompt = get_transition_prompt("intent-detection", "content-preparation")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestCommunicationSystemPrompt:
    def test_returns_string(self):
        from app.domains.communication.agents.communication_system_prompt import get_communication_system_prompt
        prompt = get_communication_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_contains_communication_reference(self):
        from app.domains.communication.agents.communication_system_prompt import get_communication_system_prompt
        prompt = get_communication_system_prompt().lower()
        assert "comunicação" in prompt or "email" in prompt or "whatsapp" in prompt


class TestCommunicationAgentProcess:
    @pytest.mark.asyncio
    async def test_process_error_returns_graceful(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent()

        with patch.object(agent, "_process_langgraph", AsyncMock(side_effect=Exception("timeout"))):
            result = await agent.process(make_input(message="enviar email"))

        assert isinstance(result, AgentOutput)
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_process_langgraph_path(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent()

        mock_output = AgentOutput(message="Email enviado.", confidence=0.90)
        with patch.object(agent, "_process_langgraph", AsyncMock(return_value=mock_output)):
            result = await agent.process(make_input(message="enviar email para candidato"))

        assert result.message == "Email enviado."


# ===========================================================================
# ATS INTEGRATION REACT AGENT
# ===========================================================================

class TestATSIntegrationAgentStructure:
    def test_importable(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        assert ATSIntegrationReActAgent is not None

    def test_instantiates(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()
        assert agent.domain_name == "ats_integration"

    def test_has_expected_tools(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()
        expected = {
            "sync_candidate_to_ats",
            "fetch_candidate_from_ats",
            "validate_ats_fields",
            "bulk_sync_candidates",
            "get_sync_status",
        }
        assert expected.issubset(set(agent.available_tools))


class TestATSIntegrationToolRegistry:
    def test_get_ats_tools_returns_five(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        tools = get_ats_integration_tools()
        assert len(tools) == 5

    def test_all_tools_callable(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        for tool in get_ats_integration_tools():
            assert callable(tool.function), f"Tool '{tool.name}' not callable"

    def test_tool_names_unique(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        names = [t.name for t in get_ats_integration_tools()]
        assert len(names) == len(set(names))

    def test_get_stage_tools_provider_detection(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_stage_tools
        tools = get_stage_tools("provider-detection")
        assert len(tools) > 0

    def test_get_stage_tools_sync_execution(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_stage_tools
        tools = get_stage_tools("sync-execution")
        names = {t.name for t in tools}
        assert "sync_candidate_to_ats" in names or "bulk_sync_candidates" in names


class TestATSIntegrationStageContext:
    def test_all_stages_defined(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import STAGE_DEFINITIONS
        assert "provider-detection" in STAGE_DEFINITIONS
        assert "field-mapping" in STAGE_DEFINITIONS
        assert "sync-execution" in STAGE_DEFINITIONS

    def test_get_stage_context_returns_dict(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import get_stage_context
        ctx = get_stage_context("sync-execution")
        assert "description" in ctx
        assert "tools" in ctx

    def test_get_stage_tools_returns_list(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import get_stage_tools
        tools = get_stage_tools("sync-execution")
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_get_transition_prompt_returns_string(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import get_transition_prompt
        prompt = get_transition_prompt("field-mapping", "sync-execution")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestATSIntegrationSystemPrompt:
    def test_returns_string(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import get_ats_integration_system_prompt
        prompt = get_ats_integration_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    def test_contains_ats_reference(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import get_ats_integration_system_prompt
        prompt = get_ats_integration_system_prompt().lower()
        assert "ats" in prompt or "integração" in prompt or "sincronização" in prompt


class TestATSIntegrationAgentProcess:
    @pytest.mark.asyncio
    async def test_process_error_returns_graceful(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()

        with patch.object(agent, "_process_langgraph", AsyncMock(side_effect=Exception("ATS down"))):
            result = await agent.process(make_input(message="sincronizar com Gupy"))

        assert isinstance(result, AgentOutput)
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_process_langgraph_path(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()

        mock_output = AgentOutput(message="Candidato sincronizado.", confidence=0.85)
        with patch.object(agent, "_process_langgraph", AsyncMock(return_value=mock_output)):
            result = await agent.process(make_input(message="sync candidato 42 para Gupy"))

        assert result.message == "Candidato sincronizado."


# ===========================================================================
# Tool wrapper smoke tests (missing service → graceful error)
# ===========================================================================

class TestAnalyticsToolWrapperErrors:
    @pytest.mark.asyncio
    async def test_get_job_insights_service_error(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        tool = next(t for t in get_analytics_tools() if t.name == "get_job_insights")

        with patch("app.core.database.AsyncSessionLocal") as mock_db_cls:
            mock_db_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_db_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            # JobInsightsService not patched → will fail gracefully
            result = await tool.function(job_title="Python Dev", company_id="c1")

        assert isinstance(result, dict)
        # Either success or graceful error dict
        assert "success" in result

    @pytest.mark.asyncio
    async def test_check_rate_limit_service_error(self):
        from app.domains.communication.agents.communication_tool_registry import get_communication_tools
        tool = next(t for t in get_communication_tools() if t.name == "check_rate_limit")

        with patch("app.core.database.AsyncSessionLocal") as mock_db_cls:
            mock_db_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_db_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await tool.function(candidate_id=1, company_id="c1", channel="email")

        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_validate_ats_fields_missing_params(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        tool = next(t for t in get_ats_integration_tools() if t.name == "validate_ats_fields")

        with patch("app.core.database.AsyncSessionLocal") as mock_db_cls:
            mock_db_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_db_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await tool.function(candidate_data={}, company_id="c1", ats_provider="gupy")

        assert isinstance(result, dict)
        assert "success" in result
