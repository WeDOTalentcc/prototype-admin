"""
Approvals API endpoints for managing approval workflow requests.
Handles creation, listing, approval, and rejection of approval requests.
"""
import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.domains.approvals.dependencies import get_approvals_repo
from app.domains.approvals.repositories.approvals_repository import ApprovalsRepository
from app.domains.communication.services.email_service import EmailService, get_email_service
from lia_models.approval import ApprovalRequest
from app.shared.compliance.audit_service import AuditService, get_audit_service
from app.shared.pii_masking import get_masked_logger
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = get_masked_logger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])


async def _sync_offer_proposal_status(db, approval) -> None:
    """Best-effort callback: when a generic approval is approved/rejected via
    this router, propagate the decision to any OfferProposal that references
    it via ``approval_request_id``. Keeps the offer status in sync with the
    canonical approvals workflow regardless of which UI path the approver
    used (offer-specific endpoint vs. generic approvals UI).
    """
    try:
        from sqlalchemy import select as _select
        from lia_models.offer_proposal import OfferProposal, OfferStatus

        result = await db.execute(
            _select(OfferProposal).where(OfferProposal.approval_request_id == approval.id)
        )
        proposal = result.scalar_one_or_none()
        if proposal is None:
            return
        if approval.status == "approved":
            proposal.status = OfferStatus.APPROVED.value
            round_type = "approval"
        elif approval.status == "rejected":
            proposal.status = OfferStatus.REJECTED.value
            round_type = "rejection"
        else:
            return

        # Mirror the decision into ``rounds`` so the per-round audit trail
        # stays complete even when the approver acted via the generic
        # approvals UI instead of /offer-proposals/{id}/approval/decision.
        from app.services.offer_letter_service import offer_letter_service as _svc

        proposal.rounds = _svc.append_round(
            list(proposal.rounds or []),
            round_type=round_type,
            actor="approver",
            actor_name=approval.approver_name,
            actor_email=approval.approver_email,
            message=(
                f"[generic_approvals_api] "
                + (approval.approval_notes or "" if approval.status == "approved" else approval.rejection_reason or "")
            ).strip(),
        )
        proposal.updated_at = datetime.utcnow()
        await db.flush()
    except Exception as sync_err:  # pragma: no cover - defensive
        logger.warning(f"OfferProposal sync skipped for approval {approval.id}: {sync_err}")


class ApprovalRequestCreate(BaseModel):
    request_type: str = "vacancy_approval"
    requester_name: str
    requester_email: str
    target_id: str | None = None
    target_type: str | None = None
    target_name: str
    target_description: str | None = None
    target_data: dict | None = None
    approver_name: str
    approver_email: str
    approval_level: int = 1
    priority: str = "normal"
    due_date: datetime | None = None


class ApprovalRequestUpdate(BaseModel):
    approval_notes: str | None = None
    rejection_reason: str | None = None


