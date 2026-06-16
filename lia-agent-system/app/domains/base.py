"""
Domain Base - Foundation for all LIA domain implementations.

Architecture B: Domain-driven design with DomainPrompt contract.
Each domain implements this ABC to provide:
- Intent processing (what does the user want?)
- Action execution (do it)
- System prompt generation
- Context validation
- Suggestions for the user

Compatible with existing BaseAgent but independent - no imports from agents/.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(StrEnum):
    ACTION = "action"
    QUERY = "query"
    NAVIGATION = "navigation"


class ConfidenceLevel(StrEnum):
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"        # < 0.5


@dataclass
class DomainAction:
    """Represents an action a domain can perform."""
    id: str = ""
    action_id: str = ""
    name: str = ""
    description: str = ""
    action_type: "ActionType" = ActionType.ACTION
    required_params: list[str] = field(default_factory=list)
    optional_params: list[str] = field(default_factory=list)
    requires_confirmation: bool = False
    tags: list[str] = field(default_factory=list)
    is_async: bool = False
    examples: tuple[str, ...] | list[str] = field(default_factory=tuple)


@dataclass
class DomainContext:
    """Context passed to domain operations."""
    domain_id: str
    user_id: str
    session_id: str
    tenant_id: str
    current_data: dict[str, Any] = field(default_factory=dict)
    selected_ids: list[str] = field(default_factory=list)
    filters_applied: dict[str, Any] = field(default_factory=dict)
    conversation_memory: Any | None = None  # lazy-loaded ConversationMemory
    conversation_state: Any | None = None  # lazy-loaded ConversationState
    api_calls_history: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntentResult:
    """Result of intent analysis."""
    intent_id: str
    action_id: str
    confidence: float
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    extracted_params: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    alternative_intents: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.confidence >= 0.8:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            self.confidence_level = ConfidenceLevel.MEDIUM
        else:
            self.confidence_level = ConfidenceLevel.LOW


@dataclass
class DomainResponse:
    """Standard response from domain operations."""
    success: bool
    message: str
    data: Any | None = None
    suggestions: list[str] = field(default_factory=list)
    needs_confirmation: bool = False
    needs_clarification: bool = False
    clarification_question: str | None = None
    clarification_options: list[str] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    api_calls: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    domain_id: str | None = None
    action_id: str | None = None

    @classmethod
    def success_response(cls, message: str, data: Any = None, **kwargs) -> "DomainResponse":
        return cls(success=True, message=message, data=data, **kwargs)

    @classmethod
    def error_response(cls, error: str, message: str = "", **kwargs) -> "DomainResponse":
        return cls(success=False, message=message or error, error=error, **kwargs)

    @classmethod
    def clarification_response(cls, question: str, options: list[str] = None, **kwargs) -> "DomainResponse":
        return cls(
            success=True,
            message=question,
            needs_clarification=True,
            clarification_question=question,
            clarification_options=options or [],
            **kwargs,
        )

    @classmethod
    def confirmation_response(cls, message: str, data: Any = None, **kwargs) -> "DomainResponse":
        return cls(success=True, message=message, data=data, needs_confirmation=True, **kwargs)


class DomainPrompt(ABC):
    """
    Abstract base class for all LIA domains.
    
    Each domain must implement this contract to participate in the
    domain-driven architecture. The DomainRegistry discovers domains
    via the @register_domain decorator.
    """
    domain_id: str = ""
    agent_aliases: tuple[str, ...] = ()  # extra routing aliases for this domain

    @classmethod
    def get_agent_aliases(cls) -> tuple[str, ...]:
        """Return extra routing aliases for this domain (beyond domain_id self-mapping)."""
        return getattr(cls, "agent_aliases", ())
    domain_name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def get_allowed_actions(self) -> list[DomainAction]:
        """Return list of actions this domain can perform."""
        ...

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for LLM interactions in this domain."""
        ...

    @abstractmethod
    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        """Analyze user query and determine intent within this domain."""
        ...

    @abstractmethod
    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        """Execute a domain action with given parameters."""
        ...

    def validate_context(self, context: DomainContext) -> bool:
        """Validate that the context has required data for this domain. Override as needed."""
        return bool(context.user_id and context.tenant_id)

    def get_suggestions(self, context: DomainContext) -> list[str]:
        """Return contextual suggestions for the user. Override as needed."""
        return []

    def get_action_by_id(self, action_id: str) -> DomainAction | None:
        """Find an action by its ID."""
        for action in self.get_allowed_actions():
            if action.action_id == action_id:
                return action
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} domain_id='{self.domain_id}'>"
