"""
Unified provider registry.

Exports all provider abstract interfaces and factories for voice, ATS, LLM,
and Embedding integrations.
"""
from .ats_factory import ATSProviderFactory
from .embedding_factory import EmbeddingProviderFactory
from .embedding_gemini import GeminiEmbeddingProvider
from .embedding_openai import OpenAIEmbeddingProvider
from .embedding_provider import EmbeddingProviderABC, EmbeddingResult
from .llm_claude import ClaudeLLMProvider
from .llm_deepseek import DeepSeekLLMProvider
from .llm_factory import LLMProviderFactory, get_voice_provider_for_tenant
from .llm_gemini import GeminiLLMProvider
from .llm_openai import OpenAILLMProvider
from .llm_provider import LLMProviderABC, LLMResponse, LLMToolCall, LLMToolResponse
from .voice_composite import CompositeVoiceProvider
from .voice_gemini_live import GeminiLiveVoiceProvider
from .voice_openai_realtime import OpenAIRealtimeVoiceProvider
from .voice_provider import (
    TranscriptionResult,
    VoiceConfig,
    VoiceProvider,
    VoiceProviderType,
    VoiceSessionConfig,
    VoiceSessionMetrics,
    VoiceStrategyType,
    VoiceStreamEvent,
    VoiceStreamProviderABC,
)

LLMProviderFactory.register(ClaudeLLMProvider)
LLMProviderFactory.register(GeminiLLMProvider)
LLMProviderFactory.register(OpenAILLMProvider)
LLMProviderFactory.register(DeepSeekLLMProvider)

EmbeddingProviderFactory.register(GeminiEmbeddingProvider)
EmbeddingProviderFactory.register(OpenAIEmbeddingProvider)

__all__ = [
    "VoiceProvider",
    "VoiceProviderType",
    "VoiceStreamProviderABC",
    "VoiceStrategyType",
    "VoiceStreamEvent",
    "VoiceSessionConfig",
    "VoiceSessionMetrics",
    "TranscriptionResult",
    "VoiceConfig",
    "GeminiLiveVoiceProvider",
    "OpenAIRealtimeVoiceProvider",
    "CompositeVoiceProvider",
    "get_voice_provider_for_tenant",
    "ATSProviderFactory",
    "LLMProviderABC",
    "LLMResponse",
    "LLMToolCall",
    "LLMToolResponse",
    "LLMProviderFactory",
    "ClaudeLLMProvider",
    "GeminiLLMProvider",
    "OpenAILLMProvider",
    "EmbeddingProviderABC",
    "EmbeddingResult",
    "EmbeddingProviderFactory",
    "GeminiEmbeddingProvider",
    "OpenAIEmbeddingProvider",
]
