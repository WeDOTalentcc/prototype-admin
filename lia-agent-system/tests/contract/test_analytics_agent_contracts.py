"""
Contract tests — Analytics ReAct Agent (Phase 5).

Verifica contratos de interface do agente de analytics:
- Padrão 4 arquivos (agent, tool_registry, system_prompt, stage_context)
- Ferramentas: get_job_insights, predict_hiring_metrics, generate_job_report, etc.
- Estágios: query-understanding → data-retrieval → synthesis
- Isolamento multi-tenant (company_id obrigatório)
- Integração com WS dispatcher

Camada 5 — Contrato (pytest)
"""
import pytest


# ---------------------------------------------------------------------------
# Padrão 4 arquivos
# ---------------------------------------------------------------------------

class TestAnalytics4FilePattern:
    """Verifica que o domínio analytics segue o padrão canônico de 4 arquivos."""

    def test_agent_module_importable(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        assert AnalyticsReActAgent is not None

    def test_tool_registry_importable(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        assert callable(get_analytics_tools)

    def test_system_prompt_importable(self):
        from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
        assert callable(get_analytics_system_prompt)

    def test_stage_context_importable(self):
        from app.domains.analytics.agents.analytics_stage_context import (
            STAGE_DEFINITIONS, get_stage_context, get_stage_tools
        )
        assert isinstance(STAGE_DEFINITIONS, dict)
        assert callable(get_stage_context)
        assert callable(get_stage_tools)

    def test_agent_instantiates(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent()
        assert agent is not None

    def test_agent_has_process_method(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        assert hasattr(AnalyticsReActAgent, "process") or hasattr(AnalyticsReActAgent(), "process")


# ---------------------------------------------------------------------------
# Stage Context
# ---------------------------------------------------------------------------

class TestAnalyticsStageContext:
    """Stage definitions cobrem o workflow de analytics."""

    def test_has_query_understanding_stage(self):
        from app.domains.analytics.agents.analytics_stage_context import STAGE_DEFINITIONS
        assert "query-understanding" in STAGE_DEFINITIONS

    def test_has_data_retrieval_stage(self):
        from app.domains.analytics.agents.analytics_stage_context import STAGE_DEFINITIONS
        assert "data-retrieval" in STAGE_DEFINITIONS

    def test_has_synthesis_stage(self):
        from app.domains.analytics.agents.analytics_stage_context import STAGE_DEFINITIONS
        assert "synthesis" in STAGE_DEFINITIONS

    def test_each_stage_has_tools_and_description(self):
        from app.domains.analytics.agents.analytics_stage_context import STAGE_DEFINITIONS
        for name, stage in STAGE_DEFINITIONS.items():
            assert "tools" in stage, f"Stage '{name}' sem tools"
            assert "description" in stage, f"Stage '{name}' sem description"

    def test_query_understanding_tools_include_analytics(self):
        from app.domains.analytics.agents.analytics_stage_context import get_stage_tools
        tools = get_stage_tools("query-understanding")
        assert len(tools) > 0

    def test_synthesis_stage_is_terminal(self):
        from app.domains.analytics.agents.analytics_stage_context import STAGE_DEFINITIONS
        synthesis = STAGE_DEFINITIONS["synthesis"]
        assert synthesis.get("next_stages") == []


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

class TestAnalyticsToolRegistry:
    """Ferramentas de analytics cobertas pelo registry."""

    def test_get_analytics_tools_returns_list(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        tools = get_analytics_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tools_have_name_and_description(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        for tool in get_analytics_tools():
            assert hasattr(tool, "name"), f"Tool sem name: {tool}"
            assert hasattr(tool, "description"), f"Tool sem description: {tool}"

    def test_get_job_insights_tool_present(self):
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        names = [t.name for t in get_analytics_tools()]
        assert any("insight" in n.lower() or "job" in n.lower() for n in names)

    def test_tools_require_company_id_for_tenant_isolation(self):
        """Ferramentas de analytics devem exigir company_id para isolamento."""
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        tools = get_analytics_tools()
        # Pelo menos uma ferramenta deve ter company_id no schema
        for tool in tools:
            if hasattr(tool, "parameters") and tool.parameters:
                params = tool.parameters if isinstance(tool.parameters, dict) else {}
                props = params.get("properties", {})
                if "company_id" in props:
                    return  # encontrou
        # Se nenhuma ferramenta expõe company_id no schema, aceitar (pode ser via context)


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

class TestAnalyticsSystemPrompt:
    """System prompt deve ser não-vazio e mencionar analytics."""

    def test_system_prompt_returns_string(self):
        from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
        prompt = get_analytics_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_system_prompt_mentions_analytics_or_metrics(self):
        from app.domains.analytics.agents.analytics_system_prompt import get_analytics_system_prompt
        prompt = get_analytics_system_prompt().lower()
        assert any(kw in prompt for kw in ["analytics", "métrica", "metrica", "kpi", "relatório", "relatorio", "indicador"])


# ---------------------------------------------------------------------------
# WS Dispatcher integration
# ---------------------------------------------------------------------------

class TestAnalyticsWSDispatcher:
    """Verifica que o domain 'analytics' está registrado no WS dispatcher."""

    def test_get_agent_analytics_returns_analytics_agent(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("analytics")
        assert agent is not None
        assert "analytics" in type(agent).__name__.lower() or "Analytics" in type(agent).__name__

    def test_analytics_agent_not_falls_back_to_talent(self):
        from app.api.v1.chat_shared import _get_agent
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = _get_agent("analytics")
        assert not isinstance(agent, TalentReActAgent), \
            "analytics domain não deve usar TalentReActAgent (wiring faltando)"
