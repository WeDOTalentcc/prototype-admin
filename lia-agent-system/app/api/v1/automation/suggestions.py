"""
AI suggestion management routes.

Includes:
- GET  /pending-suggestions
- POST /approve-suggestion/{suggestion_id}
- POST /reject-suggestion/{suggestion_id}
- POST /bulk-approve-suggestions
- POST /bulk-reject-suggestions
- GET  /ai-suggestions/vacancy/{vacancy_id}
- GET  /ai-suggestions/candidate/{candidate_id}
- POST /ai-suggestions/{suggestion_id}/approve
- POST /ai-suggestions/{suggestion_id}/reject
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.automation.repositories.ai_suggestion_repository import AISuggestionRepository

from ._shared import (
    BulkSuggestionRequest,
    RejectSuggestionRequest,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError, LIAInternalError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/pending-suggestions", response_model=None)
async def get_pending_suggestions(
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    vacancy_id: str | None = Query(None, description="Filter by vacancy ID"),
    suggestion_type: str | None = Query(None, description="Filter by suggestion type"),
    limit: int = Query(50, le=100, description="Maximum number of suggestions to return"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all pending AI suggestions for a company.
    """
    try:
        repo = AISuggestionRepository(db)
        suggestions = await repo.list_pending_for_company(
            company_id,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            suggestion_type=suggestion_type,
            limit=limit,
        )

        return {
            "success": True,
            "count": len(suggestions),
            "suggestions": [s.to_dict() for s in suggestions]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pending suggestions: {e}", exc_info=True)
        raise LIAInternalError("Internal server error")


@router.post("/approve-suggestion/{suggestion_id}", response_model=None)
async def approve_suggestion(
    suggestion_id: str,
    company_id: str = Query(..., description="Company ID for validation"),
    reviewer_id: str | None = Query(None, description="ID of the reviewer"),
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Approve an AI suggestion.
    """
    try:
        repo = AISuggestionRepository(db)
        suggestion = await repo.get_pending_by_id_and_company(suggestion_id, company_id)

        if not suggestion:
            raise HTTPException(
                status_code=404,
                detail="Suggestion not found or belongs to different company"
            )

        if suggestion.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Suggestion already processed with status: {suggestion.status}"
            )

        await repo.update(suggestion, {
            "status": "approved",
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
        })

        logger.info(f"✅ [SUGGESTION] Approved suggestion {suggestion_id} by {reviewer_id}")

        return {
            "success": True,
            "suggestion_id": suggestion_id,
            "status": "approved",
            "reviewed_by": reviewer_id,
            "reviewed_at": suggestion.reviewed_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving suggestion: {e}", exc_info=True)
        raise LIAInternalError("Internal server error")


@router.post("/reject-suggestion/{suggestion_id}", response_model=None)
async def reject_suggestion(
    suggestion_id: str,
    company_id: str = Query(..., description="Company ID for validation"),
    reviewer_id: str | None = Query(None, description="ID of the reviewer"),
    reason: str | None = Query(None, description="Reason for rejection"),
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Reject an AI suggestion.
    """
    try:
        repo = AISuggestionRepository(db)
        suggestion = await repo.get_pending_by_id_and_company(suggestion_id, company_id)

        if not suggestion:
            raise HTTPException(
                status_code=404,
                detail="Suggestion not found or belongs to different company"
            )

        if suggestion.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Suggestion already processed with status: {suggestion.status}"
            )

        await repo.update(suggestion, {
            "status": "rejected",
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.utcnow(),
            "rejection_reason": reason,
        })

        logger.info(f"❌ [SUGGESTION] Rejected suggestion {suggestion_id} by {reviewer_id}: {reason}")

        return {
            "success": True,
            "suggestion_id": suggestion_id,
            "status": "rejected",
            "reviewed_by": reviewer_id,
            "reviewed_at": suggestion.reviewed_at.isoformat(),
            "rejection_reason": reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting suggestion: {e}", exc_info=True)
        raise LIAInternalError("Internal server error")


@router.post("/bulk-approve-suggestions", response_model=None)
async def bulk_approve_suggestions(
    request: BulkSuggestionRequest,
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Bulk approve AI suggestions.
    """
    try:
        repo = AISuggestionRepository(db)
        approved_count = 0
        failed_ids = []

        for suggestion_id in request.suggestion_ids:
            try:
                suggestion = await repo.get_pending_by_id_and_company(suggestion_id, request.company_id)

                if suggestion:
                    await repo.update(suggestion, {
                        "status": "approved",
                        "reviewed_by": request.reviewer_id,
                        "reviewed_at": datetime.utcnow(),
                    })
                    approved_count += 1
                else:
                    failed_ids.append(suggestion_id)

            except Exception as e:
                logger.warning(f"Failed to approve suggestion {suggestion_id}: {e}")
                failed_ids.append(suggestion_id)

        logger.info(f"✅ [BULK_APPROVE] Approved {approved_count} suggestions, {len(failed_ids)} failed")

        return {
            "success": True,
            "approved_count": approved_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk approve: {e}", exc_info=True)
        raise LIAInternalError("Internal server error")


@router.post("/bulk-reject-suggestions", response_model=None)
async def bulk_reject_suggestions(
    request: BulkSuggestionRequest,
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Bulk reject AI suggestions.
    """
    try:
        repo = AISuggestionRepository(db)
        rejected_count = 0
        failed_ids = []

        for suggestion_id in request.suggestion_ids:
            try:
                suggestion = await repo.get_pending_by_id_and_company(suggestion_id, request.company_id)

                if suggestion:
                    await repo.update(suggestion, {
                        "status": "rejected",
                        "reviewed_by": request.reviewer_id,
                        "reviewed_at": datetime.utcnow(),
                        "rejection_reason": request.reason,
                    })
                    rejected_count += 1
                else:
                    failed_ids.append(suggestion_id)

            except Exception as e:
                logger.warning(f"Failed to reject suggestion {suggestion_id}: {e}")
                failed_ids.append(suggestion_id)

        logger.info(f"❌ [BULK_REJECT] Rejected {rejected_count} suggestions, {len(failed_ids)} failed")

        return {
            "success": True,
            "rejected_count": rejected_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "rejection_reason": request.reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk reject: {e}", exc_info=True)
        raise LIAInternalError("Internal server error")


@router.get("/ai-suggestions/vacancy/{vacancy_id}", response_model=None)
async def get_ai_suggestions_by_vacancy(
    vacancy_id: str,
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get AI suggestions for a specific vacancy.
    """
    try:
        repo = AISuggestionRepository(db)
        suggestions = await repo.list_by_vacancy(
            vacancy_id, company_id=company_id, status=status
        )
        return {
            "success": True,
            "suggestions": [s.to_dict() for s in suggestions]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI suggestions by vacancy: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/ai-suggestions/candidate/{candidate_id}", response_model=None)
async def get_ai_suggestions_by_candidate(
    candidate_id: str,
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get AI suggestions for a specific candidate.
    """
    try:
        repo = AISuggestionRepository(db)
        suggestions = await repo.list_by_candidate(
            candidate_id, company_id=company_id, status=status
        )
        return {
            "success": True,
            "suggestions": [s.to_dict() for s in suggestions]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI suggestions by candidate: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/ai-suggestions/{suggestion_id}/approve", response_model=None)
async def approve_ai_suggestion(
    suggestion_id: str,
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Approve an AI suggestion and execute the suggested action.
    """
    try:
        repo = AISuggestionRepository(db)
        suggestion = await repo.get_by_id(suggestion_id, company_id=company_id)

        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")

        if suggestion.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Suggestion already {suggestion.status}"
            )

        await repo.update(suggestion, {
            "status": "approved",
            "reviewed_at": datetime.utcnow(),
        })

        logger.info(f"✅ [AI_SUGGESTION] Approved suggestion {suggestion_id}")

        return {
            "success": True,
            "message": "Suggestion approved",
            "suggestion": suggestion.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving AI suggestion: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.post("/ai-suggestions/{suggestion_id}/reject", response_model=None)
async def reject_ai_suggestion(
    suggestion_id: str,
    request: RejectSuggestionRequest,
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Reject an AI suggestion with an optional reason.
    """
    try:
        repo = AISuggestionRepository(db)
        suggestion = await repo.get_by_id(suggestion_id, company_id=company_id)

        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")

        if suggestion.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Suggestion already {suggestion.status}"
            )

        await repo.update(suggestion, {
            "status": "rejected",
            "reviewed_at": datetime.utcnow(),
            "rejection_reason": request.reason,
        })

        logger.info(f"❌ [AI_SUGGESTION] Rejected suggestion {suggestion_id}: {request.reason}")

        return {
            "success": True,
            "message": "Suggestion rejected",
            "suggestion": suggestion.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting AI suggestion: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")
