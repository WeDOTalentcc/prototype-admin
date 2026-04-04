"""
Formal contracts (Python Protocols) for architectural boundaries in the LIA agent system.

Defines the 4 boundary protocols:
- OrchestratorProtocol  — central orchestrator → domain routing
- DomainProtocol        — domain → intent processing + action execution
- AgentProtocol         — agent → message processing
- LLMProviderProtocol   — LLM provider → text generation

These Protocols enable:
1. Compile-time structural subtyping (no inheritance needed)
2. Clean dependency injection without circular imports
3. Easy mocking at layer boundaries in tests
4. Independent evolution of each layer

Usage::

    from lia_agents_core.contracts import AgentProtocol

    def build_pipeline(agent: AgentProtocol) -> None:
        ...  # agent can be any object that satisfies the Protocol
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# OrchestratorProtocol
# Central orchestrator that routes user messages to the correct domain agent.
# ---------------------------------------------------------------------------

@runtime_checkable
class OrchestratorProtocol(Protocol):
    """Contract for the central LIA orchestrator.

    The orchestrator receives a raw user message plus session context and
    returns an ``AgentOutput``-compatible dict (or raises).  It must NOT
    import any specific domain agent directly; dependency injection via this
    Protocol eliminates that circular coupling.
    """

    async def route(
        self,
        message: str,
        session_id: str,
        company_id: str,
        user_id: str,
        context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route a user message to the appropriate domain agent.

        Args:
            message: Raw user message text.
            session_id: Unique chat session identifier.
            company_id: Tenant company ID (multi-tenancy).
            user_id: ID of the authenticated user.
            context: Current session/domain context data.
            conversation_history: Prior conversation turns.
            metadata: Optional routing hints (channel, locale, etc.).

        Returns:
            Structured response dict compatible with ``AgentOutput``.
        """
        ...

    async def get_status(self) -> Dict[str, Any]:
        """Return orchestrator health and routing statistics."""
        ...


# ---------------------------------------------------------------------------
# DomainProtocol
# Each domain (job_management, sourcing, pipeline, …) must satisfy this.
# ---------------------------------------------------------------------------

@runtime_checkable
class DomainProtocol(Protocol):
    """Contract for domain implementations.

    A domain encapsulates:
    - Intent analysis: what does the user want within this domain?
    - Action execution: carry out validated intents against backend APIs.

    Domains never import from each other; they communicate only through the
    orchestrator or via ``AgentBus`` events.
    """

    @property
    def domain_id(self) -> str:
        """Unique domain identifier, e.g. ``"job_management"``."""
        ...

    @property
    def domain_name(self) -> str:
        """Human-readable domain name."""
        ...

    def get_allowed_actions(self) -> List[Dict[str, Any]]:
        """Return the list of actions supported by this domain.

        Each dict must contain at least ``action_id`` and ``description``.
        """
        ...

    def get_system_prompt(self) -> str:
        """Return the LLM system prompt for this domain's agent."""
        ...

    async def process_intent(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyse ``query`` and return a structured intent result dict.

        Minimum keys: ``intent_id``, ``action_id``, ``confidence``.
        """
        ...

    async def execute_action(
        self,
        action_id: str,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute ``action_id`` with ``params`` and return a response dict.

        Minimum keys: ``success``, ``message``.
        """
        ...


# ---------------------------------------------------------------------------
# AgentProtocol
# All ReAct / LangGraph agents (wizard, sourcing, pipeline, …) must satisfy.
# ---------------------------------------------------------------------------

@runtime_checkable
class AgentProtocol(Protocol):
    """Contract for domain-level ReAct agents.

    An ``AgentProtocol`` implementation processes a fully-structured
    ``AgentInput``-compatible dict and returns an ``AgentOutput``-compatible
    dict.  It must NOT import from ``app.shared.agents``; use
    ``lia_agents_core`` directly.
    """

    @property
    def domain_name(self) -> str:
        """Domain this agent operates in (e.g. ``"wizard"``, ``"sourcing"``)."""
        ...

    @property
    def available_tools(self) -> List[str]:
        """Tool names available to this agent."""
        ...

    async def process(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user input dict and return a structured output dict.

        Args:
            input: Dict compatible with ``AgentInput`` schema.  Must contain
                at minimum ``message``, ``session_id``, ``company_id``,
                ``user_id``, and ``context``.

        Returns:
            Dict compatible with ``AgentOutput`` schema.  Must contain at
            minimum ``message`` and ``actions``.
        """
        ...

    async def get_status(self) -> Dict[str, Any]:
        """Return agent health, domain, and available_tools."""
        ...


# ---------------------------------------------------------------------------
# LLMProviderProtocol
# Structural twin of LLMProviderABC — allows mock injection without ABC.
# ---------------------------------------------------------------------------

@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Structural contract for LLM provider implementations.

    This Protocol mirrors ``LLMProviderABC`` from
    ``app.shared.providers.llm_provider`` but uses ``Protocol`` instead of
    ``ABC``, enabling structural subtyping and clean mock injection in tests.

    Any object satisfying this Protocol can be passed wherever an LLM
    provider is required, without needing to inherit from the ABC.
    """

    @property
    def provider_name(self) -> str:
        """Provider identifier, e.g. ``"claude"``, ``"gemini"``, ``"openai"``."""
        ...

    @property
    def default_model(self) -> str:
        """Default model string for this provider."""
        ...

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any:
        """Generate a text completion.  Returns an ``LLMResponse``-like object."""
        ...

    async def generate_with_system(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any:
        """Generate with explicit system prompt and user message."""
        ...

    async def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Any:
        """Generate with tool/function calling support.

        Returns an ``LLMToolResponse``-like object.
        """
        ...

    async def generate_structured(
        self,
        messages: List[Dict[str, Any]],
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate structured output matching a JSON schema."""
        ...


__all__ = [
    "OrchestratorProtocol",
    "DomainProtocol",
    "AgentProtocol",
    "LLMProviderProtocol",
]
