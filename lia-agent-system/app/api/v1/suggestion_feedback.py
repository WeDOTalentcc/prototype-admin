"""
Suggestion Feedback API - Endpoints for capturing and analyzing LIA suggestion feedback.

Provides:
- Record when a user accepts/rejects a LIA suggestion
- Stats on suggestion acceptance rates by field
- Learned adjustments for wizard suggestions
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.feedback_learning import SuggestionFeedback
from app.services.feedback_learning_service import FeedbackLearningService

router = APIRouter(prefix="/suggestion-feedback", tags=["Suggestion Feedback"])
logger = logging.getLogger(__name__)

_feedback_service = FeedbackLearningService()


class SuggestionFeedbackRequest(BaseModel):
    company_id: str
    field_name: str = Field(..., description="Field being suggested: salary, skills, seniority, etc.")
    suggested_value: Any | None = None
    actual_value: Any | None = None
    accepted: bool = Field(..., description="True if user accepted the suggestion")
    context: dict | None = Field(default=None, description="Context: role, seniority, department, etc.")
    created_by: str | None = None


class SuggestionFeedbackResponse(BaseModel):
    id: str
    company_id: str
    field_name: str
    suggested_value: Any | None = None
    actual_value: Any | None = None
    accepted: int
    context: dict | None = None
    created_at: str | None = None


class FieldStatsResponse(BaseModel):
    field_name: str
    total_suggestions: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    acceptance_rate: float = 0.0


class SuggestionStatsResponse(BaseModel):
    company_id: str
    total_feedback: int = 0
    overall_acceptance_rate: float = 0.0
    by_field: list[FieldStatsResponse] = Field(default_factory=list)


class AdjustmentResponse(BaseModel):
    field: str
    adjustment_reason: str
    confidence: str
    based_on_samples: int
    original_value: Any | None = None
    adjusted_value: Any | None = None


@router.post("/record", response_model=None)
# TODO(phase2): extract to repository — suggestion feedback
async def record_suggestion_feedback(
    request: SuggestionFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        feedback = SuggestionFeedback(
            company_id=request.company_id,
            field_name=request.field_name,
            suggested_value=request.suggested_value,
            actual_value=request.actual_value,
            accepted=1 if request.accepted else 0,
            context=request.context,
            created_by=request.created_by,
        )
        db.add(feedback)
        await db.flush()

        logger.info(
            f"SuggestionFeedback: recorded {'accepted' if request.accepted else 'rejected'} "
            f"for field '{request.field_name}' (company={request.company_id})"
        )

        return {
            "success": True,
            "feedback_id": str(feedback.id),
            "accepted": request.accepted,
        }
    except Exception as e:
        logger.error(f"Failed to record suggestion feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/stats", response_model=SuggestionStatsResponse)
async def get_suggestion_stats(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        base_filter = SuggestionFeedback.company_id == company_id

        total_q = await db.execute(
            select(func.count()).select_from(SuggestionFeedback).where(base_filter)
        )
        total = total_q.scalar() or 0

        accepted_q = await db.execute(
            select(func.count()).select_from(SuggestionFeedback).where(
                and_(base_filter, SuggestionFeedback.accepted == 1)
            )
        )
        accepted_total = accepted_q.scalar() or 0

        field_query = (
            select(
                SuggestionFeedback.field_name,
                func.count().label("total"),
                func.sum(case((SuggestionFeedback.accepted == 1, 1), else_=0)).label("accepted"),
            )
            .where(base_filter)
            .group_by(SuggestionFeedback.field_name)
            .order_by(func.count().desc())
        )
        field_result = await db.execute(field_query)
        field_rows = field_result.all()

        by_field = []
        for field_name, field_total, field_accepted in field_rows:
            rejected = field_total - (field_accepted or 0)
            by_field.append(
                FieldStatsResponse(
                    field_name=field_name,
                    total_suggestions=field_total,
                    accepted_count=field_accepted or 0,
                    rejected_count=rejected,
                    acceptance_rate=round((field_accepted or 0) / field_total, 4) if field_total > 0 else 0.0,
                )
            )

        return SuggestionStatsResponse(
            company_id=company_id,
            total_feedback=total,
            overall_acceptance_rate=round(accepted_total / total, 4) if total > 0 else 0.0,
            by_field=by_field,
        )
    except Exception as e:
        logger.error(f"Failed to get suggestion stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/adjustments", response_model=list[AdjustmentResponse])
async def get_learned_adjustments(
    company_id: str,
    role: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        sample_suggestion = {"salary_range": {"min": 0, "max": 0, "currency": "BRL"}}
        result = await _feedback_service.apply_learning(
            db=db,
            company_id=company_id,
            suggestion=sample_suggestion,
            role=role,
            seniority=seniority,
        )

        adjustments_raw = result.get("adjustments", [])
        return [
            AdjustmentResponse(
                field=adj.get("field", ""),
                adjustment_reason=adj.get("reason", ""),
                confidence=adj.get("confidence", "low"),
                based_on_samples=0,
                original_value=adj.get("original"),
                adjusted_value=adj.get("adjusted"),
            )
            for adj in adjustments_raw
        ]
    except Exception as e:
        logger.error(f"Failed to get learned adjustments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
