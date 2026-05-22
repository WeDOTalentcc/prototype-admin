"""
Voice Service - Speech-to-text and text-to-speech for LIA voice interactions.

Provides:
- Audio transcription using OpenAI Whisper
- Text-to-speech using OpenAI TTS API
- Real-time streaming transcription support

P1.AIC2 (2026-05-22): migrated from raw httpx → openai.AsyncOpenAI SDK so the
ai_credit_gate fires transitively. Whisper STT and TTS use a per-minute /
per-char price model distinct from chat-completion tokens; the bootstrap
patches `audio.transcriptions.create` + `audio.speech.create` and derives a
duration / char-count estimate directly from the SDK call kwargs so the
caller doesn't need a special API.
"""
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

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

    SUPPORTED_AUDIO_FORMATS = ["mp3", "wav", "webm", "m4a", "ogg", "flac", "mpeg"]
    SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    SUPPORTED_TTS_MODELS = ["tts-1", "tts-1-hd"]

    def __init__(self):
        self.openai_api_key = (
            os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        # Lazy SDK client construction — let llm_bootstrap install before
        # the first instantiation.
        self._client = None

    async def _get_client(self):
        """Lazy-build AsyncOpenAI (bootstrap gates audio.transcriptions.create
        and audio.speech.create after Wave 4 monkey-patch extension)."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.openai_api_key)
        return self._client

    async def close(self):
        """Compatibility shim — SDK manages its own connection pool."""
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
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
        Transcribe audio to text using OpenAI Whisper via openai.AsyncOpenAI SDK.

        P1.AIC2: gate transitive via llm_bootstrap monkey-patch on
        AsyncOpenAI.audio.transcriptions.create.

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
                from app.shared.services.ai_credit_gate import AICreditExhausted
                if isinstance(e, AICreditExhausted):
                    raise
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
        """Transcribe using OpenAI Whisper via AsyncOpenAI SDK."""
        client = await self._get_client()

        audio_format = self._detect_audio_format(audio_data, filename)
        file_name = filename or f"audio.{audio_format}"

        language_code = language.split("-")[0]

        # SDK expects a file-tuple (filename, bytes, mime_type). The bootstrap
        # audio gate reads this tuple's byte length to derive a duration
        # estimate.
        file_tuple = (file_name, audio_data, f"audio/{audio_format}")

        # Defense-in-depth: gate inline so tests with mocked SDK clients still
        # exercise the credit ledger. The bootstrap monkey-patch on the real
        # AsyncOpenAI is the PRIMARY enforcement in production; this call is a
        # parallel gate using the same check_credit_budget helper.
        await _credit_gate_audio_transcription(audio_data)

        response = await client.audio.transcriptions.create(
            file=file_tuple,
            model="whisper-1",
            language=language_code,
            response_format="verbose_json",
        )

        # SDK returns a parsed Transcription object; verbose_json gives us
        # segments[].words[].
        try:
            payload = response.model_dump()
        except Exception:
            payload = {
                "text": getattr(response, "text", ""),
                "duration": getattr(response, "duration", 0.0),
                "language": getattr(response, "language", language_code),
                "segments": getattr(response, "segments", []) or [],
            }

        words = []
        for segment in payload.get("segments", []) or []:
            for word_info in (segment.get("words") or []):
                words.append({
                    "word": (word_info.get("word") or "").strip(),
                    "start": word_info.get("start", 0.0),
                    "end": word_info.get("end", 0.0),
                    "confidence": 0.9,
                })

        return {
            "text": payload.get("text", "") or "",
            "confidence": 0.9,
            "duration": payload.get("duration", 0.0),
            "words": words,
            "language": payload.get("language", language_code),
            "provider": "openai",
        }

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "nova",
        speed: float = 1.0,
        model: str = "tts-1"
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS API via openai.AsyncOpenAI SDK.

        P1.AIC2: gate transitive via llm_bootstrap monkey-patch on
        AsyncOpenAI.audio.speech.create.

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

        # Defense-in-depth: gate inline (see _transcribe_with_openai).
        await _credit_gate_audio_speech(text)

        try:
            response = await client.audio.speech.create(
                model=model,
                input=text,
                voice=voice,
                speed=speed,
                response_format="mp3",
            )

            # SDK returns a streaming response wrapper; `.read()` materializes
            # bytes (async). Fall back to attribute access for older shapes.
            if hasattr(response, "read"):
                content = await response.read()
            elif hasattr(response, "content"):
                content = response.content
            else:
                content = bytes(response)  # last-ditch coercion

            return content

        except Exception as e:
            from app.shared.services.ai_credit_gate import AICreditExhausted
            if isinstance(e, AICreditExhausted):
                raise
            logger.error(f"OpenAI TTS error: {e}")
            raise SynthesisError(f"TTS failed: {e}")

    async def stream_transcription(
        self,
        audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream real-time transcription for live audio.

        Note:
            Each chunk transcription goes through transcribe_audio → SDK →
            credit gate. So buffered chunks are gated individually.
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


# ----------------------------------------------------------------------
# Inline credit-gate helpers (P1.AIC2 defense-in-depth, 2026-05-22)
# ----------------------------------------------------------------------
# These mirror the budget-projection logic in
# `app.shared.llm_bootstrap._patch_openai_audio` so the service-level
# code path is also gated. Mocked-SDK contract tests rely on this.

async def _credit_gate_audio_transcription(audio_data: bytes) -> None:
    """Project a Whisper budget hit and call check_credit_budget.

    AICreditExhausted bubbles up unchanged. Other errors fail-safe ALLOW.
    """
    from app.middleware.auth_enforcement import _current_company_id
    from app.shared.services.ai_credit_gate import (
        AICreditExhausted,
        check_credit_budget,
    )

    company_id = _current_company_id.get("")
    if not company_id:
        return

    duration_seconds = float(len(audio_data)) / 12000.0  # 96kbps heuristic
    estimated_tokens = int(round((duration_seconds / 60.0) * 2000))

    try:
        from lia_config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await check_credit_budget(
                db,
                company_id,
                estimated_tokens=estimated_tokens,
                service="voice_whisper",
            )
    except AICreditExhausted:
        raise
    except Exception as exc:
        logger.warning(
            "[VoiceService] inline whisper credit gate fail-safe ALLOW: %s",
            exc,
        )


async def _credit_gate_audio_speech(text: str) -> None:
    """Project a TTS budget hit and call check_credit_budget."""
    from app.middleware.auth_enforcement import _current_company_id
    from app.shared.services.ai_credit_gate import (
        AICreditExhausted,
        check_credit_budget,
    )

    company_id = _current_company_id.get("")
    if not company_id:
        return

    estimated_tokens = int(len(text or "") * 5)

    try:
        from lia_config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await check_credit_budget(
                db,
                company_id,
                estimated_tokens=estimated_tokens,
                service="voice_tts",
            )
    except AICreditExhausted:
        raise
    except Exception as exc:
        logger.warning(
            "[VoiceService] inline tts credit gate fail-safe ALLOW: %s",
            exc,
        )
