"""
VoiceInterviewStateMachine — controls the flow of a voice screening interview.

States: INTRO → QUESTIONING → SCORING → CLOSING → DONE

For Talent Pool context only (in jobs, the existing screening agent handles this).
Uses WSI Compact Pipeline questions from the pool's archetype.

Integrates with:
  - Whisper (local) or GeminiVoiceService (Replit) for STT
  - LLM (Haiku tier) for scoring answers vs ideal_answer
  - notification_service for recruiter alerts

Apply to: lia-agent-system/app/services/voice_interview_state_machine.py
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class InterviewState(Enum):
    INTRO = "intro"
    QUESTIONING = "questioning"
    SCORING = "scoring"
    CLOSING = "closing"
    DONE = "done"


@dataclass
class ScreeningQuestion:
    question_id: str
    text: str
    ideal_answer: str
    weight: float
    competency: str  # technical, behavioral, logistical
    max_duration_s: int = 90


@dataclass
class VoiceInterviewSession:
    session_id: str
    company_id: str
    talent_pool_id: str
    candidate_id: str
    candidate_name: str
    questions: list[ScreeningQuestion]
    channel: str = "web"  # web, whatsapp, phone
    language: str = "pt-BR"

    state: InterviewState = InterviewState.INTRO
    current_q_idx: int = 0
    answers: dict[str, str] = field(default_factory=dict)      # q_id → transcription
    scores: dict[str, float] = field(default_factory=dict)     # q_id → score 0-100
    final_score: Optional[float] = None
    duration_secs: int = 0

    @property
    def is_complete(self) -> bool:
        return self.state == InterviewState.DONE

    @property
    def progress(self) -> float:
        if not self.questions:
            return 0.0
        return round(self.current_q_idx / len(self.questions), 2)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "company_id": self.company_id,
            "talent_pool_id": self.talent_pool_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "channel": self.channel,
            "state": self.state.value,
            "current_q_idx": self.current_q_idx,
            "total_questions": len(self.questions),
            "progress": self.progress,
            "answers": self.answers,
            "scores": self.scores,
            "final_score": self.final_score,
            "duration_secs": self.duration_secs,
        }

    @classmethod
    def from_pool_questions(
        cls,
        company_id: str,
        talent_pool_id: str,
        candidate_id: str,
        candidate_name: str,
        screening_questions: list[dict],
        channel: str = "web",
    ) -> "VoiceInterviewSession":
        """Create session from pool's screening_questions JSONB."""
        questions = [
            ScreeningQuestion(
                question_id=f"q_{i}",
                text=q["question"],
                ideal_answer=q.get("ideal_answer", ""),
                weight=float(q.get("weight", 1.0 / max(len(screening_questions), 1))),
                competency=q.get("competency", "technical"),
            )
            for i, q in enumerate(screening_questions)
        ]
        return cls(
            session_id=str(uuid.uuid4()),
            company_id=company_id,
            talent_pool_id=talent_pool_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            questions=questions,
            channel=channel,
        )


