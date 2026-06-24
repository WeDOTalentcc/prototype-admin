"""
WSI Question Adjust API — adjusting and persisting screening questions per job vacancy.
"""
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.cv_screening.services.wsi_question_adjuster import wsi_question_adjuster_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.errors import LIAError

router = APIRouter(prefix="/wsi", tags=["WSI Question Adjust"])
logger = logging.getLogger(__name__)

# Onda 4.2c-P0-13 (2026-05-23): key composta (company_id, job_id) — cross-tenant safe.
# TODO migrar pra DB persistente (audit gap G5 — in-memory perde restart).
_saved_questions: dict[tuple[str, str], dict[str, Any]] = {}


class QuestionItem(BaseModel):
    id: str | None = None
    text: str
    category: str | None = None
    type: str | None = "open"
    weight: float | None = 0.75
    skill_targeted: str | None = None


class AdjustQuestionsRequest(WeDoBaseModel):
    job_id: str
    block_id: str
    adjustment_prompt: str
    current_questions: list[QuestionItem]
    job_context: dict[str, Any] | None = None


class EvaluateJDRequest(WeDoBaseModel):
    job_title: str
    responsibilities: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    behavioral_competencies: list[str] = Field(default_factory=list)
    seniority: str | None = None
    department: str | None = None
    description: str | None = None


class SaveQuestionsRequest(WeDoBaseModel):
    job_id: str
    questions: list[QuestionItem]
    source: str = "wsi_generation"


class SaveQuestionsResponse(BaseModel):
    success: bool
    job_id: str
    questions_count: int
    source: str
    saved_at: str
    iteration_reset: bool = False


class GetQuestionsResponse(BaseModel):
    success: bool
    job_id: str
    questions: list[QuestionItem]
    questions_count: int
    source: str | None = None
    saved_at: str | None = None


@router.post("/questions/adjust", response_model=None)
async def adjust_questions(request: AdjustQuestionsRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Adjust WSI questions based on recruiter's natural language prompt."""
    try:
        result = await wsi_question_adjuster_service.adjust_questions(
            job_id=request.job_id,
            block_id=request.block_id,
            adjustment_prompt=request.adjustment_prompt,
            current_questions=[q.dict() for q in request.current_questions],
            job_context=request.job_context
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Adjustment failed"))

        return result
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting WSI questions: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/jd-evaluate", response_model=None)
async def evaluate_jd(request: EvaluateJDRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Evaluate a Job Description for WSI question generation readiness."""
    try:
        result = await wsi_question_adjuster_service.evaluate_job_description(
            job_title=request.job_title,
            responsibilities=request.responsibilities,
            technical_skills=request.technical_skills,
            behavioral_competencies=request.behavioral_competencies,
            seniority=request.seniority,
            department=request.department,
            description=request.description
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating JD: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/questions/save", response_model=SaveQuestionsResponse)
async def save_questions(request: SaveQuestionsRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Save generated or adjusted screening questions to a job vacancy.
    Resets the adjuster iteration count for this job so fresh adjustments can be made.
    """
    try:
        saved_at = datetime.utcnow().isoformat() + "Z"

        # Onda 4.2c-P0-13 (2026-05-23): key inclui company_id pra evitar
        # cross-tenant read/write entre jobs com mesmo UUID em tenants
        # diferentes (defesa em profundidade — UUIDs sao unicos mas key
        # composta torna explicito).
        # TODO follow-up: migrar pra DB persistente (vide audit gap G5).
        _saved_questions[(company_id, request.job_id)] = {
            "questions": [q.dict() for q in request.questions],
            "source": request.source,
            "saved_at": saved_at,
        }

        iteration_reset = False
        iteration_keys_to_reset = [
            k for k in wsi_question_adjuster_service._iteration_counts
            if k.startswith(f"{request.job_id}_")
        ]
        if iteration_keys_to_reset:
            for key in iteration_keys_to_reset:
                del wsi_question_adjuster_service._iteration_counts[key]
            iteration_reset = True

        logger.info(
            f"Saved {len(request.questions)} questions for job {request.job_id} "
            f"(source={request.source}, iteration_reset={iteration_reset})"
        )

        return SaveQuestionsResponse(
            success=True,
            job_id=request.job_id,
            questions_count=len(request.questions),
            source=request.source,
            saved_at=saved_at,
            iteration_reset=iteration_reset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving WSI questions for job {request.job_id}: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/questions/{job_id}", response_model=GetQuestionsResponse)
async def get_questions(job_id: str, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retrieve saved screening questions for a job vacancy.
    """
    # Onda 4.2c-P0-13 (2026-05-23): lookup com tuple key (company_id, job_id).
    stored = _saved_questions.get((company_id, job_id))

    if not stored:
        return GetQuestionsResponse(
            success=True,
            job_id=job_id,
            questions=[],
            questions_count=0,
            source=None,
            saved_at=None,
        )

    questions = [QuestionItem(**q) for q in stored["questions"]]

    return GetQuestionsResponse(
        success=True,
        job_id=job_id,
        questions=questions,
        questions_count=len(questions),
        source=stored.get("source"),
        saved_at=stored.get("saved_at"),
    )
