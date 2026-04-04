"""
Unified provider registry.

Exports all provider abstract interfaces and factories for voice, ATS, LLM,
and Embedding integrations.
"""
from .voice_provider import VoiceProvider, VoiceProviderType, TranscriptionResult, VoiceConfig
from .ats_factory import ATSProviderFactory
from .llm_provider import LLMProviderABC, LLMResponse, LLMToolCall, LLMToolResponse
from .llm_factory import LLMProviderFactory
from .llm_claude import ClaudeLLMProvider
from .llm_gemini import GeminiLLMProvider
from .llm_openai import OpenAILLMProvider
from .embedding_provider import EmbeddingProviderABC, EmbeddingResult
from .embedding_factory import EmbeddingProviderFactory
from .embedding_gemini import GeminiEmbeddingProvider
from .embedding_openai import OpenAIEmbeddingProvider

LLMProviderFactory.register(ClaudeLLMProvider)
LLMProviderFactory.register(GeminiLLMProvider)
LLMProviderFactory.register(OpenAILLMProvider)

EmbeddingProviderFactory.register(GeminiEmbeddingProvider)
EmbeddingProviderFactory.register(OpenAIEmbeddingProvider)

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
    "EmbeddingProviderABC",
    "EmbeddingResult",
    "EmbeddingProviderFactory",
    "GeminiEmbeddingProvider",
    "OpenAIEmbeddingProvider",
]
