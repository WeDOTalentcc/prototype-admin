"""
Voice Provider Abstract Interface

Defines a common interface for voice/transcription providers (Gemini, Twilio)
AND bidirectional voice streaming providers (Gemini Live, OpenAI Realtime, Composite).

Two abstraction layers:
  - VoiceProvider: simple transcription (transcribe audio → text)
  - VoiceStreamProviderABC: bidirectional real-time voice streaming (mic ↔ LLM ↔ speaker)

Strategy types for VoiceStreamProviderABC:
  - NATIVE_MULTIMODAL: single connection handles STT + LLM + TTS (Gemini Live, OpenAI Realtime)
  - COMPOSITE_PIPELINE: separate STT → LLM text → TTS pipeline (for providers without native voice)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any, AsyncIterator


class VoiceProviderType(StrEnum):
    GEMINI = "gemini"
    TWILIO = "twilio"


class VoiceStrategyType(StrEnum):
    NATIVE_MULTIMODAL = "native_multimodal"
    COMPOSITE_PIPELINE = "composite_pipeline"


@dataclass
class TranscriptionResult:
    success: bool
    text: str = ""
    confidence: float = 0.0
    language: str | None = None
    duration_seconds: float | None = None
    provider: str = ""
    segments: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass
class VoiceConfig:
    api_key: str
    language: str = "pt-BR"
    model: str | None = None
    sample_rate: int = 16000
    channels: int = 1


@dataclass
class VoiceStreamEvent:
    event_type: str
    data: bytes | None = None
    text: str | None = None
    role: str | None = None
    mime_type: str = "audio/pcm"
    is_final: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceSessionConfig:
    tenant_id: str
    session_id: str
    language: str = "pt-BR"
    system_prompt: str = ""
    voice_name: str = "Aoede"
    sample_rate: int = 16000
    max_duration_seconds: int = 1200
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceSessionMetrics:
    session_id: str
    provider: str
    strategy: str
    turn_count: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    total_audio_seconds: float = 0.0
    token_usage: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})


class VoiceProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def transcribe(self, audio_data: bytes, config: VoiceConfig | None = None) -> TranscriptionResult:
        pass

    @abstractmethod
    async def transcribe_url(self, audio_url: str, config: VoiceConfig | None = None) -> TranscriptionResult:
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        pass

    def is_configured(self) -> bool:
        return self.get_status().get("configured", False)


class VoiceStreamProviderABC(ABC):
    _provider_name: str = "base_stream"
    _strategy_type: VoiceStrategyType = VoiceStrategyType.NATIVE_MULTIMODAL

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def strategy_type(self) -> VoiceStrategyType:
        return self._strategy_type

    @abstractmethod
    async def is_available(self) -> bool:
        pass

    @abstractmethod
    async def create_session(self, config: VoiceSessionConfig) -> dict[str, Any]:
        pass

    @abstractmethod
    async def send_audio(self, session_id: str, audio_data: bytes) -> None:
        pass

    @abstractmethod
    async def send_text(self, session_id: str, text: str) -> None:
        pass

    @abstractmethod
    async def receive_events(self, session_id: str) -> AsyncIterator[VoiceStreamEvent]:
        pass

    @abstractmethod
    async def close_session(self, session_id: str) -> VoiceSessionMetrics:
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        pass
