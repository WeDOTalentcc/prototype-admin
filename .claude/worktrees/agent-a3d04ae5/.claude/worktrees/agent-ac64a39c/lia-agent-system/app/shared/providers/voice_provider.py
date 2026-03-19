"""
Voice Provider Abstract Interface

Defines a common interface for voice/transcription providers (Deepgram, OpenMic, Gemini).
Concrete implementations wrap specific provider SDKs while exposing a unified API.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class VoiceProviderType(str, Enum):
    DEEPGRAM = "deepgram"
    OPENMIC = "openmic"
    GEMINI = "gemini"


@dataclass
class TranscriptionResult:
    success: bool
    text: str = ""
    confidence: float = 0.0
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    provider: str = ""
    segments: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class VoiceConfig:
    api_key: str
    language: str = "pt-BR"
    model: Optional[str] = None
    sample_rate: int = 16000
    channels: int = 1


class VoiceProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def transcribe(self, audio_data: bytes, config: Optional[VoiceConfig] = None) -> TranscriptionResult:
        pass

    @abstractmethod
    async def transcribe_url(self, audio_url: str, config: Optional[VoiceConfig] = None) -> TranscriptionResult:
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass

    def is_configured(self) -> bool:
        return self.get_status().get("configured", False)
