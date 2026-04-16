"""
WSI Question Adjust API
Endpoints for adjusting WSI questions via conversational prompts.

Note: ``/jd-evaluate`` and ``/questions/save`` previously lived here as
in-memory stubs but have been removed because the production-ready versions
in ``app/api/v1/wsi/evaluation.py`` and ``app/api/v1/wsi/questions.py``
register the same routes — the duplicates emitted "Duplicate Operation ID"
warnings from FastAPI at startup.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domains.cv_screening.services.wsi_question_adjuster import wsi_question_adjuster_service

router = APIRouter(prefix="/wsi", tags=["WSI Question Adjust"])
logger = logging.getLogger(__name__)

_saved_questions: dict[str, dict[str, Any]] = {}


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
async def get_questions(job_id: str):
    """
    Retrieve saved screening questions for a job vacancy.
    """
    stored = _saved_questions.get(job_id)

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
