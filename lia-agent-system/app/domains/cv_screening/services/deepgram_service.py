"""
Deepgram STT Service for CV Screening triagem voice flow.

Wraps the shared VoiceService to provide domain-specific transcription
for candidate audio responses during WSI triagem sessions.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DeepgramTriagemService:
    """
    Domain-level Deepgram service for triagem audio transcription.

    Delegates to the shared VoiceService but adds triagem-specific
    defaults (pt-BR, nova-2 model) and structured result formatting.
    """

    def __init__(self):
        self._voice_service = None

    @property
    def voice_service(self):
        if self._voice_service is None:
            from app.services.voice_service import voice_service
            self._voice_service = voice_service
        return self._voice_service

    async def transcribe_candidate_audio(
        self,
        audio_data: bytes,
        session_token: str,
        question_index: Optional[int] = None,
        language: str = "pt-BR",
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe a candidate's audio response during triagem.

        Args:
            audio_data: Raw audio bytes from the candidate's recording
            session_token: Triagem session token for logging
            question_index: Current question number (optional)
            language: Language code (default pt-BR)
            filename: Optional filename for format detection

        Returns:
            {
                "text": "transcribed text",
                "confidence": 0.95,
                "duration": 3.5,
                "provider": "deepgram" | "openai",
                "language": "pt-BR",
                "words": [...],
                "session_token": "...",
                "question_index": 2,
            }
        """
        if not audio_data:
            logger.warning(
                "[DeepgramTriagemService] Empty audio for session=%s q=%s",
                session_token, question_index,
            )
            return {
                "text": "",
                "confidence": 0.0,
                "duration": 0.0,
                "provider": "none",
                "error": "empty_audio",
            }

        try:
            result = await self.voice_service.transcribe_audio(
                audio_data=audio_data,
                language=language,
                model="nova-2",
                filename=filename,
            )

            result["session_token"] = session_token
            if question_index is not None:
                result["question_index"] = question_index

            logger.info(
                "[DeepgramTriagemService] Transcribed session=%s q=%s "
                "provider=%s confidence=%.2f duration=%.1fs text_len=%d",
                session_token,
                question_index,
                result.get("provider", "?"),
                result.get("confidence", 0),
                result.get("duration", 0),
                len(result.get("text", "")),
            )
            return result

        except Exception as e:
            logger.error(
                "[DeepgramTriagemService] Transcription failed session=%s: %s",
                session_token, e,
                exc_info=True,
            )
            return {
                "text": "",
                "confidence": 0.0,
                "duration": 0.0,
                "provider": "none",
                "error": str(e),
                "session_token": session_token,
            }

    def is_available(self) -> bool:
        availability = self.voice_service.is_available()
        return availability.get("any_transcription", False)


deepgram_triagem_service = DeepgramTriagemService()
