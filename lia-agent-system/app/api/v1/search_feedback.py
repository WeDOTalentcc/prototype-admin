import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.recruitment.repositories.search_feedback_repository import SearchFeedbackRepository
from app.models.search_feedback import SearchFeedback
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search/feedback", tags=["search-feedback"])


class SubmitFeedbackRequest(WeDoBaseModel):
    candidate_id: str
    feedback_type: str = Field(..., pattern="^(like|dislike)$")
    job_id: str | None = None
    search_query: str | None = None
    candidate_score: float | None = None
    candidate_name: str | None = None
    reason: str | None = None
    search_fingerprint: str | None = None


def get_search_feedback_repo(db: AsyncSession = Depends(get_db)) -> SearchFeedbackRepository:
    return SearchFeedbackRepository(db)


@router.post("/", response_model=None)
async def submit_feedback(
    request: Request,
    body: SubmitFeedbackRequest,
    repo: SearchFeedbackRepository = Depends(get_search_feedback_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    existing = await repo.get_by_user_and_candidate(
        user_id=user_id,
        candidate_id=body.candidate_id,
        job_id=body.job_id,
    )

    if existing:
        if existing.feedback_type == body.feedback_type:
            await repo.delete(existing)
            return {"action": "removed", "feedback": None}
        else:
            updated = await repo.update(existing, {
                "feedback_type": body.feedback_type,
                "search_query": body.search_query,
                "candidate_score": body.candidate_score,
                "candidate_name": body.candidate_name,
                "reason": body.reason,
            })
            return {"action": "toggled", "feedback": updated.to_dict()}

    created = await repo.create({
        "company_id": company_id,
        "search_fingerprint": body.search_fingerprint,
        "candidate_id": body.candidate_id,
        "feedback_type": body.feedback_type,
        "job_id": body.job_id,
        "user_id": user_id,
        "search_query": body.search_query,
        "candidate_score": body.candidate_score,
        "candidate_name": body.candidate_name,
        "reason": body.reason,
    })
    return {"action": "created", "feedback": created.to_dict()}


@router.get("/by-search", response_model=None)
async def get_feedback_by_search(
    request: Request,
    fingerprint: str,
    repo: SearchFeedbackRepository = Depends(get_search_feedback_repo),
    company_id: str = Depends(require_company_id),
):
    # Re-hidratacao (Fase 2): {candidate_id: feedback_type} do recrutador para os
    # criterios desta busca (fingerprint). RLS isola por company.
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    rows = await repo.list_for_user_and_fingerprint(
        user_id=user_id, search_fingerprint=fingerprint
    )
    return {
        "feedbacks": {r.candidate_id: r.feedback_type for r in rows},
        "total": len(rows),
    }


@router.get("/user/all", response_model=None)
async def get_user_feedbacks(
    request: Request,
    job_id: str | None = None,
    repo: SearchFeedbackRepository = Depends(get_search_feedback_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    feedbacks = await repo.list_for_user(user_id=user_id, job_id=job_id)
    return {
        "feedbacks": [f.to_dict() for f in feedbacks],
        "total": len(feedbacks),
    }


@router.get("/{job_id}", response_model=None)
async def get_job_feedbacks(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: SearchFeedbackRepository = Depends(get_search_feedback_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    feedbacks = await repo.list_for_job(job_id=job_id)

    likes = sum(1 for f in feedbacks if f.feedback_type == "like")
    dislikes = sum(1 for f in feedbacks if f.feedback_type == "dislike")

    return {
        "feedbacks": [f.to_dict() for f in feedbacks],
        "total": len(feedbacks),
        "likes": likes,
        "dislikes": dislikes,
    }


@router.delete("/{feedback_id}", response_model=None)
async def delete_feedback(
    request: Request,
    feedback_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: SearchFeedbackRepository = Depends(get_search_feedback_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    feedback = await repo.get_by_id_and_user(feedback_id=feedback_id, user_id=user_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    await repo.delete(feedback)
    return {"deleted": True, "id": feedback_id}

reorder_collection_before_item(router)
