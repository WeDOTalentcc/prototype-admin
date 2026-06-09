"""W1-001-B (2026-05-23) — Canonical AgentRegistry integration tests.

Substitui tests legacy `test_phase5_agent_registry.py` (que dependia de
`ReactAgentRegistry` + `register_react_agents()` removed em W1-001-B).

Verifica que os agents Phase 5 (analytics, communication, ats_integration)
+ os core agents continuam registráveis e acessíveis via canonical
`AgentRegistry().get_instance(id)` pattern.

Pre-existing test file (229 LOC) reescrita para 1 SOC: validar coverage
do registry canonical sem testar mecânica interna do legacy
ReactAgentRegistry/AgentFactory (que não existem mais).
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_canonical_registry():
    """Reset AgentRegistry instances cache entre testes (sem reset do _AGENT_REGISTRY
    porque decoradores rodaram em import time)."""
    from app.shared.agents.agent_registry import AgentRegistry
    AgentRegistry().reset()
    yield
    AgentRegistry().reset()


class TestCanonicalRegistry:
    """Canonical AgentRegistry coverage (Phase 5 + core domains)."""

    def test_phase5_domains_registered(self):
        """analytics, communication, ats_integration registrados via @register_agent."""
        from app.api.v1.chat_shared import _ensure_agents_loaded
        from app.shared.agents.agent_registry import AgentRegistry

        _ensure_agents_loaded()
        registry = AgentRegistry()
        for domain in ["analytics", "communication", "ats_integration"]:
            assert registry.is_registered(domain), (
                f"Phase 5 domain '{domain}' not registered in canonical AgentRegistry"
            )

    def test_core_domains_registered(self):
        """Core domains canonical (wizard, pipeline, sourcing, talent, etc)."""
        from app.api.v1.chat_shared import _ensure_agents_loaded
        from app.shared.agents.agent_registry import AgentRegistry

        _ensure_agents_loaded()
        registry = AgentRegistry()
        for domain in [
            "wizard", "pipeline", "sourcing", "talent",
            "jobs_management", "kanban", "policy",
        ]:
            assert registry.is_registered(domain), (
                f"Core domain '{domain}' not registered"
            )

    def test_get_instance_returns_callable_agent(self):
        """AgentRegistry().get_instance retorna agente com process method."""
        from app.api.v1.chat_shared import _ensure_agents_loaded
        from app.shared.agents.agent_registry import AgentRegistry

        _ensure_agents_loaded()
        agent = AgentRegistry().get_instance("communication")
        assert agent is not None
        assert hasattr(agent, "process"), "Agent must have async process method"

    def test_get_or_fallback_returns_talent_for_unknown(self):
        """get_or_fallback retorna talent quando domain desconhecido."""
        from app.api.v1.chat_shared import _ensure_agents_loaded
        from app.shared.agents.agent_registry import AgentRegistry

        _ensure_agents_loaded()
        registry = AgentRegistry()
        agent = registry.get_or_fallback("nonexistent_domain", fallback_id="talent")
        assert agent is not None, "Fallback to talent should resolve"
        # Identify it's a talent agent (instance class name contains "Talent")
        assert "Talent" in agent.__class__.__name__

    def test_pipeline_cv_screening_alias_resolves(self):
        """cv_screening alias resolve para pipeline (canonical W1-001 alias)."""
        from app.api.v1.chat_shared import _ensure_agents_loaded
        from app.shared.agents.agent_registry import AgentRegistry

        _ensure_agents_loaded()
        registry = AgentRegistry()
        assert registry.is_registered("cv_screening"), (
            "cv_screening alias should resolve to pipeline"
        )

    def test_unknown_domain_returns_none(self):
        """get_instance('made-up-name') retorna None sem raise."""
        from app.shared.agents.agent_registry import AgentRegistry

        registry = AgentRegistry()
        result = registry.get_instance("definitely-not-a-real-domain-xyz")
        assert result is None
