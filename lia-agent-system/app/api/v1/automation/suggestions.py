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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from ._shared import (
    BulkSuggestionRequest,
    RejectSuggestionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/pending-suggestions")
async def get_pending_suggestions(
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    vacancy_id: str | None = Query(None, description="Filter by vacancy ID"),
    suggestion_type: str | None = Query(None, description="Filter by suggestion type"),
    limit: int = Query(50, le=100, description="Maximum number of suggestions to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pending AI suggestions for a company.
    
    Returns suggestions that are waiting for user approval/rejection.
    Supports filtering by candidate, vacancy, and suggestion type.
    """
    try:
        from app.models.automation import AISuggestion
        
        query = select(AISuggestion).where(
            AISuggestion.company_id == company_id,
            AISuggestion.status == "pending"
        )
        
        if candidate_id:
            query = query.where(AISuggestion.candidate_id == candidate_id)
        if vacancy_id:
            query = query.where(AISuggestion.vacancy_id == vacancy_id)
        if suggestion_type:
            query = query.where(AISuggestion.suggestion_type == suggestion_type)
        
        query = query.order_by(AISuggestion.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        suggestions = result.scalars().all()
        
        return {
            "success": True,
            "count": len(suggestions),
            "suggestions": [s.to_dict() for s in suggestions]
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pending suggestions: {str(e)}"
        )


@router.post("/approve-suggestion/{suggestion_id}")
async def approve_suggestion(
    suggestion_id: str,
    company_id: str = Query(..., description="Company ID for validation"),
    reviewer_id: str | None = Query(None, description="ID of the reviewer"),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve an AI suggestion.
    
    Changes the suggestion status to 'approved' and records the reviewer.
    """
    try:
        from app.models.automation import AISuggestion
        
        result = await db.execute(
            select(AISuggestion).where(
                AISuggestion.id == suggestion_id,
                AISuggestion.company_id == company_id
            )
        )
        suggestion = result.scalar_one_or_none()
        
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
        
        suggestion.status = "approved"
        suggestion.reviewed_by = reviewer_id
        suggestion.reviewed_at = datetime.utcnow()
        
        await db.commit()
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Error approving suggestion: {str(e)}"
        )


@router.post("/reject-suggestion/{suggestion_id}")
async def reject_suggestion(
    suggestion_id: str,
    company_id: str = Query(..., description="Company ID for validation"),
    reviewer_id: str | None = Query(None, description="ID of the reviewer"),
    reason: str | None = Query(None, description="Reason for rejection"),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject an AI suggestion.
    
    Changes the suggestion status to 'rejected' and records the reason.
    """
    try:
        from app.models.automation import AISuggestion
        
        result = await db.execute(
            select(AISuggestion).where(
                AISuggestion.id == suggestion_id,
                AISuggestion.company_id == company_id
            )
        )
        suggestion = result.scalar_one_or_none()
        
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
        
        suggestion.status = "rejected"
        suggestion.reviewed_by = reviewer_id
        suggestion.reviewed_at = datetime.utcnow()
        suggestion.rejection_reason = reason
        
        await db.commit()
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Error rejecting suggestion: {str(e)}"
        )


@router.post("/bulk-approve-suggestions")
async def bulk_approve_suggestions(
    request: BulkSuggestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk approve AI suggestions.
    
    Approves multiple suggestions at once for efficiency.
    Returns count of successfully approved suggestions.
    """
    try:
        from app.models.automation import AISuggestion
        
        approved_count = 0
        failed_ids = []
        
        for suggestion_id in request.suggestion_ids:
            try:
                result = await db.execute(
                    select(AISuggestion).where(
                        AISuggestion.id == suggestion_id,
                        AISuggestion.company_id == request.company_id,
                        AISuggestion.status == "pending"
                    )
                )
                suggestion = result.scalar_one_or_none()
                
                if suggestion:
                    suggestion.status = "approved"
                    suggestion.reviewed_by = request.reviewer_id
                    suggestion.reviewed_at = datetime.utcnow()
                    approved_count += 1
                else:
                    failed_ids.append(suggestion_id)
                    
            except Exception as e:
                logger.warning(f"Failed to approve suggestion {suggestion_id}: {e}")
                failed_ids.append(suggestion_id)
        
        await db.commit()
        
        logger.info(f"✅ [BULK_APPROVE] Approved {approved_count} suggestions, {len(failed_ids)} failed")
        
        return {
            "success": True,
            "approved_count": approved_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids
        }
        
    except Exception as e:
        logger.error(f"Error in bulk approve: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error in bulk approve: {str(e)}"
        )


@router.post("/bulk-reject-suggestions")
async def bulk_reject_suggestions(
    request: BulkSuggestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk reject AI suggestions.
    
    Rejects multiple suggestions at once for efficiency.
    Returns count of successfully rejected suggestions.
    """
    try:
        from app.models.automation import AISuggestion
        
        rejected_count = 0
        failed_ids = []
        
        for suggestion_id in request.suggestion_ids:
            try:
                result = await db.execute(
                    select(AISuggestion).where(
                        AISuggestion.id == suggestion_id,
                        AISuggestion.company_id == request.company_id,
                        AISuggestion.status == "pending"
                    )
                )
                suggestion = result.scalar_one_or_none()
                
                if suggestion:
                    suggestion.status = "rejected"
                    suggestion.reviewed_by = request.reviewer_id
                    suggestion.reviewed_at = datetime.utcnow()
                    suggestion.rejection_reason = request.reason
                    rejected_count += 1
                else:
                    failed_ids.append(suggestion_id)
                    
            except Exception as e:
                logger.warning(f"Failed to reject suggestion {suggestion_id}: {e}")
                failed_ids.append(suggestion_id)
        
        await db.commit()
        
        logger.info(f"❌ [BULK_REJECT] Rejected {rejected_count} suggestions, {len(failed_ids)} failed")
        
        return {
            "success": True,
            "rejected_count": rejected_count,
            "failed_count": len(failed_ids),
            "failed_ids": failed_ids,
            "rejection_reason": request.reason
        }
        
    except Exception as e:
        logger.error(f"Error in bulk reject: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error in bulk reject: {str(e)}"
        )


@router.get("/ai-suggestions/vacancy/{vacancy_id}")
async def get_ai_suggestions_by_vacancy(
    vacancy_id: str,
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI suggestions for a specific vacancy.
    """
    try:
        from app.models.automation import AISuggestion
        
        query = select(AISuggestion).where(AISuggestion.vacancy_id == vacancy_id)
        
        if status:
            query = query.where(AISuggestion.status == status)
        else:
            query = query.where(AISuggestion.status == "pending")
        
        query = query.order_by(AISuggestion.created_at.desc())
        
        result = await db.execute(query)
        suggestions = result.scalars().all()
        
        return {
            "success": True,
            "suggestions": [s.to_dict() for s in suggestions]
        }
    except Exception as e:
        logger.error(f"Error getting AI suggestions by vacancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-suggestions/candidate/{candidate_id}")
async def get_ai_suggestions_by_candidate(
    candidate_id: str,
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI suggestions for a specific candidate.
    """
    try:
        from app.models.automation import AISuggestion
        
        query = select(AISuggestion).where(AISuggestion.candidate_id == candidate_id)
        
        if status:
            query = query.where(AISuggestion.status == status)
        else:
            query = query.where(AISuggestion.status == "pending")
        
        query = query.order_by(AISuggestion.created_at.desc())
        
        result = await db.execute(query)
        suggestions = result.scalars().all()
        
        return {
            "success": True,
            "suggestions": [s.to_dict() for s in suggestions]
        }
    except Exception as e:
        logger.error(f"Error getting AI suggestions by candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggestions/{suggestion_id}/approve")
async def approve_ai_suggestion(
    suggestion_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve an AI suggestion and execute the suggested action.
    """
    try:
        from app.models.automation import AISuggestion
        
        result = await db.execute(
            select(AISuggestion).where(AISuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        if suggestion.status != "pending":
            raise HTTPException(
                status_code=400, 
                detail=f"Suggestion already {suggestion.status}"
            )
        
        suggestion.status = "approved"
        suggestion.reviewed_at = datetime.utcnow()
        
        await db.commit()
        
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggestions/{suggestion_id}/reject")
async def reject_ai_suggestion(
    suggestion_id: str,
    request: RejectSuggestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject an AI suggestion with an optional reason.
    """
    try:
        from app.models.automation import AISuggestion
        
        result = await db.execute(
            select(AISuggestion).where(AISuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        if suggestion.status != "pending":
            raise HTTPException(
                status_code=400, 
                detail=f"Suggestion already {suggestion.status}"
            )
        
        suggestion.status = "rejected"
        suggestion.reviewed_at = datetime.utcnow()
        suggestion.rejection_reason = request.reason
        
        await db.commit()
        
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
        raise HTTPException(status_code=500, detail=str(e))
