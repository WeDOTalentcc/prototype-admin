"""
Deepgram Speech-to-Text (STT) Service.

Provides real-time and batch audio transcription via Deepgram API.
Integrated with circuit breaker pattern for production resilience.

Supported languages: pt-BR (default), en-US
Supported models: nova-2 (default), base, enhanced
"""
import logging
import os
from typing import Any

import httpx

from app.shared.resilience.circuit_breaker import DEEPGRAM_CIRCUIT, CircuitBreakerError

logger = logging.getLogger(__name__)


class DeepgramError(Exception):
    """Raised when Deepgram API call fails."""


class DeepgramUnconfiguredError(DeepgramError):
    """Raised when DEEPGRAM_API_KEY is not set."""


class DeepgramService:
    """
    Deepgram STT service with circuit breaker protection.

    Usage:
        result = await deepgram_service.transcribe(audio_bytes, mime_type="audio/wav")
        transcript = result["transcript"]
        confidence = result["confidence"]
    """

    DEEPGRAM_BASE_URL = "https://api.deepgram.com/v1"

    def __init__(self) -> None:
        self._api_key: str | None = None

    def _get_api_key(self) -> str:
        if self._api_key:
            return self._api_key
        key = os.getenv("DEEPGRAM_API_KEY")
        if not key:
            raise DeepgramUnconfiguredError(
                "DEEPGRAM_API_KEY env var is not set. "
                "Configure it to enable Deepgram STT transcription."
            )
        self._api_key = key
        return key

    def is_configured(self) -> bool:
        """Return True if DEEPGRAM_API_KEY is present."""
        return bool(os.getenv("DEEPGRAM_API_KEY"))

    async def transcribe(
        self,
        audio_data: bytes,
        mime_type: str = "audio/wav",
        language: str = "pt-BR",
        model: str = "nova-2",
        punctuate: bool = True,
        diarize: bool = False,
        smart_format: bool = True,
    ) -> dict[str, Any]:
        """
        Transcribe audio bytes using Deepgram nova-2 model.

        Args:
            audio_data: Raw audio bytes.
            mime_type: Audio MIME type (audio/wav, audio/mp3, audio/ogg, etc.).
            language: BCP-47 language code — pt-BR or en-US.
            model: Deepgram model name.
            punctuate: Auto-punctuate transcript.
            diarize: Enable speaker diarization.
            smart_format: Apply smart formatting (numbers, dates, etc.).

        Returns:
            Dict with keys: transcript, confidence, words, duration_seconds, language.

        Raises:
            DeepgramUnconfiguredError: API key not configured.
            DeepgramError: API call failed.
            CircuitBreakerError: Circuit is open.
        """
        async def _call() -> dict[str, Any]:
            api_key = self._get_api_key()

            params = {
                "model": model,
                "language": language,
                "punctuate": "true" if punctuate else "false",
                "diarize": "true" if diarize else "false",
                "smart_format": "true" if smart_format else "false",
            }

            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": mime_type,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.DEEPGRAM_BASE_URL}/listen",
                    content=audio_data,
                    headers=headers,
                    params=params,
                )

            if response.status_code != 200:
                raise DeepgramError(
                    f"Deepgram API returned {response.status_code}: {response.text[:200]}"
                )

            data = response.json()
            results = data.get("results", {})
            channels = results.get("channels", [{}])
            channel = channels[0] if channels else {}
            alternatives = channel.get("alternatives", [{}])
            best = alternatives[0] if alternatives else {}

            transcript = best.get("transcript", "")
            confidence = best.get("confidence", 0.0)
            words = best.get("words", [])

            metadata = data.get("metadata", {})
            duration = metadata.get("duration", 0.0)

            logger.info(
                "[Deepgram] Transcription complete — chars=%d confidence=%.2f duration=%.1fs lang=%s",
                len(transcript),
                confidence,
                duration,
                language,
            )

            return {
                "transcript": transcript,
                "confidence": confidence,
                "words": words,
                "duration_seconds": duration,
                "language": language,
                "model": model,
                "provider": "deepgram",
            }

        return await DEEPGRAM_CIRCUIT.call(_call)

    async def health_check(self) -> dict[str, Any]:
        """
        Validate Deepgram configuration (key presence only — no API call).

        Returns:
            Dict with status, configured, circuit_state.
        """
        configured = self.is_configured()
        circuit_state = DEEPGRAM_CIRCUIT.state.value

        return {
            "service": "deepgram",
            "provider": "Deepgram STT",
            "configured": configured,
            "circuit_state": circuit_state,
            "status": "healthy" if (configured and circuit_state != "open") else "degraded",
            "languages_supported": ["pt-BR", "en-US"],
            "model": "nova-2",
        }


deepgram_service = DeepgramService()
