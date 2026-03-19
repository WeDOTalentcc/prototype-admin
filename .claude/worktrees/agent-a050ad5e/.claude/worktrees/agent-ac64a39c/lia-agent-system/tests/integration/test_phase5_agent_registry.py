"""
Integration tests — Phase 5 ReAct Agent Registry.

Verifica que os 3 novos agentes (analytics, communication, ats_integration)
estão corretamente registrados em register_react_agents() e que o
DomainWorkflow consegue delegar para eles.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset do singleton ReactAgentRegistry entre testes."""
    from lia_agents_core.react_agent_registry import ReactAgentRegistry
    ReactAgentRegistry._instance = None
    ReactAgentRegistry._initialized = False
    yield
    ReactAgentRegistry._instance = None
    ReactAgentRegistry._initialized = False


# ---------------------------------------------------------------------------
# Testes de registro
# ---------------------------------------------------------------------------


class TestRegisterReactAgents:
    def test_register_returns_registry_instance(self):
        from lia_agents_core.react_agent_registry import register_react_agents, ReactAgentRegistry
        registry = register_react_agents()
        assert isinstance(registry, ReactAgentRegistry)

    def test_all_11_domains_registered(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        domains = registry.list_domains()
        assert len(domains) == 11

    def test_analytics_domain_registered(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        assert registry.is_registered("analytics")

    def test_communication_domain_registered(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        assert registry.is_registered("communication")

    def test_ats_integration_domain_registered(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        assert registry.is_registered("ats_integration")

    def test_legacy_domains_still_registered(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        expected_legacy = [
            "wizard", "pipeline", "sourcing", "talent",
            "jobs_management", "kanban", "policy", "automation",
        ]
        for domain in expected_legacy:
            assert registry.is_registered(domain), f"Domain '{domain}' missing"

    def test_analytics_agent_class_is_correct(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
        registry = register_react_agents()
        entry = registry._registry["analytics"]
        assert entry["agent_class"] is AnalyticsReActAgent

    def test_communication_agent_class_is_correct(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        from app.domains.communication.agents.communication_react_agent import CommunicationReActAgent
        registry = register_react_agents()
        entry = registry._registry["communication"]
        assert entry["agent_class"] is CommunicationReActAgent

    def test_ats_integration_agent_class_is_correct(self):
        from lia_agents_core.react_agent_registry import register_react_agents
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        registry = register_react_agents()
        entry = registry._registry["ats_integration"]
        assert entry["agent_class"] is ATSIntegrationReActAgent

    def test_double_register_is_idempotent(self):
        """Segunda chamada a register_react_agents não duplica domínios."""
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        count_first = len(registry.list_domains())
        registry2 = register_react_agents()
        assert len(registry2.list_domains()) == count_first


# ---------------------------------------------------------------------------
# Testes de AgentFactory
# ---------------------------------------------------------------------------


class TestAgentFactory:
    def test_factory_creates_analytics_agent(self):
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        agent = factory.create_agent(
            domain="analytics",
            session_id="sess-001",
            company_id="co-001",
            user_id="user-001",
        )
        assert agent is not None
        assert agent.domain_name == "analytics"

    def test_factory_creates_communication_agent(self):
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        agent = factory.create_agent(
            domain="communication",
            session_id="sess-002",
            company_id="co-002",
            user_id="user-002",
        )
        assert agent is not None
        assert agent.domain_name == "communication"

    def test_factory_creates_ats_integration_agent(self):
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        agent = factory.create_agent(
            domain="ats_integration",
            session_id="sess-003",
            company_id="co-003",
            user_id="user-003",
        )
        assert agent is not None
        assert agent.domain_name == "ats_integration"

    def test_factory_raises_for_unknown_domain(self):
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        with pytest.raises(KeyError):
            factory.create_agent(
                domain="nonexistent",
                session_id="sess-000",
                company_id="co-000",
                user_id="user-000",
            )

    def test_factory_creates_isolated_instances(self):
        """Cada chamada cria uma instância nova (session-safe)."""
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        agent_a = factory.create_agent(
            domain="analytics", session_id="sess-a", company_id="co-a", user_id="u-a"
        )
        agent_b = factory.create_agent(
            domain="analytics", session_id="sess-b", company_id="co-b", user_id="u-b"
        )
        assert agent_a is not agent_b


# ---------------------------------------------------------------------------
# Testes de disponibilidade de ferramentas
# ---------------------------------------------------------------------------


class TestAgentTools:
    def test_analytics_agent_exposes_tools(self):
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        agent = factory.create_agent(
            domain="analytics", session_id="s", company_id="c", user_id="u"
        )
        tools = agent.available_tools
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert "get_job_insights" in tools

    def test_communication_agent_exposes_tools(self):
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        agent = factory.create_agent(
            domain="communication", session_id="s", company_id="c", user_id="u"
        )
        tools = agent.available_tools
        assert "send_email" in tools
        assert "check_rate_limit" in tools

    def test_ats_integration_agent_exposes_tools(self):
        from lia_agents_core.react_agent_registry import register_react_agents, AgentFactory
        registry = register_react_agents()
        factory = AgentFactory(registry)
        agent = factory.create_agent(
            domain="ats_integration", session_id="s", company_id="c", user_id="u"
        )
        tools = agent.available_tools
        assert "sync_candidate_to_ats" in tools or "fetch_candidate_from_ats" in tools


# ---------------------------------------------------------------------------
# Testes de delegação via domain workflow
# ---------------------------------------------------------------------------


class TestDomainWorkflowDelegation:
    def test_unregistered_domain_not_in_registry(self):
        """Domínio inexistente retorna is_registered=False."""
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        assert not registry.is_registered("nonexistent_domain")

    def test_analytics_is_registered_and_has_config(self):
        """analytics tem config de agente no registry."""
        from lia_agents_core.react_agent_registry import register_react_agents
        registry = register_react_agents()
        assert registry.is_registered("analytics")
        entry = registry._registry["analytics"]
        assert entry.get("config", {}).get("max_iterations", 0) > 0
