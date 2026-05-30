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
from app.domains.cv_screening.repositories.suggestion_feedback_repository import SuggestionFeedbackRepository
from app.domains.analytics.services.feedback_learning_service import feedback_learning_service as _feedback_service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/suggestion-feedback", tags=["Suggestion Feedback"])
logger = logging.getLogger(__name__)


class SuggestionFeedbackRequest(WeDoBaseModel):
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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        _repo = SuggestionFeedbackRepository(db)
        feedback = await _repo.record(
            company_id=company_id,
            field_name=request.field_name,
            suggested_value=request.suggested_value,
            actual_value=request.actual_value,
            accepted=request.accepted,
            context=request.context,
            created_by=request.created_by,
        )

        logger.info(
            f"SuggestionFeedback: recorded {'accepted' if request.accepted else 'rejected'} "
            f"for field '{request.field_name}' (company={company_id})"
        )

        return {
            "success": True,
            "feedback_id": str(feedback.id),
            "accepted": request.accepted,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record suggestion feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/stats", response_model=SuggestionStatsResponse)
async def get_suggestion_stats(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    try:
        _repo = SuggestionFeedbackRepository(db)
        total, accepted_total = await _repo.get_total_and_accepted(company_id)
        field_rows = await _repo.get_stats_by_field(company_id)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get suggestion stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/adjustments", response_model=list[AdjustmentResponse])
async def get_learned_adjustments(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    role: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get learned adjustments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
