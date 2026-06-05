"""WSI sessions API.

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

from app.core.database import get_db, get_tenant_db
from app.domains.voice.repositories.wsi_repository import WsiRepository
from app.shared.services.interview_session_store import interview_session_store
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Simple session / results routes
# ---------------------------------------------------------------------------

@router.get("/session/{session_id}", response_model=None)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    """Get WSI session details with questions and responses.

    Onda 4.2c-P0-1 (2026-05-23): cross-tenant guard via pre-check JOIN
    com job_vacancies. Tabela wsi_sessions sem RLS — defesa app-layer.
    """
    try:
        from sqlalchemy import text as _text

        _repo = WsiRepository(db)
        session = await _repo.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Onda 4.2c-P0-1: tenant guard — session[2] = job_vacancy_id.
        if session[2]:
            tenant_check = await db.execute(
                _text("SELECT 1 FROM job_vacancies WHERE id = :jv AND company_id = :cid"),
                {"jv": session[2], "cid": company_id},
            )
            if not tenant_check.scalar():
                raise HTTPException(status_code=404, detail="Session not found")

        questions = await _repo.get_questions_for_session(session_id)

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
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Get WSI results for a specific candidate.

    Onda 4.2c-P0-2 (2026-05-23): cross-tenant guard via pre-check do
    candidate.company_id. Antes vazava overall_wsi/classification/
    percentile de candidatos cross-tenant.
    """
    try:
        from sqlalchemy import text as _text

        # Onda 4.2c-P0-2: tenant guard.
        cand_check = await db.execute(
            _text("SELECT 1 FROM candidates WHERE id = :cid AND company_id = :company_id"),
            {"cid": candidate_id, "company_id": company_id},
        )
        if not cand_check.scalar():
            raise HTTPException(status_code=404, detail="Candidate not found")

        _repo = WsiRepository(db)
        results = await _repo.get_results_for_candidate(candidate_id, limit)

        return {
            "candidate_id": candidate_id,
            "total_screenings": len(results),
            "results": [
                {
                    "result_id": r[0],
                    "job_vacancy_id": r[1],
                    "overall_wsi": float(r[2]),
                    "technical_wsi": float(r[3]),
                    "behavioral_wsi": float(r[4]),
                    "classification": r[5],
                    "percentile": r[6],
                    "created_at": r[7].isoformat() if r[7] else None,
                    "screening_type": r[8],
                }
                for r in results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{result_id}/details", response_model=None)
async def get_result_details(
    result_id: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Detalhe completo de um resultado WSI: scores, sessão, respostas analisadas,
    relatório estruturado e feedback. Contrato consumido pela modal de Triagem WSI
    (triagem-details-modal). Portado do antigo wsi_endpoints.py (não montado) para
    o pacote vivo, COM tenant guard (require_company_id + JOIN em job_vacancies)."""
    try:
        repo = WsiRepository(db)
        row = await repo.get_result_with_session(result_id)
        if not row:
            raise HTTPException(status_code=404, detail="WSI result not found")

        session_id = str(row[1])
        candidate_id = str(row[2])
        job_vacancy_id = str(row[3])

        # Tenant guard: o resultado precisa pertencer a uma vaga da company do JWT.
        tenant_check = await db.execute(
            text("SELECT 1 FROM job_vacancies WHERE id = :jv AND company_id = :cid"),
            {"jv": job_vacancy_id, "cid": company_id},
        )
        if not tenant_check.scalar():
            raise HTTPException(status_code=404, detail="WSI result not found")

        responses = await repo.get_responses_for_session(session_id)
        report_row = await repo.get_report_for_result(result_id)
        feedback_row = await repo.get_feedback_for_result(result_id)

        duration_minutes = None
        if row[12] and row[13]:
            duration_minutes = int((row[13] - row[12]).total_seconds() / 60)

        return {
            "result_id": str(row[0]),
            "session_id": session_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "scores": {
                "technical_wsi": float(row[4]),
                "behavioral_wsi": float(row[5]),
                "overall_wsi": float(row[6]),
                "classification": row[7],
                "percentile": row[8],
            },
            "session": {
                "screening_type": row[10],
                "mode": row[11],
                "started_at": row[12].isoformat() if row[12] else None,
                "completed_at": row[13].isoformat() if row[13] else None,
                "duration_minutes": duration_minutes,
            },
            "responses": [
                {
                    "competency": r[0],
                    "response_text": r[1],
                    "scores": {
                        "autodeclaration": float(r[2]) if r[2] is not None else None,
                        "context": float(r[3]) if r[3] is not None else None,
                        "bloom_level": r[4],
                        "dreyfus_level": r[5],
                        "final_score": float(r[9]),
                    },
                    "evidences": r[6] if r[6] else [],
                    "red_flags": r[7] if r[7] else [],
                    "consistency_penalty": float(r[8]) if r[8] is not None else 0,
                    "justification": r[10],
                    "question": {
                        "text": r[12],
                        "framework": r[13],
                        "type": r[14],
                        "weight": float(r[15]) if r[15] is not None else 0,
                        "expected_signals": r[16] if r[16] else [],
                        "sequence": r[17],
                    },
                }
                for r in responses
            ],
            "report": {
                "executive_summary": report_row[0],
                "technical_analysis": report_row[1],
                "behavioral_analysis": report_row[2],
                "cultural_fit": report_row[3],
                "recommendation": report_row[4],
            } if report_row else None,
            "feedback": {
                "decision": feedback_row[0],
                "main_message": feedback_row[1],
                "technical_strengths": feedback_row[2],
                "development_opportunities": feedback_row[3],
                "behavioral_strengths": feedback_row[4],
                "next_steps": feedback_row[5],
                "personalized_tip": feedback_row[6],
                "development_plan": feedback_row[7],
                "recommended_resources": feedback_row[8],
            } if feedback_row else None,
            "created_at": row[9].isoformat() if row[9] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get result details: {str(e)}")


# ---------------------------------------------------------------------------
# WSI Interview Graph — entrevistas síncronas passo-a-passo
# ---------------------------------------------------------------------------

class InterviewGraphStartRequest(WeDoBaseModel):
    candidate_id: str
    job_id: str
    interview_level: str = Field(default="standard", pattern="^(quick|standard|full)$")


class InterviewGraphRespondRequest(WeDoBaseModel):
    response: str = Field(..., description="Resposta do candidato à pergunta atual")


@router.post("/interview-graph/sessions", summary="Inicia sessão de entrevista WSI síncrona", response_model=None)
async def start_interview_graph_session(
    request: InterviewGraphStartRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Cria uma nova sessão de entrevista WSI usando o WSIInterviewGraph.

    Carrega o contexto (vaga + candidato), gera o banco de perguntas e
    apresenta a primeira pergunta. Use `POST /interview-graph/sessions/{session_id}/respond`
    para cada resposta subsequente do candidato.
    """
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = wsi_interview_graph.create_session(
        candidate_id=request.candidate_id,
        job_id=request.job_id,
        company_id=company_id,
        interview_level=request.interview_level,
    )

    # Pré-carrega contexto da vaga para o grafo (que não tem acesso direto ao DB)
    try:
        _repo = WsiRepository(db)
        job_row = await _repo.get_job_vacancy_context(request.job_id, company_id)
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
    response_model=None)
async def respond_interview_graph(session_id: str, request: InterviewGraphRespondRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    response_model=None)
async def get_interview_graph_session(session_id: str, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Retorna o resumo completo da sessão para fins de auditoria e compliance."""
    from app.domains.cv_screening.agents.wsi_interview_graph import wsi_interview_graph

    state = await interview_session_store.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Sessão '{session_id}' não encontrada")

    return wsi_interview_graph.get_session_summary(state)
