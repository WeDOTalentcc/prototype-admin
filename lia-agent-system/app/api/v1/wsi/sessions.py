"""
WSI package — session management routes.

Routes:
  GET  /session/{session_id}
  GET  /results/{candidate_id}
  POST /interview-graph/sessions
  POST /interview-graph/sessions/{session_id}/respond
  GET  /interview-graph/sessions/{session_id}
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.interview_session_store import interview_session_store

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Simple session / results routes
# ---------------------------------------------------------------------------

@router.get("/session/{session_id}", response_model=None)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get WSI session details with questions and responses."""
    try:
        result = await db.execute(text("""
            SELECT id, candidate_id, job_vacancy_id, screening_type, mode, status, started_at, completed_at
            FROM wsi_sessions WHERE id = :session_id
        """), {"session_id": session_id})
        session = result.fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        questions_result = await db.execute(text("""
            SELECT id, competency, framework, question_type, question_text, weight
            FROM wsi_questions WHERE session_id = :session_id ORDER BY sequence_order
        """), {"session_id": session_id})
        questions = questions_result.fetchall()

        return {
            "session": {
                "id": session[0],
                "candidate_id": session[1],
                "job_vacancy_id": session[2],
                "screening_type": session[3],
                "mode": session[4],
                "status": session[5],
                "started_at": session[6].isoformat() if session[6] else None,
                "completed_at": session[7].isoformat() if session[7] else None
            },
            "questions": [
                {"id": q[0], "competency": q[1], "framework": q[2],
                 "question_type": q[3], "question_text": q[4], "weight": float(q[5])}
                for q in questions
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{candidate_id}", response_model=None)
async def get_candidate_results(
    candidate_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get WSI results for a specific candidate."""
    try:
        result = await db.execute(text("""
            SELECT r.id, r.job_vacancy_id, r.overall_wsi, r.classification, r.created_at,
                   s.screening_type
            FROM wsi_results r
            JOIN wsi_sessions s ON r.session_id = s.id
            WHERE r.candidate_id = :candidate_id
            ORDER BY r.created_at DESC
            LIMIT :limit
        """), {"candidate_id": candidate_id, "limit": limit})

        results = result.fetchall()

        return {
            "candidate_id": candidate_id,
            "total_screenings": len(results),
            "results": [
                {
                    "result_id": r[0],
                    "job_vacancy_id": r[1],
                    "overall_score": float(r[2]),
                    "classification": r[3],
                    "created_at": r[4].isoformat() if r[4] else None,
                    "screening_type": r[5]
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# WSI Interview Graph — entrevistas síncronas passo-a-passo
# ---------------------------------------------------------------------------

class InterviewGraphStartRequest(BaseModel):
    candidate_id: str
    job_id: str
    company_id: str
    interview_level: str = Field(default="standard", pattern="^(quick|standard|full)$")


class InterviewGraphRespondRequest(BaseModel):
    response: str = Field(..., description="Resposta do candidato à pergunta atual")


@router.post("/interview-graph/sessions", summary="Inicia sessão de entrevista WSI síncrona", response_model=None)
async def start_interview_graph_session(
    request: InterviewGraphStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cria uma nova sessão de entrevista WSI usando o WSIInterviewGraph.

    Carrega o contexto (vaga + candidato), gera o banco de perguntas e
    apresenta a primeira pergunta. Use `POST /interview-graph/sessions/{session_id}/respond`
    para cada resposta subsequente do candidato.
    """
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = wsi_interview_graph.create_session(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        company_id=request.company_id,
        interview_level=request.interview_level,
    )

    # Pré-carrega contexto da vaga para o grafo (que não tem acesso direto ao DB)
    try:
        job_result = await db.execute(text("""
            SELECT title, description, seniority_level
            FROM job_vacancies WHERE id = :job_id AND company_id = :company_id
            LIMIT 1
        """), {"job_id": request.job_id, "company_id": request.company_id})
        job_row = job_result.fetchone()
        if job_row:
            state.job_requirements = {
                "title": job_row[0] or "",
                "description": job_row[1] or "",
                "seniority": job_row[2],
            }
    except Exception as exc:
        logger.warning(f"[WSIInterviewGraph] Failed to load job context: {exc}")

    state = await wsi_interview_graph.start(state)
    await interview_session_store.set(state.session_id, state)

    current_question = None
    if state.current_question:
        current_question = {
            "block_id": state.current_question.block_id,
            "block_type": state.current_question.block_type,
            "question": state.current_question.question,
            "competency": state.current_question.competency,
        }

    return {
        "session_id": state.session_id,
        "stage": state.stage.value,
        "is_complete": state.is_complete,
        "progress_pct": round(state.progress_pct, 1),
        "questions_total": len(state.question_blocks),
        "awaiting_response": state.awaiting_response,
        "current_question": current_question,
    }


@router.post(
    "/interview-graph/sessions/{session_id}/respond",
    summary="Envia resposta do candidato na entrevista WSI síncrona",
, response_model=None)
async def respond_interview_graph(session_id: str, request: InterviewGraphRespondRequest):
    """Processa a resposta do candidato, pontua e avança para a próxima pergunta.

    Retorna a próxima pergunta (se houver) ou o resultado final (se a entrevista encerrou).
    """
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = await interview_session_store.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")

    state = await wsi_interview_graph.submit_response(state, request.response)
    await interview_session_store.set(session_id, state)

    next_question = None
    if state.current_question and state.awaiting_response:
        next_question = {
            "block_id": state.current_question.block_id,
            "block_type": state.current_question.block_type,
            "question": state.current_question.question,
            "competency": state.current_question.competency,
        }

    result = None
    if state.is_complete and state.wsi_final_score is not None:
        result = {
            "wsi_final_score": state.wsi_final_score,
            "recommendation": state.recommendation,
            "scores": {
                "technical": round(state.technical_score, 2),
                "behavioral": round(state.behavioral_score, 2),
                "situational": round(state.situational_score, 2),
                "eligibility": round(state.eligibility_score, 2),
            },
        }
        await interview_session_store.delete(session_id)

    return {
        "session_id": session_id,
        "stage": state.stage.value,
        "is_complete": state.is_complete,
        "progress_pct": round(state.progress_pct, 1),
        "awaiting_response": state.awaiting_response,
        "next_question": next_question,
        "result": result,
    }


@router.get(
    "/interview-graph/sessions/{session_id}",
    summary="Resumo auditável da sessão de entrevista WSI",
, response_model=None)
async def get_interview_graph_session(session_id: str):
    """Retorna o resumo completo da sessão para fins de auditoria e compliance."""
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = await interview_session_store.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")

    return wsi_interview_graph.get_session_summary(state)