class VoiceInterviewStateMachine:
    """
    Processes audio input from the candidate and advances through interview states.

    Each call to handle_audio_input():
    1. Transcribes audio (STT)
    2. Processes based on current state
    3. Returns agent response text + state info
    """

    async def handle_audio_input(
        self,
        session: VoiceInterviewSession,
        audio_bytes: bytes,
        audio_format: str = "audio/webm",
    ) -> dict:
        """
        Process audio input and return agent response.

        Returns:
            {
                "agent_text": str,       # what LIA says next
                "state": str,            # current state
                "progress": float,       # 0.0 to 1.0
                "current_question": int,
                "total_questions": int,
                "is_done": bool,
                "score": float | null,   # final score when done
            }
        """
        # Transcribe
        transcription = await self._transcribe(audio_bytes, audio_format, session.language)

        if session.state == InterviewState.INTRO:
            return await self._handle_intro(session)

        elif session.state == InterviewState.QUESTIONING:
            return await self._handle_answer(session, transcription)

        elif session.state == InterviewState.SCORING:
            return await self._handle_scoring(session)

        elif session.state == InterviewState.CLOSING:
            return await self._handle_closing(session)

        return self._build_response(session, "Entrevista encerrada.", is_done=True)

    async def start_session(self, session: VoiceInterviewSession) -> dict:
        """Start interview without audio (initial greeting)."""
        return await self._handle_intro(session)

    async def _handle_intro(self, session: VoiceInterviewSession) -> dict:
        first_q = session.questions[0] if session.questions else None
        text = (
            f"Olá {session.candidate_name}! Sou a LIA, assistente de recrutamento. "
            f"Vou fazer {len(session.questions)} perguntas rápidas para conhecer melhor seu perfil. "
        )
        if first_q:
            text += f"Vamos começar: {first_q.text}"

        session.state = InterviewState.QUESTIONING
        session.current_q_idx = 0
        return self._build_response(session, text)

    async def _handle_answer(self, session: VoiceInterviewSession, answer: str) -> dict:
        if not answer.strip():
            current_q = session.questions[session.current_q_idx]
            return self._build_response(session, f"Não consegui entender. Pode repetir? {current_q.text}")

        current_q = session.questions[session.current_q_idx]

        # Store answer
        session.answers[current_q.question_id] = answer

        # Score this answer
        score = await self._score_answer(answer, current_q, company_id=session.company_id)
        session.scores[current_q.question_id] = score

        # Advance
        session.current_q_idx += 1
        if session.current_q_idx < len(session.questions):
            next_q = session.questions[session.current_q_idx]
            text = f"Entendido, obrigada! Próxima pergunta: {next_q.text}"
        else:
            session.state = InterviewState.SCORING
            text = "Perfeito! Aguarde um momento enquanto processo suas respostas."
            # Auto-advance to scoring → closing
            return await self._handle_scoring(session)

        return self._build_response(session, text)

    async def _handle_scoring(self, session: VoiceInterviewSession) -> dict:
        total = sum(
            session.scores.get(q.question_id, 0) * q.weight
            for q in session.questions
        )
        session.final_score = round(total, 1)
        session.state = InterviewState.CLOSING
        return await self._handle_closing(session)

    async def _handle_closing(self, session: VoiceInterviewSession) -> dict:
        text = (
            f"Obrigada {session.candidate_name}! "
            f"Suas respostas foram registradas com sucesso. "
            f"O time de recrutamento entrará em contato em breve. Até logo!"
        )
        session.state = InterviewState.DONE

        # Notify recruiter
        await self._notify_completion(session)

        return self._build_response(session, text, is_done=True)

    async def _score_answer(
        self, answer: str, question: ScreeningQuestion, company_id: str | None = None,
    ) -> float:
        """Score candidate answer against ideal using LLM."""
        try:
            # Canonical LLM factory (multi-tenant aware). Replaces broken
            # get_llm import — voice interview scoring was 100% in fallback
            # (returned 50.0 neutral) until 2026-05-27. ALL candidates
            # received same default score.
            from app.shared.providers.llm_factory import create_tracked_llm
            llm = create_tracked_llm(
                temperature=0.0,
                service_name="VoiceInterviewStateMachine",
                operation="score_answer",
                max_output_tokens=64,
                tenant_id=company_id,
            )
            prompt = (
                f'Pergunta: "{question.text}"\n'
                f'Resposta ideal: "{question.ideal_answer}"\n'
                f'Resposta do candidato: "{answer}"\n\n'
                f"Dê um score de 0 a 100 para a adequação da resposta.\n"
                f"Considere: completude, relevância, alinhamento com a resposta ideal.\n"
                f"Responda APENAS com o número inteiro."
            )
            resp = await llm.ainvoke(prompt)
            return float(resp.content.strip())
        except Exception:
            return 50.0  # Default neutral score

    async def _transcribe(self, audio_bytes: bytes, audio_format: str, language: str) -> str:
        """Transcribe audio to text. Tries GeminiVoice → Whisper → fallback."""
        # Try GeminiVoiceService (Replit)
        try:
            from app.shared.services.gemini_voice_service import GeminiVoiceService
            svc = GeminiVoiceService()
            result = await svc.transcribe_audio(audio_bytes, audio_format, language)
            return result.text
        except Exception:
            pass

        # Try local Whisper
        try:
            import whisper
            import tempfile
            import os
            model = whisper.load_model("base")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                f.flush()
                result = model.transcribe(f.name, language=language[:2])
                os.unlink(f.name)
                return result.get("text", "")
        except Exception:
            pass

        logger.warning("[VoiceInterview] All transcription methods failed")
        return ""

    async def _notify_completion(self, session: VoiceInterviewSession):
        """Notify recruiter that voice screening is complete."""
        try:
            from lia_messaging.notification_service import NotificationService
            notification_service = NotificationService()
            await notification_service.send(
                company_id=session.company_id,
                event_type="voice_screening_completed",
                title=f"Triagem por voz concluída — {session.candidate_name}",
                body=f"Score: {session.final_score}/100 · {len(session.questions)} perguntas",
                severity="info",
                channels=["bell", "email"],
                metadata=session.to_dict(),
            )
        except Exception as e:
            logger.warning("[VoiceInterview] Notification failed: %s", e)

    def _build_response(self, session: VoiceInterviewSession, text: str, is_done: bool = False) -> dict:
        return {
            "agent_text": text,
            "state": session.state.value,
            "progress": session.progress,
            "current_question": session.current_q_idx,
            "total_questions": len(session.questions),
            "is_done": is_done or session.is_complete,
            "score": session.final_score,
        }


voice_interview_state_machine = VoiceInterviewStateMachine()
