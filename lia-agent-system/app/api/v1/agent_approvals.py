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
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

# Router for agent-specific approval requests
agent_router = APIRouter(prefix="/custom-agents", tags=["Agent Approvals"])


@agent_router.post("/{agent_id}/request-approval", response_model=ApprovalResponse, status_code=201)
async def request_agent_approval(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    """Submit an agent for approval. Agent must be in draft status."""
    try:
        approval = await agent_approval_service.request_approval(
            db=db,
            agent_id=agent_id,
            company_id=current_user.company_id,
            requested_by=str(current_user.id),
        )
        await db.commit()

        # P0-3 chunk 2 audit 2026-05-21: approval request trail
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_request_approval",
            decision="requested",
            reasoning=[
                f"Approval ID: {approval.id}",
                f"Agent ID: {agent_id}",
            ],
            actor_user_id=str(current_user.id),
            target_id=str(approval.id),
            target_type="agent_approval",
        )

        # P2.5a: Notify all admins (non-blocking)
        try:
            from app.services.studio_notification_service import (
                studio_notification_service, get_company_admin_ids,
            )
            from sqlalchemy import select as _sel
            from lia_models.custom_agent import CustomAgent as _CA
            _agent_res = await db.execute(_sel(_CA).where(_CA.id == agent_id))
            _agent = _agent_res.scalar_one_or_none()
            if _agent:
                _admin_ids = await get_company_admin_ids(db, current_user.company_id)
                if _admin_ids:
                    await studio_notification_service.notify_approval_requested(
                        db=db,
                        admin_user_ids=_admin_ids,
                        agent_id=str(_agent.id),
                        agent_name=_agent.name,
                        requested_by=str(current_user.id),
                    )
                    await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval request notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.approval.requested",
                payload={
                    "approval_id": str(approval.id),
                    "agent_id": str(approval.agent_id),
                    "requested_by": approval.requested_by,
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] approval request dispatch failed: %s", _wh_err)

        return ApprovalResponse(**approval.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
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
company_id: str = Depends(require_company_id)):
    """List all pending approval requests (admin only)."""
    approvals = await agent_approval_service.list_pending(
        db=db, company_id=current_user.company_id
    )

    # Enrich with agent names
    from lia_models.custom_agent import CustomAgent
    responses = []
    for a in approvals:
        resp = ApprovalResponse(**a.to_dict())
        # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
        agent_result = await db.execute(
            select(CustomAgent).where(
                CustomAgent.id == a.agent_id,
                CustomAgent.company_id == current_user.company_id,
            )
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
company_id: str = Depends(require_company_id)):
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

        # P0-3 audit 2026-05-21: canonical lifecycle audit (EU AI Act Art. 12 — review decision trail)
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=current_user.company_id,
            action="studio_agent_review",
            decision=body.action,
            reasoning=[
                f"Approval ID: {approval_id}",
                f"Agent ID: {approval.agent_id}",
                f"Reviewer notes: {body.notes or 'no notes'}",
            ],
            actor_user_id=str(current_user.id),
            target_id=str(approval.agent_id),
            target_type="agent_approval",
        )

        # P2.5a: Notify creator of decision (non-blocking)
        try:
            from app.services.studio_notification_service import studio_notification_service
            from sqlalchemy import select as _sel
            from lia_models.custom_agent import CustomAgent as _CA
            _agent_res = await db.execute(_sel(_CA).where(_CA.id == approval.agent_id))
            _agent = _agent_res.scalar_one_or_none()
            if _agent and approval.requested_by:
                await studio_notification_service.notify_approval_reviewed(
                    db=db,
                    creator_user_id=approval.requested_by,
                    agent_id=str(_agent.id),
                    agent_name=_agent.name,
                    action=body.action,
                    reviewer_id=str(current_user.id),
                    review_notes=body.notes,
                )
                await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval review notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.approval.reviewed",
                payload={
                    "approval_id": str(approval.id),
                    "agent_id": str(approval.agent_id),
                    "action": body.action,
                    "reviewer_id": str(current_user.id),
                    "review_notes": body.notes,
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] approval review dispatch failed: %s", _wh_err)

        return ApprovalResponse(**approval.to_dict())
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error reviewing approval: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to review approval")
