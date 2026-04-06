import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.search_feedback import SearchFeedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search/feedback", tags=["search-feedback"])


class SubmitFeedbackRequest(BaseModel):
    candidate_id: str
    feedback_type: str = Field(..., pattern="^(like|dislike)$")
    job_id: str | None = None
    search_query: str | None = None
    candidate_score: float | None = None
    candidate_name: str | None = None
    reason: str | None = None


@router.post("/", response_model=None)
async def submit_feedback(request: Request, body: SubmitFeedbackRequest, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    job_filter = SearchFeedback.job_id == body.job_id if body.job_id else SearchFeedback.job_id.is_(None)
    result = await db.execute(
        select(SearchFeedback).where(
            and_(
                SearchFeedback.user_id == user_id,
                SearchFeedback.candidate_id == body.candidate_id,
                job_filter,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.feedback_type == body.feedback_type:
            await db.delete(existing)
            await db.flush()
            return {"action": "removed", "feedback": None}
        else:
            existing.feedback_type = body.feedback_type
            existing.search_query = body.search_query
            existing.candidate_score = body.candidate_score
            existing.candidate_name = body.candidate_name
            existing.reason = body.reason
            await db.flush()
            return {"action": "toggled", "feedback": existing.to_dict()}

    feedback = SearchFeedback(
        candidate_id=body.candidate_id,
        feedback_type=body.feedback_type,
        job_id=body.job_id,
        user_id=user_id,
        search_query=body.search_query,
        candidate_score=body.candidate_score,
        candidate_name=body.candidate_name,
        reason=body.reason,
    )
    db.add(feedback)
    await db.flush()
    return {"action": "created", "feedback": feedback.to_dict()}


@router.get("/user/all", response_model=None)
async def get_user_feedbacks(request: Request, job_id: str | None = None, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    query = select(SearchFeedback).where(SearchFeedback.user_id == user_id)
    if job_id:
        query = query.where(SearchFeedback.job_id == job_id)
    query = query.order_by(SearchFeedback.created_at.desc())
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    return {
        "feedbacks": [f.to_dict() for f in feedbacks],
        "total": len(feedbacks),
    }


@router.get("/{job_id}", response_model=None)
async def get_job_feedbacks(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SearchFeedback).where(SearchFeedback.job_id == job_id).order_by(SearchFeedback.created_at.desc())
    )
    feedbacks = result.scalars().all()

    likes = sum(1 for f in feedbacks if f.feedback_type == "like")
    dislikes = sum(1 for f in feedbacks if f.feedback_type == "dislike")

    return {
        "feedbacks": [f.to_dict() for f in feedbacks],
        "total": len(feedbacks),
        "likes": likes,
        "dislikes": dislikes,
    }


@router.delete("/{feedback_id}", response_model=None)
async def delete_feedback(request: Request, feedback_id: str, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    result = await db.execute(
        select(SearchFeedback).where(
            and_(SearchFeedback.id == feedback_id, SearchFeedback.user_id == user_id)
        )
    )
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    await db.delete(feedback)
    await db.flush()
    return {"deleted": True, "id": feedback_id}
