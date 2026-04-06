"""
Voice Service - Speech-to-text and text-to-speech for LIA voice interactions.

Provides:
- Audio transcription using OpenAI Whisper
- Text-to-speech using OpenAI TTS API
- Real-time streaming transcription support
"""
import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any, Final, Optional

import httpx

logger = logging.getLogger(__name__)


class VoiceServiceError(Exception):
    """Base exception for voice service errors."""
    pass


class TranscriptionError(VoiceServiceError):
    """Error during audio transcription."""
    pass


class SynthesisError(VoiceServiceError):
    """Error during speech synthesis."""
    pass


class VoiceService:
    """
    Service for voice processing - speech-to-text and text-to-speech.
    
    Supports:
    - OpenAI Whisper for transcription
    - OpenAI TTS for speech synthesis
    - Multiple audio formats: mp3, wav, webm, m4a, ogg
    """
    
    OPENAI_TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"
    OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"
    
    SUPPORTED_AUDIO_FORMATS = ["mp3", "wav", "webm", "m4a", "ogg", "flac", "mpeg"]
    SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    SUPPORTED_TTS_MODELS = ["tts-1", "tts-1-hd"]
    
    def __init__(self):
        self.openai_api_key = (
            os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY") or 
            os.getenv("OPENAI_API_KEY")
        )
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _detect_audio_format(self, audio_data: bytes, filename: str | None = None) -> str:
        """Detect audio format from file header or filename."""
        if filename:
            ext = filename.lower().split(".")[-1]
            if ext in self.SUPPORTED_AUDIO_FORMATS:
                return ext
        
        if audio_data[:4] == b"RIFF":
            return "wav"
        if audio_data[:3] == b"ID3" or audio_data[:2] == b"\xff\xfb":
            return "mp3"
        if audio_data[:4] == b"fLaC":
            return "flac"
        if audio_data[:4] == b"OggS":
            return "ogg"
        if audio_data[4:8] == b"ftyp":
            return "m4a"
        if audio_data[:4] == b"\x1aE\xdf\xa3":
            return "webm"
        
        return "mp3"
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "pt-BR",
        model: str = "nova-2",
        filename: str | None = None
    ) -> dict[str, Any]:
        """
        Transcribe audio to text using OpenAI Whisper.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (e.g., "pt-BR", "en-US")
            model: Model to use (whisper-1, etc.)
            filename: Optional filename for format detection
            
        Returns:
            {
                "text": "transcribed text",
                "confidence": 0.95,
                "duration": 3.5,
                "words": [{"word": "olá", "start": 0.0, "end": 0.3}],
                "language": "pt-BR",
                "provider": "openai"
            }
            
        Raises:
            TranscriptionError: If transcription fails
        """
        if not audio_data:
            raise TranscriptionError("No audio data provided")
        
        if self.openai_api_key:
            try:
                return await self._transcribe_with_openai(
                    audio_data, language, filename
                )
            except Exception as e:
                logger.error(f"OpenAI transcription failed: {e}")
                raise TranscriptionError(f"Transcription failed: {e}")
        
        raise TranscriptionError(
            "No transcription provider available. Please configure OPENAI_API_KEY."
        )
    
    async def _transcribe_with_openai(
        self,
        audio_data: bytes,
        language: str,
        filename: str | None = None
    ) -> dict[str, Any]:
        """Transcribe using OpenAI Whisper API."""
        client = await self._get_client()
        
        audio_format = self._detect_audio_format(audio_data, filename)
        file_name = filename or f"audio.{audio_format}"
        
        language_code = language.split("-")[0]
        
        files = {
            "file": (file_name, audio_data, f"audio/{audio_format}"),
            "model": (None, "whisper-1"),
            "language": (None, language_code),
            "response_format": (None, "verbose_json"),
        }
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
        }
        
        response = await client.post(
            self.OPENAI_TRANSCRIPTION_URL,
            headers=headers,
            files=files
        )
        
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"OpenAI API error: {response.status_code} - {error_detail}")
            raise TranscriptionError(f"OpenAI API error: {response.status_code}")
        
        result = response.json()
        
        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info.get("word", "").strip(),
                    "start": word_info.get("start", 0.0),
                    "end": word_info.get("end", 0.0),
                    "confidence": 0.9
                })
        
        return {
            "text": result.get("text", ""),
            "confidence": 0.9,
            "duration": result.get("duration", 0.0),
            "words": words,
            "language": result.get("language", language_code),
            "provider": "openai"
        }
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "nova",
        speed: float = 1.0,
        model: str = "tts-1"
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS API.
        
        Args:
            text: Text to synthesize (max 4096 characters)
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            model: TTS model (tts-1 for speed, tts-1-hd for quality)
            
        Returns:
            Audio bytes in MP3 format
            
        Raises:
            SynthesisError: If synthesis fails
        """
        if not text:
            raise SynthesisError("No text provided for synthesis")
        
        if not self.openai_api_key:
            raise SynthesisError(
                "OpenAI API key not configured. Please set OPENAI_API_KEY or AI_INTEGRATIONS_OPENAI_API_KEY."
            )
        
        if len(text) > 4096:
            logger.warning(f"Text too long ({len(text)} chars), truncating to 4096")
            text = text[:4096]
        
        if voice not in self.SUPPORTED_VOICES:
            logger.warning(f"Unknown voice '{voice}', using 'nova'")
            voice = "nova"
        
        speed = max(0.25, min(4.0, speed))
        
        if model not in self.SUPPORTED_TTS_MODELS:
            model = "tts-1"
        
        client = await self._get_client()
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": "mp3"
        }
        
        response = await client.post(
            self.OPENAI_TTS_URL,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"OpenAI TTS API error: {response.status_code} - {error_detail}")
            raise SynthesisError(f"TTS API error: {response.status_code}")
        
        return response.content
    
    async def stream_transcription(
        self,
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream real-time transcription for live audio.
        
        Uses streaming API for low-latency
        real-time transcription.
        
        Args:
            audio_stream: Async generator yielding audio chunks
            
        Yields:
            Transcribed text fragments as they become available
            
        Note:
            Requires OPENAI_API_KEY. Falls back to buffered
            transcription if streaming is not available.
        """
        if not self.openai_api_key:
            buffer = bytearray()
            async for chunk in audio_stream:
                buffer.extend(chunk)
            
            if buffer:
                result = await self.transcribe_audio(bytes(buffer))
                yield result.get("text", "")
            return
        
        
        buffer = bytearray()
        last_transcript = ""
        
        async for chunk in audio_stream:
            buffer.extend(chunk)
            
            if len(buffer) >= 16000 * 2:
                try:
                    result = await self.transcribe_audio(bytes(buffer))
                    transcript = result.get("text", "")
                    
                    if transcript and transcript != last_transcript:
                        new_text = transcript[len(last_transcript):].strip()
                        if new_text:
                            yield new_text
                        last_transcript = transcript
                except Exception as e:
                    logger.warning(f"Streaming transcription error: {e}")
        
        if buffer:
            try:
                result = await self.transcribe_audio(bytes(buffer))
                transcript = result.get("text", "")
                if transcript and transcript != last_transcript:
                    yield transcript[len(last_transcript):].strip()
            except Exception as e:
                logger.warning(f"Final transcription error: {e}")
    
    def is_available(self) -> dict[str, bool]:
        """Check which voice services are available."""
        return {
            "transcription_openai": bool(self.openai_api_key),
            "synthesis_openai": bool(self.openai_api_key),
            "any_transcription": bool(self.openai_api_key),
            "any_synthesis": bool(self.openai_api_key)
        }


voice_service = VoiceService()
