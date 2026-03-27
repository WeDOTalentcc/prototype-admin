"""
Deepgram Transcription Service

Handles audio transcription for WhatsApp voice messages using Deepgram's Nova-2 model.
Cost: $0.0043/minute (cheapest STT option)
Free tier: 12,000 minutes/year

Use cases:
- WhatsApp voice message transcription
- Interview audio transcription
- Quick screening audio responses
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
import httpx
from pydantic import BaseModel

from tenacity import retry, stop_after_attempt, wait_exponential
from app.shared.resilience.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)


class TranscriptionResult(BaseModel):
    """Result from Deepgram transcription."""
    text: str
    confidence: float
    duration_seconds: float
    language: str
    words: Optional[List[Dict[str, Any]]] = None
    cost_estimate: Optional[float] = None
    is_error: bool = False
    error_message: Optional[str] = None
    error_type: Optional[str] = None


async def _deepgram_cb_fallback(self, audio_url, language="pt-BR", model="nova-2"):
    """Fallback retornado quando circuit breaker do Deepgram está aberto."""
    logger.warning("[CIRCUIT-BREAKER] Deepgram circuit aberto — retornando resultado de erro")
    return TranscriptionResult(
        text="",
        confidence=0.0,
        duration_seconds=0.0,
        language=language,
        is_error=True,
        error_type="circuit_open",
        error_message="Serviço Deepgram temporariamente indisponível (circuit breaker ativo)",
    )


class DeepgramService:
    """
    Service for audio transcription using Deepgram Nova-2.
    
    Deepgram Nova-2 is the best accuracy model for Portuguese (pt-BR).
    Cost: $0.0043/minute (pay-as-you-go)
    Free tier: 12,000 minutes/year
    
    API Docs: https://developers.deepgram.com/docs/getting-started-with-pre-recorded-audio
    """
    
    COST_PER_MINUTE = 0.0043
    
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.base_url = "https://api.deepgram.com/v1"
        
        if not self.api_key:
            logger.warning("⚠️  DEEPGRAM_API_KEY not configured - transcription will use mock data")
        else:
            logger.info("✅ Deepgram service initialized")
    
    @property
    def is_configured(self) -> bool:
        """Check if the service has valid API credentials."""
        return bool(self.api_key)
    
    @circuit_breaker("deepgram", failure_threshold=3, recovery_timeout=30.0, fallback=_deepgram_cb_fallback)
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))
    async def transcribe_audio_url(
        self,
        audio_url: str,
        language: str = "pt-BR",
        model: str = "nova-2"
    ) -> TranscriptionResult:
        """
        Transcribe audio from URL using Deepgram.
        
        Args:
            audio_url: URL of audio file (supports WhatsApp audio, S3, etc)
            language: Language code (default: pt-BR for Brazilian Portuguese)
            model: Deepgram model (default: nova-2 - best accuracy)
            
        Returns:
            TranscriptionResult with text and metadata, or error result on failure
        """
        if not self.api_key:
            logger.warning("Deepgram API key not configured, returning mock transcription")
            return self._create_mock_result(audio_url)
        
        logger.info(f"🎤 Transcribing audio from URL: {audio_url[:50]}...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/listen",
                    json={"url": audio_url},
                    headers={
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    params={
                        "model": model,
                        "language": language,
                        "punctuate": "true",
                        "diarize": "false",
                        "smart_format": "true"
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                
                data = response.json()
                return self._parse_response(data, language)
                
        except httpx.TimeoutException as e:
            logger.error(f"❌ Deepgram API timeout: {e}")
            return self._create_error_result(
                language=language,
                error_type="timeout",
                error_message=f"Transcription request timed out: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Deepgram API HTTP error: {e.response.status_code} - {e}")
            return self._create_error_result(
                language=language,
                error_type="http_error",
                error_message=f"API returned status {e.response.status_code}: {str(e)}"
            )
        except httpx.RequestError as e:
            logger.error(f"❌ Deepgram API request error: {e}")
            return self._create_error_result(
                language=language,
                error_type="network_error",
                error_message=f"Network error during transcription: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Unexpected Deepgram error: {e}")
            return self._create_error_result(
                language=language,
                error_type="unexpected_error",
                error_message=f"Unexpected error during transcription: {str(e)}"
            )
    
    async def transcribe_audio_bytes(
        self,
        audio_data: bytes,
        mimetype: str = "audio/ogg",
        language: str = "pt-BR",
        model: str = "nova-2"
    ) -> TranscriptionResult:
        """
        Transcribe audio from bytes (for uploaded files).
        
        Args:
            audio_data: Raw audio bytes
            mimetype: Audio MIME type (audio/ogg, audio/mp3, audio/wav, etc)
            language: Language code (default: pt-BR)
            model: Deepgram model (default: nova-2)
            
        Returns:
            TranscriptionResult with text and metadata, or error result on failure
        """
        if not self.api_key:
            logger.warning("Deepgram API key not configured, returning mock transcription")
            return self._create_mock_result_from_bytes(len(audio_data))
        
        logger.info(f"🎤 Transcribing {len(audio_data)} bytes of {mimetype} audio...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/listen",
                    content=audio_data,
                    headers={
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": mimetype
                    },
                    params={
                        "model": model,
                        "language": language,
                        "punctuate": "true",
                        "diarize": "false",
                        "smart_format": "true"
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                
                data = response.json()
                return self._parse_response(data, language)
                
        except httpx.TimeoutException as e:
            logger.error(f"❌ Deepgram API timeout: {e}")
            return self._create_error_result(
                language=language,
                error_type="timeout",
                error_message=f"Transcription request timed out: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Deepgram API HTTP error: {e.response.status_code} - {e}")
            return self._create_error_result(
                language=language,
                error_type="http_error",
                error_message=f"API returned status {e.response.status_code}: {str(e)}"
            )
        except httpx.RequestError as e:
            logger.error(f"❌ Deepgram API request error: {e}")
            return self._create_error_result(
                language=language,
                error_type="network_error",
                error_message=f"Network error during transcription: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Unexpected Deepgram error: {e}")
            return self._create_error_result(
                language=language,
                error_type="unexpected_error",
                error_message=f"Unexpected error during transcription: {str(e)}"
            )
    
    def _parse_response(self, data: Dict[str, Any], language: str) -> TranscriptionResult:
        """Parse Deepgram API response into TranscriptionResult."""
        results = data.get("results", {})
        channels = results.get("channels", [{}])
        
        if not channels:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                duration_seconds=0.0,
                language=language,
                words=None,
                cost_estimate=0.0
            )
        
        alternatives = channels[0].get("alternatives", [{}])
        if not alternatives:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                duration_seconds=0.0,
                language=language,
                words=None,
                cost_estimate=0.0
            )
        
        best_alternative = alternatives[0]
        transcript = best_alternative.get("transcript", "")
        confidence = best_alternative.get("confidence", 0.0)
        words = best_alternative.get("words", [])
        
        metadata = data.get("metadata", {})
        duration = metadata.get("duration", 0.0)
        
        cost = self.estimate_cost(duration)
        
        logger.info(f"✅ Transcription completed: {len(transcript)} chars, {duration:.1f}s, ${cost:.4f}")
        
        return TranscriptionResult(
            text=transcript,
            confidence=confidence,
            duration_seconds=duration,
            language=language,
            words=words if words else None,
            cost_estimate=cost
        )
    
    def _create_mock_result(self, audio_url: str) -> TranscriptionResult:
        """Create mock transcription result for testing without API key."""
        logger.info("📝 Creating mock transcription (no API key)")
        return TranscriptionResult(
            text="Então, no meu último projeto, trabalhei com Python para desenvolver uma API de processamento de pagamentos...",
            confidence=0.94,
            duration_seconds=45.0,
            language="pt-BR",
            words=None,
            cost_estimate=self.estimate_cost(45.0)
        )
    
    def _create_mock_result_from_bytes(self, data_size: int) -> TranscriptionResult:
        """Create mock transcription result from audio bytes."""
        estimated_duration = data_size / 16000
        logger.info(f"📝 Creating mock transcription for {data_size} bytes (no API key)")
        return TranscriptionResult(
            text="Então, no meu último projeto, trabalhei com Python para desenvolver uma API de processamento de pagamentos...",
            confidence=0.94,
            duration_seconds=estimated_duration,
            language="pt-BR",
            words=None,
            cost_estimate=self.estimate_cost(estimated_duration)
        )
    
    def _create_error_result(
        self,
        language: str,
        error_type: str,
        error_message: str
    ) -> TranscriptionResult:
        """
        Create an error result for graceful fallback when API is unavailable.
        
        Args:
            language: The language code that was requested
            error_type: Type of error (timeout, http_error, network_error, unexpected_error)
            error_message: Detailed error message for logging/debugging
            
        Returns:
            TranscriptionResult with is_error=True and error details
        """
        logger.warning(f"⚠️ Creating error result: {error_type} - {error_message}")
        return TranscriptionResult(
            text="",
            confidence=0.0,
            duration_seconds=0.0,
            language=language,
            words=None,
            cost_estimate=None,
            is_error=True,
            error_type=error_type,
            error_message=error_message
        )
    
    def estimate_cost(self, duration_seconds: float) -> float:
        """
        Estimate transcription cost based on duration.
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated cost in USD (based on $0.0043/min)
        """
        minutes = duration_seconds / 60
        return round(minutes * self.COST_PER_MINUTE, 4)


deepgram_service = DeepgramService()
