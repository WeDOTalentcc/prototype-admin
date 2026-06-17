"""
LLM Provider Abstraction Layer.

Defines the contract for LLM provider implementations.
Allows swapping between Claude, Gemini, OpenAI without changing business logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    text: str
    provider: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw_response: Any | None = None


@dataclass 
class LLMToolCall:
    """Standardized tool call from any LLM provider."""
    id: str
    name: str
    parameters: dict[str, Any]


@dataclass
class LLMToolResponse:
    """Standardized tool response from any LLM provider."""
    text: str | None = None
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    is_tool_call: bool = False
    provider: str = ""
    model: str = ""
    raw_response: Any | None = None


class LLMProviderABC(ABC):
    """Abstract base class for LLM providers.
    
    Implement this interface to add new LLM providers.
    The factory will manage provider instances.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'claude', 'gemini', 'openai')."""
        ...
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""
        ...
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate text completion."""
        ...
    
    @abstractmethod
    async def generate_with_system(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate with explicit system prompt and user message."""
        ...
    
    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMToolResponse:
        """Generate with tool/function calling support."""
        ...
    
    @abstractmethod
    async def generate_structured(
        self,
        messages: list[dict[str, Any]],
        output_schema: dict[str, Any],
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> dict[str, Any]:
        """Generate structured output matching a JSON schema."""
        ...
