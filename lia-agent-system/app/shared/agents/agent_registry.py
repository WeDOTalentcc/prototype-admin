"""
AgentRegistry — canonical singleton lookup for ReAct agent instances.

Mirrors DomainRegistry (app/domains/registry.py) but serves ReAct agent
executors (LangGraphReActBase subclasses) instead of DomainPrompts.

Rationale (Wave 2 / Fase 3a):
  Previously agent_chat_ws.py:_get_agent() was a 21-branch if/elif that
  duplicated DomainRegistry at agent level. This registry follows the
  standard enterprise pattern: @register_agent decorator + lazy singleton
  instantiation via AgentRegistry().get_instance(id).

Usage:
    @register_agent("wizard")
    class WizardReActAgent(LangGraphReActBase, EnhancedAgentMixin):
        ...

    @register_agent("pipeline", aliases=["cv_screening"])
    class PipelineReActAgent(...):
        ...

    # dispatch:
    agent = AgentRegistry().get_instance("wizard")
    agent = AgentRegistry().get_or_fallback("unknown", fallback_id="talent")

Compliance: agents MUST extend LangGraphReActBase (enforced at decoration
time via TypeError). Escape hatch: LIA_ALLOW_NON_COMPLIANT_AGENTS=1 (emergency
only — mirrors LIA_ALLOW_NON_COMPLIANT_DOMAINS in DomainRegistry).

"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_AGENT_REGISTRY: dict[str, type] = {}
_AGENT_ALIASES: dict[str, str] = {}  # alias -> canonical_id


def _get_base_classes() -> tuple[type, ...]:
    """Lazy import of LangGraphReActBase to avoid circular imports at module load."""
    try:
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        return (LangGraphReActBase,)
    except ImportError:
        return ()


def register_agent(agent_id: str, *, aliases: list[str] | None = None):
    """Decorator for auto-registering ReAct agent classes.

    Args:
        agent_id: canonical domain id (e.g., "wizard", "sourcing", "pipeline")
        aliases: alternate ids that resolve to the same class (e.g., "cv_screening"
                 maps to "pipeline"; "jobs_mgmt" maps to "jobs_management")

    Raises:
        TypeError: if the decorated class does not extend LangGraphReActBase
                   (unless LIA_ALLOW_NON_COMPLIANT_AGENTS=1 is set).
    """
    def decorator(cls: type) -> type:
        # Enforce LangGraphReActBase inheritance
        bases = _get_base_classes()
        if bases and not issubclass(cls, bases):
            msg = (
                f"[AgentRegistry] Agent '{agent_id}' (class={cls.__name__}) does NOT "
                f"extend LangGraphReActBase. All agents MUST inherit from it for "
                f"PII stripping, FairnessGuard, AuditCallback and tool timeout."
            )
            if os.environ.get("LIA_ALLOW_NON_COMPLIANT_AGENTS") == "1":
                logger.error("%s — BYPASS via LIA_ALLOW_NON_COMPLIANT_AGENTS=1", msg)
            else:
                logger.error(msg)
                raise TypeError(msg)

        if agent_id in _AGENT_REGISTRY:
            logger.warning(
                "[AgentRegistry] Agent '%s' already registered by %s. Overwriting with %s.",
                agent_id, _AGENT_REGISTRY[agent_id].__name__, cls.__name__,
            )

        _AGENT_REGISTRY[agent_id] = cls

        if aliases:
            for alias in aliases:
                if alias in _AGENT_ALIASES:
                    logger.warning(
                        "[AgentRegistry] Alias '%s' already points to '%s', overwriting with '%s'.",
                        alias, _AGENT_ALIASES[alias], agent_id,
                    )
                _AGENT_ALIASES[alias] = agent_id

        logger.info(
            "[AgentRegistry] Registered: %s (class=%s, aliases=%s)",
            agent_id, cls.__name__, aliases or [],
        )
        return cls

    return decorator


class AgentRegistry:
    """Singleton registry with lazy instance caching per agent_id."""

    _instance: "AgentRegistry | None" = None
    _instances: dict[str, Any] = {}

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._instances = {}
        return cls._instance

    def _resolve_id(self, agent_id: str) -> str:
        """Resolve aliases to canonical id."""
        return _AGENT_ALIASES.get(agent_id, agent_id)

    def get_instance(self, agent_id: str) -> Any | None:
        """Get (or create + cache) an agent instance by id/alias.

        Returns None if agent_id is unknown.
        """
        canonical = self._resolve_id(agent_id)
        if canonical in self._instances:
            return self._instances[canonical]

        cls = _AGENT_REGISTRY.get(canonical)
        if cls is None:
            logger.warning("[AgentRegistry] Agent '%s' not found in registry", agent_id)
            return None

        try:
            instance = cls()
            self._instances[canonical] = instance
            return instance
        except Exception as exc:
            logger.error("[AgentRegistry] Failed to instantiate '%s': %s", agent_id, exc)
            return None

    def get_or_fallback(self, agent_id: str, *, fallback_id: str) -> Any | None:
        """Get instance by id, falling back to fallback_id if not found.

        Does NOT suppress fallback errors — if fallback_id is unknown, returns None.
        """
        inst = self.get_instance(agent_id)
        if inst is not None:
            return inst
        logger.info("[AgentRegistry] Falling back '%s' -> '%s'", agent_id, fallback_id)
        return self.get_instance(fallback_id)

    def list_agents(self) -> list[str]:
        """List canonical agent ids (excluding aliases)."""
        return list(_AGENT_REGISTRY.keys())

    def list_aliases(self) -> dict[str, str]:
        """Map of alias -> canonical id."""
        return dict(_AGENT_ALIASES)

    def is_registered(self, agent_id: str) -> bool:
        """True if agent_id (or alias) resolves to a registered agent."""
        return self._resolve_id(agent_id) in _AGENT_REGISTRY

    def reset(self) -> None:
        """Clear cached instances (for testing)."""
        self._instances.clear()

    @classmethod
    def reset_registry(cls) -> None:
        """Reset registry + instances (tests only)."""
        global _AGENT_REGISTRY, _AGENT_ALIASES
        _AGENT_REGISTRY.clear()
        _AGENT_ALIASES.clear()
        if cls._instance:
            cls._instance._instances.clear()

    def __repr__(self) -> str:
        return (
            f"<AgentRegistry registered={sorted(_AGENT_REGISTRY.keys())} "
            f"aliases={_AGENT_ALIASES} instantiated={sorted(self._instances.keys())}>"
        )
