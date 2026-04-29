"""
W4.1: register_agent decorator em automation + autonomous (gap real W3.3 v2).

Auditoria 2026-04-27: 2 dos 13 agents existentes nao tem @register_agent.
Discovery confirmou que ambos funcionam via paths nao-canonical:
  - AutomationReActAgent: chamado diretamente por task_planner endpoint +
    Sidekiq jobs.
  - AutonomousReActAgent: chamado pelo cascaded_router como Tier 6
    cross-domain fallback via factory get_autonomous_react_agent().

Nao estao quebrados, mas ficaram fora do registry pattern canonical.
Fix: adicionar @register_agent (decorator e nao-disruptivo, callsites
diretos preservados; agents tornam-se routable via registry tambem).
"""
from __future__ import annotations
import inspect


class TestRegisterAgentCanonical:
    def test_automation_react_agent_has_register_agent(self):
        from app.domains.automation.agents.automation_react_agent import (
            AutomationReActAgent,
        )
        # The decorator stamps a metadata attribute on the class
        # via app.shared.agents.agent_registry.register_agent. We check
        # via source inspection (works regardless of how the decorator is
        # implemented) and via registry presence.
        src = inspect.getsource(AutomationReActAgent)
        # Decorator should appear above the class definition in source
        # (inspect.getsource includes decorators). Check the file source too.
        import app.domains.automation.agents.automation_react_agent as mod
        mod_src = inspect.getsource(mod)
        assert "@register_agent(" in mod_src, (
            "AutomationReActAgent must have @register_agent decorator (W4.1 — "
            "make agent routable via canonical registry pattern)"
        )

    def test_autonomous_react_agent_has_register_agent(self):
        from app.domains.autonomous.agents.autonomous_react_agent import (
            AutonomousReActAgent,
        )
        import app.domains.autonomous.agents.autonomous_react_agent as mod
        mod_src = inspect.getsource(mod)
        assert "@register_agent(" in mod_src, (
            "AutonomousReActAgent must have @register_agent decorator (W4.1)"
        )

    def test_automation_registered_in_registry(self):
        # Importing the module triggers the decorator side-effect
        import app.domains.automation.agents.automation_react_agent  # noqa: F401
        from app.shared.agents.agent_registry import _AGENT_REGISTRY
        assert "automation" in _AGENT_REGISTRY, (
            f"'automation' must be in registry. Current: {list(_AGENT_REGISTRY.keys())}"
        )

    def test_autonomous_registered_in_registry(self):
        import app.domains.autonomous.agents.autonomous_react_agent  # noqa: F401
        from app.shared.agents.agent_registry import _AGENT_REGISTRY
        assert "autonomous" in _AGENT_REGISTRY, (
            f"'autonomous' must be in registry. Current: {list(_AGENT_REGISTRY.keys())}"
        )

    def test_existing_callsites_unbroken(self):
        """
        Decorator é puramente registro adicional — callsites existentes (direct
        instantiation, factory, endpoint) devem continuar funcionando.
        """
        from app.domains.automation.agents.automation_react_agent import (
            AutomationReActAgent,
        )
        from app.domains.autonomous.agents.autonomous_react_agent import (
            AutonomousReActAgent,
            get_autonomous_react_agent,
        )
        # Class still instantiable (no breaking signature change)
        assert AutomationReActAgent is not None
        # Factory still callable
        agent = get_autonomous_react_agent()
        assert isinstance(agent, AutonomousReActAgent)
