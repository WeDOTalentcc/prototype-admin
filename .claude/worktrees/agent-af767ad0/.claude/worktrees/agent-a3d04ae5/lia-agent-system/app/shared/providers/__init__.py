"""
Unified provider registry.

Exports all provider abstract interfaces and factories for voice, ATS, and LLM integrations.
"""
from .voice_provider import VoiceProvider, VoiceProviderType, TranscriptionResult, VoiceConfig
from .ats_factory import ATSProviderFactory
from .llm_provider import LLMProviderABC, LLMResponse, LLMToolCall, LLMToolResponse
from .llm_factory import LLMProviderFactory
from .llm_claude import ClaudeLLMProvider
from .llm_gemini import GeminiLLMProvider
from .llm_openai import OpenAILLMProvider

LLMProviderFactory.register(ClaudeLLMProvider)
LLMProviderFactory.register(GeminiLLMProvider)
LLMProviderFactory.register(OpenAILLMProvider)

__all__ = [
    "VoiceProvider",
    "VoiceProviderType",
    "TranscriptionResult",
    "VoiceConfig",
    "ATSProviderFactory",
    "LLMProviderABC",
    "LLMResponse",
    "LLMToolCall",
    "LLMToolResponse",
    "LLMProviderFactory",
    "ClaudeLLMProvider",
    "GeminiLLMProvider",
    "OpenAILLMProvider",
]
