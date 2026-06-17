"""
Voice Service for CV Screening triagem — OpenAI TTS for question narration.

Wraps the shared VoiceService to provide domain-specific text-to-speech
for LIA's triagem questions, enabling voice-mode interviews.
"""
import base64
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "nova"
DEFAULT_SPEED = 1.0
DEFAULT_MODEL = "tts-1"


class TriagemVoiceService:
    """
    Domain-level TTS service for triagem voice mode.

    Generates MP3 audio for LIA's questions so candidates can listen
    instead of (or in addition to) reading.
    """

    def __init__(self):
        self._voice_service = None

    @property
    def voice_service(self):
        if self._voice_service is None:
            from app.shared.services.voice_service import voice_service
            self._voice_service = voice_service
        return self._voice_service

    async def synthesize_question(
        self,
        text: str,
        session_token: str,
        question_index: int | None = None,
        voice: str = DEFAULT_VOICE,
        speed: float = DEFAULT_SPEED,
    ) -> dict[str, Any]:
        """
        Generate TTS audio for a triagem question.

        Args:
            text: Question text to synthesize
            session_token: Triagem session token for logging
            question_index: Current question number (optional)
            voice: OpenAI TTS voice (default: nova)
            speed: Speech speed 0.25–4.0 (default: 1.0)

        Returns:
            {
                "audio_base64": "base64-encoded MP3",
                "content_type": "audio/mpeg",
                "text_length": 120,
                "session_token": "...",
                "question_index": 2,
            }
        """
        if not text:
            return {
                "audio_base64": "",
                "content_type": "audio/mpeg",
                "text_length": 0,
                "error": "empty_text",
            }

        try:
            audio_bytes = await self.voice_service.synthesize_speech(
                text=text,
                voice=voice,
                speed=speed,
                model=DEFAULT_MODEL,
            )

            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

            logger.info(
                "[TriagemVoiceService] Synthesized session=%s q=%s "
                "voice=%s text_len=%d audio_bytes=%d",
                session_token,
                question_index,
                voice,
                len(text),
                len(audio_bytes),
            )

            return {
                "audio_base64": audio_b64,
                "content_type": "audio/mpeg",
                "text_length": len(text),
                "session_token": session_token,
                "question_index": question_index,
            }

        except Exception as e:
            logger.error(
                "[TriagemVoiceService] Synthesis failed session=%s: %s",
                session_token, e,
                exc_info=True,
            )
            return {
                "audio_base64": "",
                "content_type": "audio/mpeg",
                "text_length": len(text),
                "error": str(e),
            }

    def is_available(self) -> bool:
        availability = self.voice_service.is_available()
        return availability.get("any_synthesis", False)


triagem_voice_service = TriagemVoiceService()
