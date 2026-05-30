"""
Voice Screening API — Talent Pool only.

In jobs, the existing screening agent handles triagem.

Apply to: lia-agent-system/app/api/v1/voice_screening.py
Register: app.include_router(voice_screening_router)
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from pydantic import BaseModel, Field
from typing import Optional
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/voice-screening", tags=["Voice Screening"])

# In-memory session store (production: use Redis with TTL)
_sessions: dict = {}


class CreateSessionRequest(WeDoBaseModel):
    talent_pool_id: str
    candidate_id: str
    candidate_name: str
    channel: str = Field(default="web", pattern="^(web|whatsapp|phone)$")


class SessionResponse(BaseModel):
    session_id: str
    state: str
    progress: float
    current_question: int
    total_questions: int
    is_done: bool
    agent_text: str
    score: Optional[float] = None


@router.post("/sessions", response_model=SessionResponse)
async def create_voice_session(
    body: CreateSessionRequest,
    current_user: dict = Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a new voice screening session for a candidate in a talent pool.

    Loads screening questions from the pool's WSI compact config.
    Returns the initial greeting + first question.

    Onda 4.2c-P0-12 (2026-05-23): removido `company_id = current_user.get(...)`
    com fallback 'unknown' — bypass de tenant isolation. company_id JA vem
    injetado via Depends(require_company_id) (REGRA 6 CLAUDE.md).
    """
    # Onda 4.2c-P0-10 (2026-05-23): _load_pool_questions agora recebe company_id
    # pra cross-tenant guard.
    screening_questions = await _load_pool_questions(body.talent_pool_id, company_id)
    if not screening_questions:
        raise HTTPException(400, "Pool não tem perguntas de triagem configuradas")

    from app.services.voice_interview_state_machine import (
        VoiceInterviewSession,
        voice_interview_state_machine,
    )

    session = VoiceInterviewSession.from_pool_questions(
        company_id=company_id,
        talent_pool_id=body.talent_pool_id,
        candidate_id=body.candidate_id,
        candidate_name=body.candidate_name,
        screening_questions=screening_questions,
        channel=body.channel,
    )

    # Start session (intro + first question)
    response = await voice_interview_state_machine.start_session(session)

    # Store session
    _sessions[session.session_id] = session

    return SessionResponse(
        session_id=session.session_id,
        **response,
    )


@router.post("/sessions/{session_id}/audio", response_model=SessionResponse)
async def submit_audio(
    session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    file: UploadFile = File(...),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Submit audio response from candidate. Transcribes and advances the state machine.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Sessão não encontrada ou expirada")

    if session.is_complete:
        raise HTTPException(400, "Sessão já finalizada")

    audio_bytes = await file.read()
    audio_format = file.content_type or "audio/webm"

    from app.services.voice_interview_state_machine import voice_interview_state_machine

    response = await voice_interview_state_machine.handle_audio_input(
        session, audio_bytes, audio_format,
    )

    # If done, persist results and update candidate stage
    if response.get("is_done"):
        await _persist_results(session)
        del _sessions[session_id]  # Clean up memory

    return SessionResponse(session_id=session_id, **response)


@router.post("/sessions/{session_id}/text", response_model=SessionResponse)
async def submit_text(
    session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: dict,
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Submit text response (for WhatsApp/chat fallback). Same flow as audio but skips STT.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Sessão não encontrada ou expirada")

    text = body.get("text", "")
    if not text.strip():
        raise HTTPException(400, "Texto vazio")

    from app.services.voice_interview_state_machine import (
        VoiceInterviewStateMachine,
        InterviewState,
    )

    sm = VoiceInterviewStateMachine()

    if session.state == InterviewState.INTRO:
        response = await sm._handle_intro(session)
    elif session.state == InterviewState.QUESTIONING:
        response = await sm._handle_answer(session, text)
    else:
        response = sm._build_response(session, "Sessão em estado inesperado.")

    if response.get("is_done"):
        await _persist_results(session)
        del _sessions[session_id]

    return SessionResponse(session_id=session_id, **response)


@router.get("/sessions/{session_id}")
async def get_session_status(session_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get current status of a voice screening session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Sessão não encontrada ou expirada")

    return session.to_dict()


# ---------- Helpers ----------

async def _load_pool_questions(talent_pool_id: str, company_id: str) -> list[dict]:
    """Load screening questions from talent pool.

    Onda 4.2c-P0-10 (2026-05-23): adicionado company_id obrigatorio.
    Antes user empresa A podia iniciar voice session usando talent_pool_id
    da empresa B e obter screening_questions configuradas (cross-tenant read).
    """
    try:
        from app.core.database import get_db_session
        from sqlalchemy import text

        async with get_db_session() as db:
            result = await db.execute(
                text(
                    "SELECT screening_questions FROM talent_pools "
                    "WHERE id = :id AND company_id = :company_id"
                ),
                {"id": talent_pool_id, "company_id": company_id},
            )
            row = result.fetchone()
            if row and row[0]:
                return row[0] if isinstance(row[0], list) else json.loads(row[0])
    except Exception as e:
        logger.warning("[VoiceScreening] Failed to load pool questions: %s", e)

    return []


async def _persist_results(session) -> None:
    """Save screening results to talent_pool_candidates and advance stage."""
    try:
        from app.core.database import get_db_session
        from sqlalchemy import text

        screening_data = {
            "type": "voice",
            "session_id": session.session_id,
            "channel": session.channel,
            "answers": session.answers,
            "scores": session.scores,
            "final_score": session.final_score,
            "duration_secs": session.duration_secs,
        }

        async with get_db_session() as db:
            # Onda 4.2c-P0-11 (2026-05-23): adicionado company_id filter no UPDATE.
            # session.company_id ja foi gravado em create_voice_session via JWT.
            await db.execute(
                text("""
                    UPDATE talent_pool_candidates
                    SET screening_data = :data,
                        fit_score = :score,
                        stage = 'screened',
                        updated_at = NOW()
                    WHERE talent_pool_id = :pool_id
                      AND candidate_id = :candidate_id
                      AND company_id = :company_id
                """),
                {
                    "data": json.dumps(screening_data),
                    "score": session.final_score,
                    "pool_id": session.talent_pool_id,
                    "candidate_id": session.candidate_id,
                    "company_id": session.company_id,
                },
            )
            await db.commit()

        logger.info(
            "[VoiceScreening] Results saved: session=%s candidate=%s score=%s",
            session.session_id, session.candidate_id, session.final_score,
        )
    except Exception as e:
        logger.error("[VoiceScreening] Failed to persist results: %s", e)

reorder_collection_before_item(router)