class ApprovalRequestResponse(BaseModel):
    id: str
    company_id: str
    request_type: str
    requester_id: str | None
    requester_name: str
    requester_email: str
    target_id: str | None
    target_type: str | None
    target_name: str
    target_description: str | None
    target_data: dict | None
    approver_id: str | None
    approver_name: str
    approver_email: str
    approval_level: int
    status: str
    priority: str
    due_date: datetime | None
    approval_notes: str | None
    rejection_reason: str | None
    email_sent: bool
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def to_response(approval: ApprovalRequest) -> ApprovalRequestResponse:
    return ApprovalRequestResponse(
        id=str(approval.id),
        company_id=str(approval.company_id),
        request_type=approval.request_type,
        requester_id=str(approval.requester_id) if approval.requester_id else None,
        requester_name=approval.requester_name,
        requester_email=approval.requester_email,
        target_id=str(approval.target_id) if approval.target_id else None,
        target_type=approval.target_type,
        target_name=approval.target_name,
        target_description=approval.target_description,
        target_data=approval.target_data or {},
        approver_id=str(approval.approver_id) if approval.approver_id else None,
        approver_name=approval.approver_name,
        approver_email=approval.approver_email,
        approval_level=approval.approval_level,
        status=approval.status,
        priority=approval.priority,
        due_date=approval.due_date,
        approval_notes=approval.approval_notes,
        rejection_reason=approval.rejection_reason,
        email_sent=approval.email_sent,
        resolved_at=approval.resolved_at,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.post("", response_model=ApprovalRequestResponse)
async def create_approval_request(
    request: ApprovalRequestCreate,
    company_id: str = Query(..., description="Company ID"),
    requester_id: str | None = Query(None, description="Requester user ID"),
    repo: ApprovalsRepository = Depends(get_approvals_repo),
    email_svc: EmailService = Depends(get_email_service),
):
    """Create a new approval request and send notification email to approver."""
    try:
        approval = ApprovalRequest(
            id=uuid.uuid4(),
            company_id=UUID(company_id),
            request_type=request.request_type,
            requester_id=UUID(requester_id) if requester_id else None,
            requester_name=request.requester_name,
            requester_email=request.requester_email,
            target_id=UUID(request.target_id) if request.target_id else None,
            target_type=request.target_type,
            target_name=request.target_name,
            target_description=request.target_description,
            target_data=request.target_data or {},
            approver_name=request.approver_name,
            approver_email=request.approver_email,
            approval_level=request.approval_level,
            status="pending",
            priority=request.priority,
            due_date=request.due_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        approval = await repo.add_and_flush(approval)

        try:
            await send_approval_request_email(repo.db, approval, email_svc=email_svc)
            approval.email_sent = True
            approval.email_sent_at = datetime.utcnow()
            approval = await repo.flush_and_refresh(approval)
        except Exception as e:
            logger.error(f"Failed to send approval request email: {e}")

        logger.info(f"Created approval request {approval.id} for {request.target_name}")
        return to_response(approval)

    except Exception as e:
        logger.error(f"Error creating approval request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ApprovalRequestResponse])
async def list_approval_requests(
    company_id: str = Query(..., description="Company ID"),
    status: str | None = Query(None, description="Filter by status"),
    request_type: str | None = Query(None, description="Filter by request type"),
    approver_email: str | None = Query(None, description="Filter by approver email"),
    requester_email: str | None = Query(None, description="Filter by requester email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: ApprovalsRepository = Depends(get_approvals_repo)
):
    """List approval requests for a company with optional filters."""
    try:
        try:
            parsed_company_id = UUID(company_id)
        except (ValueError, TypeError):
            default_id = await repo.get_default_company_id()
            if default_id:
                parsed_company_id = default_id
            else:
                return []

        approvals = await repo.list_by_company(
            company_id=parsed_company_id,
            status=status,
            request_type=request_type,
            approver_email=approver_email,
            requester_email=requester_email,
            limit=limit,
            offset=offset,
        )

        return [to_response(a) for a in approvals]

    except Exception as e:
        logger.error(f"Error listing approval requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=list[ApprovalRequestResponse])
async def list_pending_approvals(
    company_id: str = Query(..., description="Company ID"),
    approver_email: str | None = Query(None, description="Filter by approver email"),
    repo: ApprovalsRepository = Depends(get_approvals_repo)
):
    """List pending approval requests for a company."""
    try:
        approvals = await repo.list_pending_by_company(
            company_id=UUID(company_id),
            approver_email=approver_email,
        )
        return [to_response(a) for a in approvals]

    except Exception as e:
        logger.error(f"Error listing pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval_request(
    approval_id: _DualId,
    repo: ApprovalsRepository = Depends(get_approvals_repo)
):
    """Get a specific approval request by ID."""
    try:
        approval = await repo.get_by_id(UUID(approval_id))

        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")

        return to_response(approval)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting approval request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{approval_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    approval_id: _DualId,
    update: ApprovalRequestUpdate,
    company_id: str = Query(..., description="Company ID"),
    approved_by: str = Query(..., description="Email of the approver"),
    repo: ApprovalsRepository = Depends(get_approvals_repo),
    audit_svc: AuditService = Depends(get_audit_service),
    email_svc: EmailService = Depends(get_email_service),
):
    """Approve an approval request."""
    try:
        approval = await repo.get_by_id(UUID(approval_id))

        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if str(approval.company_id) != company_id:
            logger.warning(f"Company ID mismatch: approval belongs to {approval.company_id}, request from {company_id}")
            raise HTTPException(status_code=403, detail="Approval request does not belong to this company")

        if approval.approver_email.lower() != approved_by.lower():
            logger.warning(f"Unauthorized approval attempt: {approved_by} tried to approve request assigned to {approval.approver_email}")
            raise HTTPException(status_code=403, detail="Only the assigned approver can approve this request")

        if approval.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Cannot approve request with status '" + approval.status + "'"
            )

        approval.status = "approved"
        approval.approval_notes = update.approval_notes
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = approved_by
        approval.updated_at = datetime.utcnow()

        approval = await repo.flush_and_refresh(approval)

        await _sync_offer_proposal_status(repo.db, approval)

        try:
            await send_approval_result_email(repo.db, approval, approved=True, email_svc=email_svc)
            approval.notification_sent = True
        except Exception as e:
            logger.error(f"Failed to send approval result email for {approval_id}: {str(e)}", exc_info=True)
            approval.notification_sent = False

        logger.info(f"Approval request {approval_id} approved by {approved_by}")

        try:
            await audit_svc.log_decision(
                company_id=company_id,
                agent_name="approvals_module",
                decision_type="approve_candidate",
                action="approval_request_approved",
                decision="approved",
                reasoning=[
                    "Approval request approved",
                    f"Approved by role: {getattr(approval, 'approver_role', 'N/A')}",
                    f"Request type: {getattr(approval, 'request_type', 'N/A')}",
                    f"Notes provided: {'yes' if update.approval_notes else 'no'}",
                ],
                criteria_used=["approver_authorization", "request_type", "approval_policy"],
                job_vacancy_id=approval.target_id,
                human_review_required=False,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for approval: {audit_err}")

        return to_response(approval)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{approval_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    approval_id: _DualId,
    update: ApprovalRequestUpdate,
    company_id: str = Query(..., description="Company ID"),
    rejected_by: str = Query(..., description="Email of the rejector"),
    repo: ApprovalsRepository = Depends(get_approvals_repo),
    audit_svc: AuditService = Depends(get_audit_service),
    email_svc: EmailService = Depends(get_email_service),
):
    """Reject an approval request."""
    try:
        approval = await repo.get_by_id(UUID(approval_id))

        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if str(approval.company_id) != company_id:
            logger.warning(f"Company ID mismatch: approval belongs to {approval.company_id}, request from {company_id}")
            raise HTTPException(status_code=403, detail="Approval request does not belong to this company")

        if approval.approver_email.lower() != rejected_by.lower():
            logger.warning(f"Unauthorized rejection attempt: {rejected_by} tried to reject request assigned to {approval.approver_email}")
            raise HTTPException(status_code=403, detail="Only the assigned approver can reject this request")

        if approval.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Cannot reject request with status '" + approval.status + "'"
            )

        approval.status = "rejected"
        approval.rejection_reason = update.rejection_reason
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = rejected_by
        approval.updated_at = datetime.utcnow()

        approval = await repo.flush_and_refresh(approval)

        await _sync_offer_proposal_status(repo.db, approval)

        try:
            await send_approval_result_email(repo.db, approval, approved=False, email_svc=email_svc)
            approval.notification_sent = True
        except Exception as e:
            logger.error(f"Failed to send rejection email for {approval_id}: {str(e)}", exc_info=True)
            approval.notification_sent = False

        logger.info(f"Approval request {approval_id} rejected by {rejected_by}")

        try:
            await audit_svc.log_decision(
                company_id=company_id,
                agent_name="approvals_module",
                decision_type="reject_candidate",
                action="approval_request_rejected",
                decision="rejected",
                reasoning=[
                    "Approval request rejected",
                    f"Rejected by role: {getattr(approval, 'approver_role', 'N/A')}",
                    f"Request type: {getattr(approval, 'request_type', 'N/A')}",
                    f"Rejection reason provided: {'yes' if update.rejection_reason else 'no'}",
                ],
                criteria_used=["approver_authorization", "request_type", "rejection_policy"],
                job_vacancy_id=approval.target_id,
                human_review_required=True,
            )
        except Exception as audit_err:
            logger.warning(f"Audit log failed for rejection: {audit_err}")

        return to_response(approval)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{approval_id}/cancel", response_model=ApprovalRequestResponse)
async def cancel_request(
    approval_id: _DualId,
    company_id: str = Query(..., description="Company ID"),
    cancelled_by: str = Query(..., description="Email of the canceller"),
    repo: ApprovalsRepository = Depends(get_approvals_repo)
):
    """Cancel an approval request (by the requester)."""
    try:
        approval = await repo.get_by_id(UUID(approval_id))

        if not approval:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if str(approval.company_id) != company_id:
            logger.warning(f"Company ID mismatch: approval belongs to {approval.company_id}, request from {company_id}")
            raise HTTPException(status_code=403, detail="Approval request does not belong to this company")

        if approval.requester_email.lower() != cancelled_by.lower():
            logger.warning(f"Unauthorized cancel attempt: {cancelled_by} tried to cancel request created by {approval.requester_email}")
            raise HTTPException(status_code=403, detail="Only the requester can cancel this request")

        if approval.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel request with status '" + approval.status + "'"
            )

        approval.status = "cancelled"
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = cancelled_by
        approval.updated_at = datetime.utcnow()

        approval = await repo.flush_and_refresh(approval)

        logger.info(f"Approval request {approval_id} cancelled by {cancelled_by}")
        return to_response(approval)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_approval_request_email(db, approval: ApprovalRequest, email_svc: "EmailService" = None):
    """Send email notification to approver about new approval request."""
    request_type_labels = {
        "vacancy_approval": "Aprovacao de Vaga",
        "candidate_hire": "Aprovacao de Contratacao",
        "offer_approval": "Aprovacao de Proposta",
        "budget_approval": "Aprovacao de Orcamento",
        "custom": "Aprovacao Personalizada"
    }

    type_label = request_type_labels.get(approval.request_type, "Aprovacao")
    subject = "[LIA] " + type_label + ": " + approval.target_name

    description_block = "<p><strong>Descricao:</strong> " + approval.target_description + "</p>" if approval.target_description else ""
    date_str = approval.created_at.strftime("%d/%m/%Y %H:%M")

    body_html = (
        "<html><body>"
        "<h2>Solicitacao de Aprovacao</h2>"
        "<p>Ola " + approval.approver_name + ",</p>"
        "<p>Voce recebeu uma solicitacao de aprovacao de " + approval.requester_name + ".</p>"
        "<ul>"
        "<li>Tipo: " + type_label + "</li>"
        "<li>Item: " + approval.target_name + "</li>"
        "<li>Solicitante: " + approval.requester_name + " (" + approval.requester_email + ")</li>"
        "<li>Data: " + date_str + "</li>"
        "</ul>"
        + description_block +
        "<p>Por favor, acesse a plataforma LIA para aprovar ou rejeitar esta solicitacao.</p>"
        "<p>Atenciosamente,<br>Sistema LIA</p>"
        "</body></html>"
    )

    try:
        _svc = email_svc or get_email_service()
        success = await _svc._send_email_provider(
            to_email=approval.approver_email,
            subject=subject,
            body_html=body_html
        )
        return success
    except Exception as e:
        logger.error(f"Failed to send approval request email: {e}")
        raise


async def send_approval_result_email(db, approval: ApprovalRequest, approved: bool, email_svc: "EmailService" = None):
    """Send email notification to requester about approval result."""
    status_label = "Aprovada" if approved else "Rejeitada"
    status_color = "#16a34a" if approved else "#dc2626"
    subject = "[LIA] Solicitacao " + status_label + ": " + approval.target_name

    notes_section = ""
    if approved and approval.approval_notes:
        notes_section = "<p><strong>Observacoes:</strong> " + approval.approval_notes + "</p>"
    elif not approved and approval.rejection_reason:
        notes_section = "<p><strong>Motivo da Rejeicao:</strong> " + approval.rejection_reason + "</p>"

    resolved_date = approval.resolved_at.strftime("%d/%m/%Y %H:%M") if approval.resolved_at else "N/A"

    body_html = (
        "<html><body>"
        "<h2>Solicitacao " + status_label + "</h2>"
        "<p>Ola " + approval.requester_name + ",</p>"
        "<p>Sua solicitacao de aprovacao foi " + status_label.lower() + " por " + approval.approver_name + ".</p>"
        "<ul>"
        "<li>Item: " + approval.target_name + "</li>"
        "<li>Aprovador: " + approval.approver_name + "</li>"
        "<li>Data da Decisao: " + resolved_date + "</li>"
        "</ul>"
        + notes_section +
        "<p>Atenciosamente,<br>Sistema LIA</p>"
        "</body></html>"
    )

    try:
        _svc = email_svc or get_email_service()
        success = await _svc._send_email_provider(
            to_email=approval.requester_email,
            subject=subject,
            body_html=body_html
        )
        return success
    except Exception as e:
        logger.error(f"Failed to send approval result email: {e}")
        raise

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
