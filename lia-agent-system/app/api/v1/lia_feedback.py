"""
LIA Feedback Loop & Training Data endpoints — extracted from lia_assistant.py (Sprint E).
Router is included by lia_assistant.router, so all routes resolve under /lia/feedback/... and /lia/training-data/...
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.feedback_service import feedback_service

logger = logging.getLogger(__name__)

feedback_router = APIRouter()

_DEPRECATED_DEFAULT_COMPANY_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


# ── Schemas ──────────────────────────────────────────────────────────────────

class ThumbsFeedbackRequest(BaseModel):
    """Request model for thumbs feedback."""
    session_id: str
    message_id: str
    thumbs: str  # "up" or "down"
    user_id: str = "default_user"
    company_id: str
    message_context: Optional[Dict[str, Any]] = None


class RatingFeedbackRequest(BaseModel):
    """Request model for rating feedback."""
    session_id: str
    message_id: str
    rating: int  # 1-5
    feedback_text: Optional[str] = None
    feedback_category: Optional[str] = None
    user_id: str = "default_user"
    company_id: str
    message_context: Optional[Dict[str, Any]] = None


class CorrectionFeedbackRequest(BaseModel):
    """Request model for correction feedback."""
    session_id: str
    message_id: str
    original_response: str
    correction: str
    user_id: str = "default_user"
    company_id: str
    message_context: Optional[Dict[str, Any]] = None


# ── Feedback Endpoints ────────────────────────────────────────────────────────

@feedback_router.post("/feedback/thumbs")
async def submit_thumbs_feedback(request: ThumbsFeedbackRequest) -> dict:
    """Submit thumbs up/down feedback on a LIA response."""
    try:
        if request.thumbs not in ("up", "down"):
            raise HTTPException(status_code=400, detail="thumbs must be 'up' or 'down'")
        message_context = request.message_context or {"message_id": request.message_id}
        message_context["message_id"] = request.message_id
        feedback = await feedback_service.record_feedback(
            session_id=request.session_id,
            company_id=request.company_id,
            user_id=request.user_id,
            feedback_type="thumbs",
            feedback_value=request.thumbs,
            message_context=message_context
        )
        logger.info(f"Thumbs feedback recorded: session={request.session_id}, thumbs={request.thumbs}")
        return {
            "success": True,
            "feedback_id": str(feedback.id),
            "message": f"Thank you for your {'positive' if request.thumbs == 'up' else 'negative'} feedback!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording thumbs feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.post("/feedback/rating")
async def submit_rating_feedback(request: RatingFeedbackRequest) -> dict:
    """Submit star rating feedback (1-5) on a LIA response."""
    try:
        if not 1 <= request.rating <= 5:
            raise HTTPException(status_code=400, detail="rating must be between 1 and 5")
        message_context = request.message_context or {"message_id": request.message_id}
        message_context["message_id"] = request.message_id
        feedback = await feedback_service.record_feedback(
            session_id=request.session_id,
            company_id=request.company_id,
            user_id=request.user_id,
            feedback_type="rating",
            feedback_value={"rating": request.rating, "feedback_text": request.feedback_text, "category": request.feedback_category},
            message_context=message_context
        )
        logger.info(f"Rating feedback recorded: session={request.session_id}, rating={request.rating}")
        return {"success": True, "feedback_id": str(feedback.id), "message": f"Thank you for rating this response {request.rating}/5!"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording rating feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.post("/feedback/correction")
async def submit_correction(request: CorrectionFeedbackRequest) -> dict:
    """Submit a correction for a LIA response (creates DPO training pair)."""
    try:
        if not request.correction.strip():
            raise HTTPException(status_code=400, detail="correction cannot be empty")
        message_context = request.message_context or {"message_id": request.message_id}
        message_context["message_id"] = request.message_id
        message_context["lia_response"] = request.original_response
        feedback = await feedback_service.record_feedback(
            session_id=request.session_id,
            company_id=request.company_id,
            user_id=request.user_id,
            feedback_type="correction",
            feedback_value=request.correction,
            message_context=message_context
        )
        logger.info(f"Correction feedback recorded: session={request.session_id}")
        return {"success": True, "feedback_id": str(feedback.id), "message": "Thank you for the correction! LIA will learn from this."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording correction feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.get("/feedback/metrics")
async def get_feedback_metrics(
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    days: int = Query(default=30, ge=1, le=365)
) -> dict:
    """Get aggregated feedback metrics (satisfaction rate, rating distribution, pattern insights)."""
    try:
        metrics = await feedback_service.get_feedback_metrics(company_id=company_id, days=days)
        logger.info(f"Feedback metrics retrieved: company={company_id}, days={days}")
        return metrics
    except Exception as e:
        logger.error(f"Error getting feedback metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.post("/feedback/process-batch")
async def process_feedback_batch() -> dict:
    """Process unprocessed feedback to extract learning patterns."""
    try:
        result = await feedback_service.process_feedback_batch()
        logger.info(f"Feedback batch processed: {result.get('processed_count', 0)} items")
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Error processing feedback batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Training Data Endpoints ───────────────────────────────────────────────────

@feedback_router.get("/training-data/export/openai")
async def export_training_data_openai(
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    min_rating: int = Query(default=4, ge=1, le=5),
    limit: int = Query(default=1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Export training data in OpenAI JSONL format."""
    from app.services.training_data_service import TrainingDataService
    try:
        service = TrainingDataService(db)
        training_data = await service.export_openai_format(company_id=company_id, min_rating=min_rating, limit=limit)
        jsonl_content = service.to_jsonl(training_data)
        logger.info(f"Exported {len(training_data)} samples in OpenAI format for company {company_id}")
        return Response(
            content=jsonl_content,
            media_type="application/jsonl",
            headers={
                "Content-Disposition": f"attachment; filename=training_data_openai_{company_id[:8]}.jsonl",
                "X-Sample-Count": str(len(training_data))
            }
        )
    except Exception as e:
        logger.error(f"Error exporting OpenAI training data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.get("/training-data/export/anthropic")
async def export_training_data_anthropic(
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    min_rating: int = Query(default=4, ge=1, le=5),
    limit: int = Query(default=1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Export training data in Anthropic JSONL format."""
    from app.services.training_data_service import TrainingDataService
    try:
        service = TrainingDataService(db)
        training_data = await service.export_anthropic_format(company_id=company_id, min_rating=min_rating, limit=limit)
        jsonl_content = service.to_jsonl(training_data)
        logger.info(f"Exported {len(training_data)} samples in Anthropic format for company {company_id}")
        return Response(
            content=jsonl_content,
            media_type="application/jsonl",
            headers={
                "Content-Disposition": f"attachment; filename=training_data_anthropic_{company_id[:8]}.jsonl",
                "X-Sample-Count": str(len(training_data))
            }
        )
    except Exception as e:
        logger.error(f"Error exporting Anthropic training data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.get("/training-data/export/dpo")
async def export_dpo_pairs(
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    limit: int = Query(default=500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db)
):
    """Export DPO preference pairs from corrections for Direct Preference Optimization training."""
    from app.services.training_data_service import TrainingDataService
    try:
        service = TrainingDataService(db)
        dpo_data = await service.export_dpo_pairs(company_id=company_id, limit=limit)
        jsonl_content = service.to_jsonl(dpo_data)
        logger.info(f"Exported {len(dpo_data)} DPO pairs for company {company_id}")
        return Response(
            content=jsonl_content,
            media_type="application/jsonl",
            headers={
                "Content-Disposition": f"attachment; filename=training_data_dpo_{company_id[:8]}.jsonl",
                "X-Sample-Count": str(len(dpo_data))
            }
        )
    except Exception as e:
        logger.error(f"Error exporting DPO training data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.get("/training-data/statistics")
async def get_training_data_stats(
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get statistics about available training data (counts, quality, export readiness)."""
    from app.services.training_data_service import TrainingDataService
    try:
        service = TrainingDataService(db)
        statistics = await service.get_export_statistics(company_id=company_id)
        logger.info(f"Training data statistics retrieved for company {company_id}")
        return statistics
    except Exception as e:
        logger.error(f"Error getting training data statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@feedback_router.post("/training-data/curate")
async def curate_training_data(
    company_id: str = Query(..., description="Company ID for tenant scoping"),
    target_count: int = Query(default=500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Automatically curate high-quality training samples (rating 5 > 4 > thumbs-up)."""
    from app.services.training_data_service import TrainingDataService
    try:
        service = TrainingDataService(db)
        curated_ids = await service.curate_high_quality_samples(company_id=company_id, target_count=target_count)
        logger.info(f"Curated {len(curated_ids)} training samples for company {company_id}")
        return {
            "success": True,
            "company_id": company_id,
            "target_count": target_count,
            "curated_count": len(curated_ids),
            "feedback_ids": curated_ids,
            "message": f"Successfully curated {len(curated_ids)} high-quality samples for training."
        }
    except Exception as e:
        logger.error(f"Error curating training data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
