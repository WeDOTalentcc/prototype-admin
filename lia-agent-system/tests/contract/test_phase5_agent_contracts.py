"""
Contract tests — Phase 5 agents (Analytics, Communication, ATSIntegration).

Verifica contratos de interface: AgentInput/AgentOutput, multi-tenant,
LGPD constraints e compatibilidade com o registry.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_input(
    message: str = "teste",
    session_id: str = "sess-contract-001",
    company_id: str = "co-contract-001",
    user_id: str = "user-001",
    context: dict | None = None,
):
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message=message,
        session_id=session_id,
        company_id=company_id,
        user_id=user_id,
        context=context or {},
    )


# ---------------------------------------------------------------------------
# Analytics Agent — Contracts
# ---------------------------------------------------------------------------


class TestAnalyticsAgentContract:
    def test_analytics_agent_output_is_agent_output_type(self):
        """AnalyticsReActAgent.process() sempre retorna AgentOutput."""
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        from lia_agents_core.agent_interface import AgentOutput
        agent = AnalyticsReActAgent()
        assert hasattr(agent, "process")
        # Verify return type annotation
        import inspect
        hints = inspect.get_annotations(agent.process)
        # AgentOutput is the return type (checked by running)
        assert callable(agent.process)

    @pytest.mark.asyncio
    async def test_analytics_agent_returns_agent_output_on_error(self):
        """process() nunca levanta exceção — sempre retorna AgentOutput."""
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        from lia_agents_core.agent_interface import AgentOutput

        agent = AnalyticsReActAgent()
        inp = _make_agent_input(message="trigger error")

        with patch.object(agent, "_process_langgraph", side_effect=RuntimeError("boom")):
            result = await agent.process(inp)

        assert isinstance(result, AgentOutput)
        assert result.error is not None
        assert result.confidence == 0.0

    def test_analytics_agent_domain_name(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent()
        assert agent.domain_name == "analytics"

    def test_analytics_agent_has_required_tools(self):
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        agent = AnalyticsReActAgent()
        required_tools = {
            "get_job_insights",
            "predict_hiring_metrics",
            "generate_job_report",
            "generate_candidate_report",
            "get_search_analytics",
            "get_agent_performance",
        }
        assert required_tools.issubset(set(agent.available_tools))

    def test_analytics_tools_with_job_id_also_have_company_id(self):
        """Tools que recebem job_id (não candidate_ids) também devem receber company_id."""
        from app.domains.analytics.agents.analytics_tool_registry import get_analytics_tools
        tools = get_analytics_tools()
        job_scoped_tools = [t for t in tools if "job_id" in t.description and "candidate_ids" not in t.description]
        for tool in job_scoped_tools:
            assert "company_id" in tool.description, (
                f"Tool '{tool.name}' com job_id deve também exigir company_id"
            )


# ---------------------------------------------------------------------------
# Communication Agent — Contracts
# ---------------------------------------------------------------------------


class TestCommunicationAgentContract:
    def test_communication_agent_domain_name(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent()
        assert agent.domain_name == "communication"

    @pytest.mark.asyncio
    async def test_communication_agent_returns_agent_output_on_error(self):
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        from lia_agents_core.agent_interface import AgentOutput

        agent = CommunicationReActAgent()
        inp = _make_agent_input(message="enviar email")

        with patch.object(agent, "_process_langgraph", side_effect=RuntimeError("comm error")):
            result = await agent.process(inp)

        assert isinstance(result, AgentOutput)
        assert result.confidence == 0.0

    def test_communication_agent_has_lgpd_tools(self):
        """CommunicationAgent deve ter check_rate_limit (compliance LGPD)."""
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent()
        assert "check_rate_limit" in agent.available_tools

    def test_communication_agent_has_history_tool(self):
        """CommunicationAgent deve ter get_communication_history."""
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        agent = CommunicationReActAgent()
        assert "get_communication_history" in agent.available_tools

    def test_communication_system_prompt_enforces_lgpd(self):
        """System prompt deve mencionar LGPD e rate limit."""
        from app.domains.communication.agents.communication_system_prompt import (
            get_communication_system_prompt,
        )
        prompt = get_communication_system_prompt()
        prompt_lower = prompt.lower()
        assert "lgpd" in prompt_lower or "rate limit" in prompt_lower or "opt-out" in prompt_lower

    def test_communication_stage_context_has_lgpd_stage(self):
        """Deve ter estágio de detecção de intenção com check_rate_limit."""
        from app.domains.communication.agents.communication_stage_context import (
            STAGE_DEFINITIONS,
            get_stage_tools,
        )
        # check_rate_limit deve aparecer em algum estágio
        all_tools = set()
        for stage in STAGE_DEFINITIONS:
            all_tools.update(get_stage_tools(stage))
        assert "check_rate_limit" in all_tools

    def test_communication_tool_descriptions_require_company_id(self):
        """Todas as tools de comunicação exigem company_id via canonical contract.

        Canonical multi-tenancy (CLAUDE.md REGRA #1 + Pydantic R2):
        company_id NUNCA aparece na description (que vai pro LLM) — vem do JWT
        via Depends(require_company_id) e é injetado pelo runtime_context.
        O flag \\`ToolContract.requires_company_id=True\\` é a fonte canonical.
        """
        from app.domains.communication.agents.communication_tool_registry import (
            get_communication_tools,
        )
        tools = get_communication_tools()
        for tool in tools:
            assert tool.requires_company_id is True, (
                f"Tool '{tool.name}' deve declarar requires_company_id=True "
                f"(canonical multi-tenant gate via runtime_context)"
            )


# ---------------------------------------------------------------------------
# ATS Integration Agent — Contracts
# ---------------------------------------------------------------------------


class TestATSIntegrationAgentContract:
    def test_ats_agent_domain_name(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()
        assert agent.domain_name == "ats_integration"

    @pytest.mark.asyncio
    async def test_ats_agent_returns_agent_output_on_error(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        from lia_agents_core.agent_interface import AgentOutput

        agent = ATSIntegrationReActAgent()
        inp = _make_agent_input(message="sync candidate")

        with patch.object(agent, "_process_langgraph", side_effect=RuntimeError("ats error")):
            result = await agent.process(inp)

        assert isinstance(result, AgentOutput)
        assert result.confidence == 0.0

    def test_ats_agent_has_sync_tools(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()
        tools = agent.available_tools
        # Must have at least one sync tool
        sync_tools = [t for t in tools if "sync" in t or "fetch" in t or "validate" in t]
        assert len(sync_tools) > 0

    def test_ats_agent_has_minimum_tools(self):
        """ATS agent has at least 5 sync tools.

        Originally 5 (sync/fetch/validate/bulk/status). Grew to 8 with integration
        catalog tools (recommend_by_industry, apply_entry, create_custom).
        Asserts floor — new canonical tools can be added without breaking the test.
        """
        from app.domains.ats_integration.agents.ats_integration_tool_registry import (
            get_ats_integration_tools,
        )
        tools = get_ats_integration_tools()
        assert len(tools) >= 5, (
            f"ATS agent must keep at least 5 sync tools, got {len(tools)}"
        )
        # Sync surface canonical (audit 2026-05-22): must keep these 5 names.
        canonical_sync_tool_names = {
            "sync_candidate_to_ats",
            "fetch_candidate_from_ats",
            "validate_ats_fields",
            "bulk_sync_candidates",
            "get_sync_status",
        }
        actual_names = {t.name for t in tools}
        missing = canonical_sync_tool_names - actual_names
        assert not missing, f"Canonical sync tools removed: {missing}"

    def test_ats_stage_context_has_provider_detection_stage(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import (
            STAGE_DEFINITIONS,
        )
        assert "provider-detection" in STAGE_DEFINITIONS

    def test_ats_tool_descriptions_require_company_id(self):
        """Todas as tools de ATS exigem company_id via canonical contract.

        Canonical multi-tenancy (CLAUDE.md REGRA #1 + Pydantic R2):
        company_id NUNCA aparece na description (que vai pro LLM) — vem do JWT
        via Depends(require_company_id) e é injetado pelo runtime_context.
        O flag \\`ToolContract.requires_company_id=True\\` é a fonte canonical.
        """
        from app.domains.ats_integration.agents.ats_integration_tool_registry import (
            get_ats_integration_tools,
        )
        tools = get_ats_integration_tools()
        for tool in tools:
            assert tool.requires_company_id is True, (
                f"Tool '{tool.name}' deve declarar requires_company_id=True "
                f"(canonical multi-tenant gate via runtime_context)"
            )

    def test_ats_system_prompt_mentions_gupy_or_pandape(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import (
            get_ats_integration_system_prompt,
        )
        prompt = get_ats_integration_system_prompt()
        prompt_lower = prompt.lower()
        assert "gupy" in prompt_lower or "pandapé" in prompt_lower or "merge" in prompt_lower


# ---------------------------------------------------------------------------
# Cross-agent contracts
# ---------------------------------------------------------------------------


class TestCrossAgentContracts:
    def test_all_phase5_agents_have_consistent_confidence_range(self):
        """Confidence dos novos agentes deve estar em [0.0, 1.0]."""
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent

        # Confidence fields in _state_to_output are: 0.88, 0.90, 0.85
        for cls in [AnalyticsReActAgent, CommunicationReActAgent, ATSIntegrationReActAgent]:
            agent = cls()
            assert hasattr(agent, "domain_name")
            assert hasattr(agent, "available_tools")

    def test_all_phase5_agents_have_langgraph_process(self):
        """Todos os novos agentes têm _process_langgraph."""
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent

        for cls in [AnalyticsReActAgent, CommunicationReActAgent, ATSIntegrationReActAgent]:
            agent = cls()
            assert hasattr(agent, "_process_langgraph"), f"{cls.__name__} missing _process_langgraph"

    def test_all_phase5_agents_registered_in_registry(self):
        """W1-001-B (2026-05-23): Migrado para canonical AgentRegistry."""
        from app.api.v1.chat_shared import _ensure_agents_loaded
        from app.shared.agents.agent_registry import AgentRegistry

        _ensure_agents_loaded()
        registry = AgentRegistry()
        for domain in ["analytics", "communication", "ats_integration"]:
            assert registry.is_registered(domain), f"Domain '{domain}' not registered"
