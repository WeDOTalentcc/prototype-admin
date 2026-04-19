"""
LIA Chat Feedback — canonical HTTP endpoints for thumbs/rating/correction.

Closes the gap identified in Audit #569 (docs/audits/chat-message-actions-and-feedback-loop-audit.md):
the frontend posted to /api/v1/lia/feedback/* but the router did not exist,
so every thumbs click 404'd silently and the learning loop was dead in production.

Contract:
- company_id and user_id are read from the authenticated user — NEVER from body
  (protects against IDOR — see lia-compliance, multi-tenant isolation).
- Endpoints return explicit 4xx/5xx on failure (no silent try/except).
- The actual persist + pattern update is delegated to the canonical
  feedback_service (app.domains.analytics.services.feedback_service).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.domains.analytics.services.feedback_service import FeedbackService
from lia_models.feedback import InteractionFeedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia/feedback", tags=["lia-feedback"])

_feedback_service = FeedbackService()


# ─── Schemas ──────────────────────────────────────────────────────────────

class MessageContextPayload(BaseModel):
    """Optional context about the LIA response being rated. All fields optional."""
    user_message: str | None = None
    lia_response: str | None = None
    intent: str | None = None
    stage: str | None = None
    response_time_ms: int | None = None
    tools_used: list[str] | None = None
    confidence_score: float | None = None


class ThumbsRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    thumbs: str = Field(..., pattern="^(up|down)$")
    feedback_text: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    message_context: MessageContextPayload | None = None


class RatingRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=50)
    message_context: MessageContextPayload | None = None


class CorrectionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    original_response: str = Field(..., max_length=20000)
    correction: str = Field(..., min_length=1, max_length=20000)
    message_context: MessageContextPayload | None = None


class FeedbackAck(BaseModel):
    feedback_id: str
    status: str = "recorded"


class MessageFeedbackEntry(BaseModel):
    message_id: str
    thumbs: str | None = None
    rating: int | None = None
    feedback_text: str | None = None


class ConversationFeedbackResponse(BaseModel):
    items: list[MessageFeedbackEntry]


# ─── Helpers ──────────────────────────────────────────────────────────────

def _require_company_id(user: User) -> str:
    """Multi-tenant guard. Without a company we can't isolate the learning loop."""
    if not user.company_id:
        raise HTTPException(
            status_code=400,
            detail="Authenticated user has no company_id; cannot record feedback.",
        )
    return user.company_id


def _build_context(
    message_id: str,
    payload: MessageContextPayload | None,
) -> dict[str, Any]:
    ctx: dict[str, Any] = {"message_id": message_id}
    if payload is not None:
        ctx.update({k: v for k, v in payload.model_dump().items() if v is not None})
    return ctx


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.post("/thumbs", response_model=FeedbackAck, status_code=201)
async def submit_thumbs(
    body: ThumbsRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
) -> FeedbackAck:
    """Record a thumbs up/down. Optionally attaches a free-text comment."""
    company_id = _require_company_id(current_user)
    try:
        feedback = await _feedback_service.record_feedback(
            session_id=body.session_id,
            company_id=company_id,
            user_id=str(current_user.id),
            feedback_type="thumbs",
            feedback_value=body.thumbs,
            message_context=_build_context(body.message_id, body.message_context),
            db=db,
        )
        # Attach optional comment in the same row (avoids creating two records).
        if body.feedback_text or body.category:
            feedback.feedback_text = body.feedback_text
            feedback.feedback_category = body.category
            await db.commit()
            await db.refresh(feedback)
        return FeedbackAck(feedback_id=str(feedback.id))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to record thumbs feedback")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {e}")


@router.post("/rating", response_model=FeedbackAck, status_code=201)
async def submit_rating(
    body: RatingRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
) -> FeedbackAck:
    company_id = _require_company_id(current_user)
    try:
        feedback = await _feedback_service.record_feedback(
            session_id=body.session_id,
            company_id=company_id,
            user_id=str(current_user.id),
            feedback_type="rating",
            feedback_value={
                "rating": body.rating,
                "feedback_text": body.feedback_text,
                "category": body.category,
            },
            message_context=_build_context(body.message_id, body.message_context),
            db=db,
        )
        return FeedbackAck(feedback_id=str(feedback.id))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to record rating feedback")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {e}")


@router.post("/correction", response_model=FeedbackAck, status_code=201)
async def submit_correction(
    body: CorrectionRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
) -> FeedbackAck:
    company_id = _require_company_id(current_user)
    ctx = _build_context(body.message_id, body.message_context)
    # Preserve the original response in context if not explicitly provided.
    ctx.setdefault("lia_response", body.original_response)
    try:
        feedback = await _feedback_service.record_feedback(
            session_id=body.session_id,
            company_id=company_id,
            user_id=str(current_user.id),
            feedback_type="correction",
            feedback_value=body.correction,
            message_context=ctx,
            db=db,
        )
        return FeedbackAck(feedback_id=str(feedback.id))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to record correction feedback")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {e}")


@router.get("/metrics")
async def get_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    company_id = _require_company_id(current_user)
    try:
        return await _feedback_service.get_feedback_metrics(
            company_id=company_id, days=days, db=db
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to load feedback metrics")
        raise HTTPException(status_code=500, detail=f"Failed to load metrics: {e}")


@router.get("/by-conversation/{session_id}", response_model=ConversationFeedbackResponse)
async def get_feedback_by_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
) -> ConversationFeedbackResponse:
    """
    Hydrate per-message feedback state for a conversation.

    Returns the LATEST feedback row per message_id, scoped to the current
    user's company (multi-tenant isolation). Used by the chat UI to restore
    thumbs state after a refresh — closes UX gap F3 from the audit.
    """
    company_id = _require_company_id(current_user)
    try:
        from uuid import UUID as _UUID
        try:
            company_uuid = _UUID(company_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid company_id: {company_id}"
            )

        result = await db.execute(
            select(InteractionFeedback)
            .where(
                and_(
                    InteractionFeedback.session_id == session_id,
                    InteractionFeedback.company_id == company_uuid,
                    InteractionFeedback.message_id.isnot(None),
                )
            )
            .order_by(InteractionFeedback.created_at.asc())
        )
        rows = result.scalars().all()

        # Last-write-wins per message_id.
        latest: dict[str, InteractionFeedback] = {}
        for row in rows:
            if row.message_id:
                latest[row.message_id] = row

        items = [
            MessageFeedbackEntry(
                message_id=mid,
                thumbs=fb.thumbs,
                rating=fb.rating,
                feedback_text=fb.feedback_text,
            )
            for mid, fb in latest.items()
        ]
        return ConversationFeedbackResponse(items=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to load conversation feedback")
        raise HTTPException(status_code=500, detail=f"Failed to load feedback: {e}")
