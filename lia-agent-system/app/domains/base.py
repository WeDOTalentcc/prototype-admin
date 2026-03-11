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
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    HIGH = "high"      # >= 0.8
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"        # < 0.5


@dataclass
class DomainAction:
    """Represents an action a domain can perform."""
    action_id: str
    name: str
    description: str
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    tags: List[str] = field(default_factory=list)
    is_async: bool = False


@dataclass
class DomainContext:
    """Context passed to domain operations."""
    domain_id: str
    user_id: str
    session_id: str
    tenant_id: str
    current_data: Dict[str, Any] = field(default_factory=dict)
    selected_ids: List[str] = field(default_factory=list)
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    conversation_memory: Optional[Any] = None  # lazy-loaded ConversationMemory
    conversation_state: Optional[Any] = None  # lazy-loaded ConversationState
    api_calls_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntentResult:
    """Result of intent analysis."""
    intent_id: str
    action_id: str
    confidence: float
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    alternative_intents: List[Dict[str, Any]] = field(default_factory=list)

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
    data: Optional[Any] = None
    suggestions: List[str] = field(default_factory=list)
    needs_confirmation: bool = False
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    clarification_options: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    api_calls: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    domain_id: Optional[str] = None
    action_id: Optional[str] = None

    @classmethod
    def success_response(cls, message: str, data: Any = None, **kwargs) -> "DomainResponse":
        return cls(success=True, message=message, data=data, **kwargs)

    @classmethod
    def error_response(cls, error: str, message: str = "", **kwargs) -> "DomainResponse":
        return cls(success=False, message=message or error, error=error, **kwargs)

    @classmethod
    def clarification_response(cls, question: str, options: List[str] = None, **kwargs) -> "DomainResponse":
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
    domain_name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def get_allowed_actions(self) -> List[DomainAction]:
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
    async def execute_action(self, action_id: str, params: Dict[str, Any], context: DomainContext) -> DomainResponse:
        """Execute a domain action with given parameters."""
        ...

    def validate_context(self, context: DomainContext) -> bool:
        """Validate that the context has required data for this domain. Override as needed."""
        return bool(context.user_id and context.tenant_id)

    def get_suggestions(self, context: DomainContext) -> List[str]:
        """Return contextual suggestions for the user. Override as needed."""
        return []

    def get_action_by_id(self, action_id: str) -> Optional[DomainAction]:
        """Find an action by its ID."""
        for action in self.get_allowed_actions():
            if action.action_id == action_id:
                return action
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} domain_id='{self.domain_id}'>"
