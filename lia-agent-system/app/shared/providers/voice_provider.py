"""
Voice Provider Abstract Interface

Defines a common interface for voice/transcription providers (Gemini, Twilio).
Concrete implementations wrap specific provider SDKs while exposing a unified API.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VoiceProviderType(str, Enum):
    GEMINI = "gemini"
    TWILIO = "twilio"


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
