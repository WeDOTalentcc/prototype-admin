"""
REST API for agent approval workflow.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import UserRole
from app.core.database import get_db
from app.schemas.agent_approval import (
    ApprovalListResponse,
    ApprovalResponse,
    ReviewApprovalRequest,
)
from app.services.agent_approval_service import agent_approval_service

logger = logging.getLogger(__name__)

# Router for agent-specific approval requests
agent_router = APIRouter(prefix="/custom-agents", tags=["Agent Approvals"])


@agent_router.post("/{agent_id}/request-approval", response_model=ApprovalResponse, status_code=201)
async def request_agent_approval(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an agent for approval. Agent must be in draft status."""
    try:
        approval = await agent_approval_service.request_approval(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            requested_by=str(current_user.id),
        )
        await db.commit()
        return ApprovalResponse(**approval.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error requesting approval: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to request approval")


# Router for approval management (admin only)
approvals_router = APIRouter(prefix="/agent-approvals", tags=["Agent Approvals"])


@approvals_router.get("/pending", response_model=ApprovalListResponse)
async def list_pending_approvals(
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
    """List all pending approval requests (admin only)."""
    approvals = await agent_approval_service.list_pending(
        db=db, company_id=current_user.company_id
    )

    # Enrich with agent names
    from lia_models.custom_agent import CustomAgent
    responses = []
    for a in approvals:
        resp = ApprovalResponse(**a.to_dict())
        agent_result = await db.execute(
            select(CustomAgent).where(CustomAgent.id == a.agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if agent:
            resp.agent_name = agent.name
        responses.append(resp)

    return ApprovalListResponse(approvals=responses, total=len(responses))


@approvals_router.post("/{approval_id}/review", response_model=ApprovalResponse)
async def review_approval(
    approval_id: str,
    body: ReviewApprovalRequest,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject an approval request (admin only)."""
    try:
        approval = await agent_approval_service.review(
            db=db,
            approval_id=approval_id,
            company_id=current_user.company_id,
            reviewer_id=str(current_user.id),
            action=body.action,
            notes=body.notes,
        )
        await db.commit()
        return ApprovalResponse(**approval.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Error reviewing approval: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to review approval")
