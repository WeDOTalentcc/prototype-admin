"""
Voice Screening Orchestrator — Twilio Voice + Gemini + TTS pipeline.

Connects:
- Twilio Programmable Voice (telephony, μ-law audio stream)
- Gemini Flash 2.5 (STT via WAV + conversational LLM)
- OpenAI TTS → μ-law transcoding (for Twilio Media Stream playback)
- WSI pipeline (transcript analysis and scoring)
- Consent management (LGPD compliance — hard-block on revoke, soft-warn on absent)
- PII Masking (before any logging or persistence)

Audio pipeline:
  Twilio → [raw μ-law 8kHz] → mulaw_to_wav() → [WAV] → Gemini STT → [text]
  Gemini LLM → [text] → OpenAI TTS → [MP3] → mp3_to_mulaw() → [μ-law] → Twilio

Compliance:
- LGPD Art. 7: Consentimento explícito verificado antes de iniciar ligação
- LGPD Art. 12 / SEG-3B: PII masked before logging
- Crença #4: Transparência — candidato informado sobre finalidade e duração
- LGPD absent consent → soft_warning logged, call proceeds
- LGPD revoked consent → ConsentNotGrantedError raised, call BLOCKED
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.shared.pii_masking import mask_pii
from app.domains.communication.services.twilio_voice_service import (
    mulaw_to_wav,
    mp3_to_mulaw,
    TwilioVoiceUnconfiguredError,
    twilio_voice_service as _twilio_voice_service,
)
from app.services.voice_service import VoiceService
from app.shared.resilience.circuit_breaker import TWILIO_VOICE_CIRCUIT, CircuitBreakerError

try:
    from app.services.gemini_voice_service import get_voice_service as _get_voice_service
except ImportError:
    _get_voice_service = None  # type: ignore[assignment]

try:
    from app.services.voice_screening_analysis import analyze_voice_screening as _analyze_voice_screening
except ImportError:
    _analyze_voice_screening = None  # type: ignore[assignment]

try:
    from app.services.consent_checker_service import ConsentCheckerService as _ConsentCheckerService
except ImportError:
    _ConsentCheckerService = None  # type: ignore[assignment]

try:
    from app.services.wsi_voice_orchestrator import WSIVoiceOrchestrator as _WSIVoiceOrchestrator
except ImportError:
    _WSIVoiceOrchestrator = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class VoiceScreeningSession:
    """State for an active voice screening call."""
    session_id: str
    candidate_id: str
    candidate_name: str
    job_title: str
    company_id: str
    phone_number: str
    job_id: Optional[str] = None
    call_sid: Optional[str] = None
    status: str = "pending"
    language: str = "pt-BR"
    transcript_segments: List[Dict[str, Any]] = field(default_factory=list)
    questions_asked: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    wsi_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    consent_verified: bool = False


class VoiceScreeningOrchestratorError(Exception):
    """Error during voice screening orchestration."""
    pass


class ConsentNotGrantedError(VoiceScreeningOrchestratorError):
    """Raised when candidate has not granted consent for voice screening."""
    pass


class VoiceScreeningOrchestrator:
    """
    Orchestrates the end-to-end voice screening pipeline.

    Flow:
    1. verify_consent() — check LGPD consent; BLOCK if revoked, warn if absent
    2. initiate_call() — start Twilio Voice call protected by TWILIO_VOICE_CIRCUIT
                         if Twilio unconfigured/circuit-open → status="fallback" (not mock)
    3. handle_audio_stream() — μ-law → WAV → Gemini STT → transcript
    4. generate_lia_response() — Gemini LLM drives conversation
    5. synthesize_lia_response() — OpenAI TTS → MP3 → μ-law for Twilio stream
    6. finalize_screening() — PII-masked transcript → WSI analysis → scores
    7. Fallback: circuit_open/unconfigured → status="fallback" → chat/WhatsApp

    Circuit breaker: TWILIO_VOICE_CIRCUIT
    """

    SCREENING_QUESTIONS_PT = [
        "Pode me contar brevemente sobre sua experiência profissional mais recente?",
        "Por que você tem interesse nessa posição?",
        "Quais são suas principais habilidades técnicas relevantes para essa vaga?",
        "Como você prefere trabalhar: em equipe ou de forma mais independente?",
        "Qual sua disponibilidade de início? Está aberto a mudanças ou trabalho remoto?",
    ]

    def __init__(self):
        self._sessions: Dict[str, VoiceScreeningSession] = {}
        self._tts_service = VoiceService()

    async def verify_consent(
        self,
        candidate_id: str,
        company_id: str,
        db=None,
    ) -> bool:
        """
        Verify LGPD consent before initiating voice call.

        LGPD Art. 7 + Crença #4: Prior explicit consent is MANDATORY for outbound calls.

        - Confirmed consent (allowed=True) → returns True, call proceeds
        - Absent consent (soft_warning)    → raises ConsentNotGrantedError (BLOCKED)
        - Revoked consent (allowed=False)  → raises ConsentNotGrantedError (BLOCKED)
        - No DB session provided           → raises ConsentNotGrantedError (BLOCKED)
        - ConsentCheckerService unavailable → raises ConsentNotGrantedError (BLOCKED)

        This is a hard-block: if we cannot confirm consent, the call is not placed.
        Outbound phone calls without confirmed consent violate LGPD Art. 7 and Lei 13.853/2019.

        Args:
            candidate_id: Candidate UUID
            company_id: Company UUID (tenant)
            db: SQLAlchemy async session. REQUIRED — without it, call is blocked.

        Returns:
            True only when explicit consent is confirmed

        Raises:
            ConsentNotGrantedError: If consent cannot be confirmed (any reason)
        """
        if db is None:
            logger.error(
                "[VOICE SCREENING] BLOCKED: No DB session provided — cannot verify consent "
                "for candidate %s. Outbound calls require confirmed LGPD consent (Art. 7).",
                mask_pii(candidate_id),
            )
            raise ConsentNotGrantedError(
                "Cannot verify LGPD consent: no database session provided. "
                "Outbound calls require confirmed prior consent (LGPD Art. 7)."
            )

        ConsentCheckerService = _ConsentCheckerService
        if ConsentCheckerService is None:
            logger.error(
                "[VOICE SCREENING] BLOCKED: ConsentCheckerService unavailable — cannot verify "
                "consent for candidate %s. Outbound calls require confirmed consent.",
                mask_pii(candidate_id),
            )
            raise ConsentNotGrantedError(
                "Cannot verify LGPD consent: ConsentCheckerService not available. "
                "Outbound calls require confirmed prior consent (LGPD Art. 7)."
            )

        try:
            checker = ConsentCheckerService(db)
            result = await checker.check_candidate_consent(
                candidate_id=candidate_id,
                company_id=company_id,
                purpose="ai_screening",
            )

            if not result.allowed:
                logger.warning(
                    "[VOICE SCREENING] BLOCKED: Consent REVOKED for candidate %s company=%s",
                    mask_pii(candidate_id),
                    company_id,
                )
                raise ConsentNotGrantedError(
                    "Candidate consent revoked for voice screening (LGPD Art. 18)"
                )

            if hasattr(result, "soft_warning") and result.soft_warning:
                logger.error(
                    "[VOICE SCREENING] BLOCKED: Consent ABSENT for candidate %s company=%s. "
                    "Outbound calls require confirmed prior consent — soft_warning is not sufficient.",
                    mask_pii(candidate_id),
                    company_id,
                )
                raise ConsentNotGrantedError(
                    "Candidate has not explicitly granted consent for voice screening. "
                    "Outbound calls require confirmed prior consent (LGPD Art. 7)."
                )

            logger.info(
                "[VOICE SCREENING] Consent CONFIRMED for candidate %s company=%s",
                mask_pii(candidate_id),
                company_id,
            )
            return True

        except ConsentNotGrantedError:
            raise
        except Exception as e:
            logger.error(
                "[VOICE SCREENING] BLOCKED: Consent check error for candidate %s: %s. "
                "Blocking call — cannot confirm consent.",
                mask_pii(candidate_id),
                e,
            )
            raise ConsentNotGrantedError(
                f"Consent check failed with error: {e}. "
                "Outbound calls blocked until consent is confirmed."
            )

    async def initiate_call(
        self,
        candidate_id: str,
        candidate_name: str,
        phone_number: str,
        job_title: str,
        company_id: str,
        job_id: Optional[str] = None,
        language: str = "pt-BR",
        db=None,
    ) -> VoiceScreeningSession:
        """
        Verify consent and initiate an outbound voice screening call.

        If Twilio is not configured or the circuit is open, the session is
        created with status='fallback' — callers must route to chat/WhatsApp.
        This is an explicit failure, NOT a transparent mock.

        Args:
            candidate_id: Candidate UUID
            candidate_name: Candidate's display name
            phone_number: Candidate's phone (with country code)
            job_title: Job title for screening context
            company_id: Company/tenant UUID
            job_id: Optional job vacancy UUID
            language: Conversation language (default: pt-BR)
            db: SQLAlchemy async session for consent check.
                When None, consent check is skipped (soft failure).

        Returns:
            VoiceScreeningSession. Check session.status:
            - 'initiated' → call placed successfully
            - 'fallback'  → Twilio unavailable, use chat/WhatsApp
            - 'failed'    → API error during call placement

        Raises:
            ConsentNotGrantedError: If consent has been explicitly revoked
        """
        await self.verify_consent(candidate_id, company_id, db)

        session = VoiceScreeningSession(
            session_id=str(uuid4()),
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_title=job_title,
            job_id=job_id,
            company_id=company_id,
            phone_number=phone_number,
            language=language,
            started_at=datetime.utcnow(),
            consent_verified=True,
        )

        try:
            call_result = await TWILIO_VOICE_CIRCUIT.call(
                _twilio_voice_service.make_call,
                to_phone=phone_number,
                candidate_name=candidate_name,
                job_title=job_title,
                session_id=session.session_id,
                language=language,
            )

            if call_result.get("success"):
                session.call_sid = call_result.get("call_sid")
                session.status = "initiated"
                logger.info(
                    "[VOICE SCREENING] Call initiated: session=%s call_sid=%s",
                    session.session_id,
                    session.call_sid,
                )
                if db is not None and session.call_sid:
                    await self._register_wsi_session(session, db)
            else:
                session.status = "failed"
                session.error = call_result.get("error", "Unknown Twilio error")
                logger.error(
                    "[VOICE SCREENING] Call failed: session=%s error=%s",
                    session.session_id,
                    session.error,
                )

        except TwilioVoiceUnconfiguredError as e:
            logger.warning(
                "[VOICE SCREENING] Twilio Voice not configured — returning 'fallback' status. "
                "session=%s Reason: %s",
                session.session_id,
                e,
            )
            session.status = "fallback"
            session.error = (
                "Twilio Voice not configured — use chat/WhatsApp fallback channel"
            )

        except CircuitBreakerError as e:
            logger.warning(
                "[VOICE SCREENING] TWILIO_VOICE_CIRCUIT open — returning 'fallback' status. "
                "session=%s retry_after=%.1fs",
                session.session_id,
                e.retry_after,
            )
            session.status = "fallback"
            session.error = (
                f"Twilio Voice circuit open (retry in {e.retry_after:.0f}s) — "
                "use chat/WhatsApp fallback"
            )

        except Exception as e:
            logger.error("[VOICE SCREENING] Unexpected call error: %s", e)
            session.status = "failed"
            session.error = str(e)

        self._sessions[session.session_id] = session
        return session

    async def process_audio_chunk(
        self,
        session_id: str,
        audio_data: bytes,
        mime_type: str = "audio/mulaw",
    ) -> Optional[str]:
        """
        Process an incoming audio chunk from Twilio's bidirectional Media Stream.

        Audio pipeline:
          raw μ-law bytes → WAV with RIFF header → Gemini STT → transcript text

        Twilio Media Streams deliver raw G.711 μ-law at 8kHz mono.
        Gemini requires a valid audio container (WAV). This method performs
        the transcoding before forwarding to STT.

        PII is masked before logging.

        Args:
            session_id: Active screening session ID
            audio_data: Raw μ-law bytes from Twilio WebSocket media event
            mime_type: Original MIME type hint (expected "audio/mulaw")

        Returns:
            Transcribed text segment, or None if insufficient audio/no speech
        """
        if not audio_data or len(audio_data) < 160:
            return None

        try:
            if _get_voice_service is None:
                logger.warning("[VOICE SCREENING] gemini_voice_service not available — skipping STT")
                return None

            wav_data = mulaw_to_wav(audio_data, sample_rate=8000)

            voice_svc = _get_voice_service()
            result = await voice_svc.transcribe_audio(
                audio_data=wav_data,
                mime_type="audio/wav",
                language=self._get_session_language(session_id),
            )

            text = result.get("text", "").strip()
            if text:
                masked_text = mask_pii(text)
                logger.debug(
                    "[VOICE SCREENING] STT segment session=%s: %s",
                    session_id,
                    masked_text[:100],
                )

                session = self._sessions.get(session_id)
                if session:
                    session.transcript_segments.append({
                        "text": text,
                        "timestamp": datetime.utcnow().isoformat(),
                        "role": "candidate",
                    })

            return text if text else None

        except Exception as e:
            logger.error(
                "[VOICE SCREENING] Audio processing error session=%s: %s",
                session_id,
                e,
            )
            return None

    async def generate_lia_response(
        self,
        session_id: str,
        candidate_utterance: str,
    ) -> str:
        """
        Generate LIA's next question/response using Gemini conversational LLM.

        Drives the screening conversation based on:
        - What the candidate said
        - Questions already asked
        - Job requirements context

        Falls back to scripted questions if Gemini is unavailable.

        Args:
            session_id: Active screening session ID
            candidate_utterance: What the candidate just said

        Returns:
            LIA's next response text (ready for TTS)
        """
        session = self._sessions.get(session_id)
        if not session:
            return "Desculpe, ocorreu um erro. Podemos encerrar a triagem."

        try:
            import os
            from google import genai
            from google.genai import types

            api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
            base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

            if not api_key or not base_url:
                return self._get_next_scripted_question(session)

            client = genai.Client(
                api_key=api_key,
                http_options={"api_version": "", "base_url": base_url},
            )

            questions_asked = session.questions_asked
            next_q_index = len(questions_asked)
            is_last = next_q_index >= len(self.SCREENING_QUESTIONS_PT) - 1

            system_prompt = (
                f"Você é LIA, assistente de recrutamento da WeDO Talent.\n"
                f"Você está conduzindo uma triagem por voz para a vaga de: {session.job_title}\n"
                f"Perguntas já feitas: {next_q_index} de {len(self.SCREENING_QUESTIONS_PT)}\n"
                f"{'Esta é a última pergunta da triagem.' if is_last else ''}\n\n"
                f"Instruções:\n"
                f"- Seja profissional, empático e conciso (respostas curtas para voz)\n"
                f"- Faça UMA pergunta por vez\n"
                f"- Valide brevemente o que o candidato disse antes da próxima pergunta\n"
                f"- Língua: {session.language}"
            )

            conversation_history = []
            for seg in session.transcript_segments[-6:]:
                role = "user" if seg.get("role") == "candidate" else "model"
                conversation_history.append(
                    types.Content(role=role, parts=[types.Part(text=seg["text"])])
                )

            if not conversation_history or conversation_history[-1].role != "user":
                conversation_history.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=candidate_utterance)],
                    )
                )

            if is_last:
                next_prompt = "Agradeça ao candidato e encerre a triagem de forma cordial."
            else:
                next_q = self.SCREENING_QUESTIONS_PT[next_q_index]
                next_prompt = f"Responda brevemente e faça esta pergunta: {next_q}"

            conversation_history.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=f"[INSTRUÇÃO]: {next_prompt}")],
                )
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=conversation_history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=200,
                ),
            )

            lia_text = response.text.strip() if response.text else ""

            if lia_text:
                if not is_last and next_q_index < len(self.SCREENING_QUESTIONS_PT):
                    session.questions_asked.append(self.SCREENING_QUESTIONS_PT[next_q_index])

                session.transcript_segments.append({
                    "text": lia_text,
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "lia",
                })

            return lia_text or self._get_next_scripted_question(session)

        except Exception as e:
            logger.error(
                "[VOICE SCREENING] Gemini response generation failed session=%s: %s",
                session_id,
                e,
            )
            return self._get_next_scripted_question(session)

    def _get_next_scripted_question(self, session: VoiceScreeningSession) -> str:
        """Fallback: return next scripted question if Gemini unavailable."""
        asked = len(session.questions_asked)
        if asked < len(self.SCREENING_QUESTIONS_PT):
            q = self.SCREENING_QUESTIONS_PT[asked]
            session.questions_asked.append(q)
            session.transcript_segments.append({
                "text": q,
                "timestamp": datetime.utcnow().isoformat(),
                "role": "lia",
            })
            return q
        return (
            "Muito obrigada pela sua participação! Encerramos a triagem por aqui. "
            "Nossa equipe entrará em contato em breve. Tenha um ótimo dia!"
        )

    async def synthesize_lia_response(
        self,
        text: str,
        voice: str = "nova",
        for_twilio_stream: bool = True,
    ) -> Optional[bytes]:
        """
        Convert LIA's response text to audio for Twilio Media Stream playback.

        Audio pipeline:
          text → OpenAI TTS → MP3 → mp3_to_mulaw() → raw μ-law 8kHz → Twilio

        Twilio bidirectional Media Streams require raw μ-law/PCM payload;
        MP3 is transcoded via pydub. If transcoding is unavailable, None is
        returned and caller should use TwiML <Say> instead of streaming.

        Args:
            text: LIA response text to synthesize
            voice: OpenAI TTS voice name
            for_twilio_stream: If True, returns μ-law bytes for Twilio stream.
                               If False, returns MP3 bytes for other uses.

        Returns:
            Audio bytes (μ-law for Twilio stream, MP3 otherwise), or None if
            synthesis or transcoding fails.
        """
        try:
            audio_mp3 = await self._tts_service.synthesize_speech(
                text=text,
                voice=voice,
                speed=1.0,
                model="tts-1",
            )

            if not for_twilio_stream:
                return audio_mp3

            mulaw_bytes = mp3_to_mulaw(audio_mp3)
            if mulaw_bytes is None:
                logger.warning(
                    "[VOICE SCREENING] TTS→μ-law transcoding unavailable — "
                    "caller should use TwiML <Say> as fallback"
                )
            return mulaw_bytes

        except Exception as e:
            logger.warning("[VOICE SCREENING] TTS synthesis failed (non-blocking): %s", e)
            return None

    async def finalize_screening(
        self,
        session_id: str,
        db=None,
    ) -> Dict[str, Any]:
        """
        Finalize screening session: run WSI analysis on full transcript.

        - Merges all transcript segments into full transcript
        - Applies PII masking before logging/storage (LGPD Art. 12)
        - Runs WSI voice analysis pipeline (analyze_voice_screening)
        - Updates session status

        Args:
            session_id: Screening session ID
            db: SQLAlchemy async session (optional — for WSI persistence)

        Returns:
            Analysis result dict with WSI scores and recommendation
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.error("[VOICE SCREENING] Session not found: %s", session_id)
            return {"error": "Session not found", "session_id": session_id}

        session.ended_at = datetime.utcnow()
        session.status = "analyzing"

        full_transcript = "\n".join(
            f"{'CANDIDATO' if seg.get('role') == 'candidate' else 'LIA'}: {seg['text']}"
            for seg in session.transcript_segments
        )

        masked_transcript = mask_pii(full_transcript)
        logger.info(
            "[VOICE SCREENING] Finalizing session=%s transcript_chars=%d",
            session_id,
            len(full_transcript),
        )

        duration_seconds = None
        if session.started_at and session.ended_at:
            duration_seconds = int(
                (session.ended_at - session.started_at).total_seconds()
            )

        masked_segments = self._mask_transcript_segments(session.transcript_segments)

        try:
            wsi_result = None

            if _WSIVoiceOrchestrator is not None and session.call_sid:
                try:
                    wsi_orch = _WSIVoiceOrchestrator()
                    wsi_result = await wsi_orch.process_call_completed(
                        call_id=session.call_sid,
                        transcript=masked_transcript,
                        transcript_object=masked_segments,
                        db=db,
                    )
                    if wsi_result is not None:
                        logger.info(
                            "[VOICE SCREENING] WSI pipeline analysis complete session=%s via wsi_voice_orchestrator",
                            session_id,
                        )
                except Exception as wsi_err:
                    logger.warning(
                        "[VOICE SCREENING] wsi_voice_orchestrator failed (session=%s), "
                        "falling back to analyze_voice_screening: %s",
                        session_id,
                        wsi_err,
                    )

            if wsi_result is None:
                analyze_fn = _analyze_voice_screening
                if analyze_fn is None:
                    raise ImportError("Neither wsi_voice_orchestrator nor analyze_voice_screening available")

                wsi_result = await analyze_fn(
                    transcript=masked_transcript,
                    transcript_object=masked_segments,
                    job_title=session.job_title,
                    candidate_name=None,
                    duration_seconds=duration_seconds,
                )
                logger.info(
                    "[VOICE SCREENING] Standalone LLM analysis complete session=%s",
                    session_id,
                )

            if wsi_result is None:
                raise RuntimeError("Both WSI pipeline and standalone analysis returned None")

            score = (
                wsi_result.get("overall_evaluation", {}).get("overall_score", "?")
                if isinstance(wsi_result, dict)
                else "?"
            )
            session.wsi_result = wsi_result if isinstance(wsi_result, dict) else wsi_result.dict() if hasattr(wsi_result, "dict") else str(wsi_result)
            session.status = "completed"

            logger.info(
                "[VOICE SCREENING] Analysis complete session=%s score=%s",
                session_id,
                score,
            )

            return {
                "session_id": session_id,
                "status": "completed",
                "duration_seconds": duration_seconds,
                "transcript_length": len(full_transcript),
                "wsi_result": session.wsi_result,
                "provider": "twilio_voice_gemini",
            }

        except Exception as e:
            logger.error(
                "[VOICE SCREENING] WSI analysis failed session=%s: %s", session_id, e
            )
            session.status = "analysis_failed"
            session.error = str(e)
            return {
                "session_id": session_id,
                "status": "analysis_failed",
                "error": str(e),
                "transcript_length": len(full_transcript),
            }

    def get_session(self, session_id: str) -> Optional[VoiceScreeningSession]:
        """Get an active screening session by ID."""
        return self._sessions.get(session_id)

    def _get_session_language(self, session_id: str) -> str:
        session = self._sessions.get(session_id)
        return session.language if session else "pt-BR"

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active (non-completed) screening sessions."""
        return [
            {
                "session_id": s.session_id,
                "candidate_name": mask_pii(s.candidate_name),
                "job_title": s.job_title,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in self._sessions.values()
            if s.status not in ("completed", "failed")
        ]

    async def _register_wsi_session(
        self,
        session: VoiceScreeningSession,
        db,
    ) -> None:
        """
        Register Twilio call in wsi_sessions table using call_sid as call_id.

        This enables wsi_voice_orchestrator.process_call_completed() to find
        the session by Twilio call_sid during finalization, making the WSI
        pipeline the primary analysis path (not a fallback).

        Schema: wsi_sessions(id, candidate_id, job_vacancy_id, mode, call_id, status)
        """
        try:
            from sqlalchemy import text

            await db.execute(
                text("""
                    INSERT INTO wsi_sessions (id, candidate_id, job_vacancy_id, mode, call_id, status, created_at, updated_at)
                    VALUES (:id, :candidate_id, :job_vacancy_id, :mode, :call_id, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE
                        SET call_id = :call_id, status = :status, updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "id": session.session_id,
                    "candidate_id": session.candidate_id,
                    "job_vacancy_id": session.job_id or session.session_id,
                    "mode": "compact",
                    "call_id": session.call_sid,
                    "status": "in_progress",
                },
            )
            await db.commit()
            logger.info(
                "[VOICE SCREENING] WSI session registered: session=%s call_sid=%s",
                session.session_id,
                session.call_sid,
            )
        except Exception as e:
            logger.warning(
                "[VOICE SCREENING] Failed to register WSI session (non-blocking): %s", e
            )

    @staticmethod
    def _mask_transcript_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return a copy of transcript_segments with PII masked in text fields.

        Ensures no unmasked PII reaches WSI persistence layer (LGPD Art. 12 / SEG-3B).
        """
        masked = []
        for seg in segments:
            masked.append({
                **seg,
                "text": mask_pii(seg.get("text", "")),
            })
        return masked


voice_screening_orchestrator = VoiceScreeningOrchestrator()
