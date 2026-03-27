"""
Approvals API endpoints for managing approval workflow requests.
Handles creation, listing, approval, and rejection of approval requests.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.approval import ApprovalRequest, ApprovalStatus, ApprovalType
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalRequestCreate(BaseModel):
    request_type: str = "vacancy_approval"
    requester_name: str
    requester_email: str
    target_id: Optional[str] = None
    target_type: Optional[str] = None
    target_name: str
    target_description: Optional[str] = None
    target_data: Optional[dict] = None
    approver_name: str
    approver_email: str
    approval_level: int = 1
    priority: str = "normal"
    due_date: Optional[datetime] = None


class ApprovalRequestUpdate(BaseModel):
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApprovalRequestResponse(BaseModel):
    id: str
    company_id: str
    request_type: str
    requester_id: Optional[str]
    requester_name: str
    requester_email: str
    target_id: Optional[str]
    target_type: Optional[str]
    target_name: str
    target_description: Optional[str]
    target_data: Optional[dict]
    approver_id: Optional[str]
    approver_name: str
    approver_email: str
    approval_level: int
    status: str
    priority: str
    due_date: Optional[datetime]
    approval_notes: Optional[str]
    rejection_reason: Optional[str]
    email_sent: bool
    resolved_at: Optional[datetime]
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
    requester_id: Optional[str] = Query(None, description="Requester user ID"),
    db: AsyncSession = Depends(get_db)
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
        
        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        
        try:
            await send_approval_request_email(db, approval)
            approval.email_sent = True
            approval.email_sent_at = datetime.utcnow()
            await db.commit()
            await db.refresh(approval)
        except Exception as e:
            logger.error(f"Failed to send approval request email: {e}")
        
        logger.info(f"Created approval request {approval.id} for {request.target_name}")
        return to_response(approval)
        
    except Exception as e:
        logger.error(f"Error creating approval request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ApprovalRequestResponse])
async def list_approval_requests(
    company_id: str = Query(..., description="Company ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    request_type: Optional[str] = Query(None, description="Filter by request type"),
    approver_email: Optional[str] = Query(None, description="Filter by approver email"),
    requester_email: Optional[str] = Query(None, description="Filter by requester email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List approval requests for a company with optional filters."""
    try:
        try:
            parsed_company_id = UUID(company_id)
        except (ValueError, TypeError):
            from app.models.company import CompanyProfile
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_default == True).limit(1)
            )
            default_company = result.scalar_one_or_none()
            if default_company:
                parsed_company_id = default_company.id
            else:
                return []
        
        query = select(ApprovalRequest).where(
            ApprovalRequest.company_id == parsed_company_id
        )
        
        if status:
            query = query.where(ApprovalRequest.status == status)
        if request_type:
            query = query.where(ApprovalRequest.request_type == request_type)
        if approver_email:
            query = query.where(ApprovalRequest.approver_email == approver_email)
        if requester_email:
            query = query.where(ApprovalRequest.requester_email == requester_email)
        
        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        approvals = result.scalars().all()
        
        return [to_response(a) for a in approvals]
        
    except Exception as e:
        logger.error(f"Error listing approval requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=List[ApprovalRequestResponse])
async def list_pending_approvals(
    company_id: str = Query(..., description="Company ID"),
    approver_email: Optional[str] = Query(None, description="Filter by approver email"),
    db: AsyncSession = Depends(get_db)
):
    """List pending approval requests for a company."""
    try:
        query = select(ApprovalRequest).where(
            and_(
                ApprovalRequest.company_id == UUID(company_id),
                ApprovalRequest.status == "pending"
            )
        )
        
        if approver_email:
            query = query.where(ApprovalRequest.approver_email == approver_email)
        
        query = query.order_by(ApprovalRequest.created_at.desc())
        
        result = await db.execute(query)
        approvals = result.scalars().all()
        
        return [to_response(a) for a in approvals]
        
    except Exception as e:
        logger.error(f"Error listing pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval_request(
    approval_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific approval request by ID."""
    try:
        result = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == UUID(approval_id))
        )
        approval = result.scalar_one_or_none()
        
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
    approval_id: str,
    update: ApprovalRequestUpdate,
    company_id: str = Query(..., description="Company ID"),
    approved_by: str = Query(..., description="Email of the approver"),
    db: AsyncSession = Depends(get_db)
):
    """Approve an approval request."""
    try:
        result = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == UUID(approval_id))
        )
        approval = result.scalar_one_or_none()
        
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
                detail=f"Cannot approve request with status '{approval.status}'"
            )
        
        approval.status = "approved"
        approval.approval_notes = update.approval_notes
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = approved_by
        approval.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(approval)
        
        try:
            await send_approval_result_email(db, approval, approved=True)
            approval.notification_sent = True
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to send approval result email for {approval_id}: {str(e)}", exc_info=True)
            approval.notification_sent = False
            await db.commit()
        
        logger.info(f"Approval request {approval_id} approved by {approved_by}")
        return to_response(approval)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{approval_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    approval_id: str,
    update: ApprovalRequestUpdate,
    company_id: str = Query(..., description="Company ID"),
    rejected_by: str = Query(..., description="Email of the rejector"),
    db: AsyncSession = Depends(get_db)
):
    """Reject an approval request."""
    try:
        result = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == UUID(approval_id))
        )
        approval = result.scalar_one_or_none()
        
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
                detail=f"Cannot reject request with status '{approval.status}'"
            )
        
        approval.status = "rejected"
        approval.rejection_reason = update.rejection_reason
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = rejected_by
        approval.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(approval)
        
        try:
            await send_approval_result_email(db, approval, approved=False)
            approval.notification_sent = True
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to send rejection email for {approval_id}: {str(e)}", exc_info=True)
            approval.notification_sent = False
            await db.commit()
        
        logger.info(f"Approval request {approval_id} rejected by {rejected_by}")
        return to_response(approval)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{approval_id}/cancel", response_model=ApprovalRequestResponse)
async def cancel_request(
    approval_id: str,
    company_id: str = Query(..., description="Company ID"),
    cancelled_by: str = Query(..., description="Email of the canceller"),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an approval request (by the requester)."""
    try:
        result = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == UUID(approval_id))
        )
        approval = result.scalar_one_or_none()
        
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
                detail=f"Cannot cancel request with status '{approval.status}'"
            )
        
        approval.status = "cancelled"
        approval.resolved_at = datetime.utcnow()
        approval.resolved_by = cancelled_by
        approval.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(approval)
        
        logger.info(f"Approval request {approval_id} cancelled by {cancelled_by}")
        return to_response(approval)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_approval_request_email(db: AsyncSession, approval: ApprovalRequest):
    """Send email notification to approver about new approval request."""
    request_type_labels = {
        "vacancy_approval": "Aprovação de Vaga",
        "candidate_hire": "Aprovação de Contratação",
        "offer_approval": "Aprovação de Proposta",
        "budget_approval": "Aprovação de Orçamento",
        "custom": "Aprovação Personalizada"
    }
    
    type_label = request_type_labels.get(approval.request_type, "Aprovação")
    
    subject = f"[LIA] {type_label}: {approval.target_name}"
    
    body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #60BED1;">Solicitação de Aprovação</h2>
    
    <p>Olá <strong>{approval.approver_name}</strong>,</p>
    
    <p>Você recebeu uma solicitação de aprovação de <strong>{approval.requester_name}</strong>.</p>
    
    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1f2937;">Detalhes da Solicitação:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>📋 <strong>Tipo:</strong> {type_label}</li>
            <li>📌 <strong>Item:</strong> {approval.target_name}</li>
            <li>👤 <strong>Solicitante:</strong> {approval.requester_name} ({approval.requester_email})</li>
            <li>📅 <strong>Data:</strong> {approval.created_at.strftime('%d/%m/%Y %H:%M')}</li>
        </ul>
        
        {f'<p><strong>Descrição:</strong> {approval.target_description}</p>' if approval.target_description else ''}
    </div>
    
    <p>Por favor, acesse a plataforma LIA para aprovar ou rejeitar esta solicitação.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Sistema LIA
    </p>
