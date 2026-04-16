"""
WSI Question Adjust API
Endpoints for adjusting WSI questions via conversational prompts.

Note: ``/jd-evaluate`` and ``/questions/save`` previously lived here as
in-memory stubs but have been removed because the production-ready versions
in ``app/api/v1/wsi/evaluation.py`` and ``app/api/v1/wsi/questions.py``
register the same routes — the duplicates emitted "Duplicate Operation ID"
warnings from FastAPI at startup.

The ``GET /wsi/questions/{job_id}`` reader used to be backed by an in-memory
dict that was never populated (saves go to PostgreSQL via the canonical
``/wsi/questions/save`` handler). It now reads the active screening question
set from the database via ``ScreeningQuestionSetService``.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.cv_screening.services.screening_question_set_service import (
    ScreeningQuestionSetService,
    get_screening_question_set_service,
)
from app.domains.cv_screening.services.wsi_question_adjuster import wsi_question_adjuster_service

router = APIRouter(prefix="/wsi", tags=["WSI Question Adjust"])
logger = logging.getLogger(__name__)


class QuestionItem(BaseModel):
    id: str | None = None
    text: str
    category: str | None = None
    type: str | None = "open"
    weight: float | None = 0.75
    skill_targeted: str | None = None


class AdjustQuestionsRequest(BaseModel):
    job_id: str
    block_id: str
    adjustment_prompt: str
    current_questions: list[QuestionItem]
    job_context: dict[str, Any] | None = None


class GetQuestionsResponse(BaseModel):
    success: bool
    job_id: str
    questions: list[QuestionItem]
    questions_count: int
    source: str | None = None
    saved_at: str | None = None


@router.post("/questions/adjust", response_model=None)
async def adjust_questions(request: AdjustQuestionsRequest):
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
    except Exception as e:
        logger.error(f"Error adjusting WSI questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/{job_id}", response_model=GetQuestionsResponse)
async def get_questions(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    sqs_svc: ScreeningQuestionSetService = Depends(get_screening_question_set_service),
):
    """
    Retrieve saved screening questions for a job vacancy.

    Reads the active screening question set version from the database
    (the same store written by ``POST /wsi/questions/save``).
    """
    try:
        qs = await sqs_svc.get_active_version(db, job_id)
    except Exception as e:
        logger.error(f"Failed to load active question set for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if not qs or not qs.questions_snapshot:
        return GetQuestionsResponse(
            success=True,
            job_id=job_id,
            questions=[],
            questions_count=0,
            source=None,
            saved_at=None,
        )

    questions: list[QuestionItem] = []
    for q in qs.questions_snapshot:
        if not isinstance(q, dict):
            continue
        questions.append(QuestionItem(
            id=q.get("id"),
            text=q.get("text") or q.get("question") or "",
            category=q.get("category"),
            type=q.get("type", "open"),
            weight=q.get("weight", 0.75),
            skill_targeted=q.get("skill_targeted"),
        ))

    return GetQuestionsResponse(
        success=True,
        job_id=job_id,
        questions=questions,
        questions_count=len(questions),
        source=qs.source,
        saved_at=qs.created_at.isoformat() if qs.created_at else None,
    )