</body>
</html>
"""
    
    try:
        success = await email_service._send_email_provider(
            to_email=approval.approver_email,
            subject=subject,
            body_html=body_html
        )
        return success
    except Exception as e:
        logger.error(f"Failed to send approval request email: {e}")
        raise


async def send_approval_result_email(db: AsyncSession, approval: ApprovalRequest, approved: bool):
    """Send email notification to requester about approval result."""
    status_label = "Aprovada" if approved else "Rejeitada"
    status_color = "#16a34a" if approved else "#dc2626"
    
    subject = f"[LIA] Solicitação {status_label}: {approval.target_name}"
    
    notes_section = ""
    if approved and approval.approval_notes:
        notes_section = f'<p><strong>Observações:</strong> {approval.approval_notes}</p>'
    elif not approved and approval.rejection_reason:
        notes_section = f'<p><strong>Motivo da Rejeição:</strong> {approval.rejection_reason}</p>'
    
    body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: {status_color};">Solicitação {status_label}</h2>
    
    <p>Olá <strong>{approval.requester_name}</strong>,</p>
    
    <p>Sua solicitação de aprovação foi <strong style="color: {status_color};">{status_label.lower()}</strong> por <strong>{approval.approver_name}</strong>.</p>
    
    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1f2937;">Detalhes:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>📌 <strong>Item:</strong> {approval.target_name}</li>
            <li>👤 <strong>Aprovador:</strong> {approval.approver_name}</li>
            <li>📅 <strong>Data da Decisão:</strong> {approval.resolved_at.strftime('%d/%m/%Y %H:%M') if approval.resolved_at else 'N/A'}</li>
        </ul>
        {notes_section}
    </div>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Sistema LIA
    </p>
</body>
</html>
"""
    
    try:
        success = await email_service._send_email_provider(
            to_email=approval.requester_email,
            subject=subject,
            body_html=body_html
        )
        return success
    except Exception as e:
        logger.error(f"Failed to send approval result email: {e}")
        raise
