"""
Data Subject Requests API (Portal do Titular LGPD).

Provides endpoints for data subjects to exercise their rights under LGPD Art. 18:
- Access to personal data
- Correction of inaccurate data
- Deletion/anonymization of data
- Data portability
- Objection to processing
- Restriction of processing
- Explanation of automated decisions

Multi-tenant: Uses X-Company-ID header for authenticated endpoints.
SLA: 15 business days legal deadline per LGPD.
"""
import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.observability import DataSubjectRequest
from app.schemas.data_subject_requests import (
    DataSubjectRequestAssign,
    DataSubjectRequestComplete,
    DataSubjectRequestCreate,
    DataSubjectRequestListResponse,
    DataSubjectRequestPublicCreate,
    DataSubjectRequestPublicTrack,
    DataSubjectRequestReject,
    DataSubjectRequestResponse,
    DataSubjectRequestStats,
    DataSubjectRequestVerifyIdentity,
)
from app.shared.tenant_guard import get_verified_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-subject-requests", tags=["data-subject-requests"])

# ─────────────────────────────────────────────────────────────────
# Notificações ao titular — helpers não-bloqueantes (LGPD Art. 18 §4º)
# Falha de notificação NUNCA impede a operação DSR (fail-safe)
# ─────────────────────────────────────────────────────────────────

_REQUEST_TYPE_LABELS = {
    "access": "Acesso aos dados",
    "correction": "Correção de dados",
    "deletion": "Exclusão de dados",
    "portability": "Portabilidade de dados",
    "objection": "Objeção ao tratamento",
    "restriction": "Restrição de tratamento",
    "explanation": "Explicação sobre decisão automatizada",
    "revisao_decisao_automatizada": "Revisão de decisão automatizada (LGPD Art. 20)",
}


async def _notify_subject(
    subject_email: str,
    subject_name: str | None,
    subject: str,
    body: str,
    company_id: str,
) -> bool:
    """
    Envia e-mail de notificação ao titular da DSR.

    Usa notification_service com canal e-mail. Fail-safe: retorna False em erro,
    nunca propaga exceção para o caller.

    Returns:
        True se enviado com sucesso, False se falhou (logado como warning).
    """
    try:
        from app.services.notification_service import NotificationService
        svc = NotificationService()
        await svc.send_notification(
            user_id=subject_email,          # endereço externo como identificador
            title=subject,
            message=body,
            notification_type="dsr_notification",
            priority="normal",
            source_agent="dsr_workflow",
            channels=["email"],
            metadata={
                "recipient_email": subject_email,
                "recipient_name": subject_name or "",
                "company_id": company_id,
            },
        )
        logger.info("DSR notification sent (company=%s)", company_id)
        return True
    except Exception as exc:
        logger.warning(
            "DSR notification failed (company=%s): %s",
            company_id, exc
        )
        return False


def calculate_sla_deadline(start_date: datetime, business_days: int = 15) -> datetime:
    """Calculate SLA deadline based on 15 business days (LGPD requirement)."""
    current = start_date
    days_added = 0
    while days_added < business_days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days_added += 1
    return current


def add_audit_trail_entry(request: DataSubjectRequest, action: str, user_id: str | None = None, details: dict | None = None):
    """Add an entry to the request's audit trail."""
    entry = {
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "details": details or {}
    }
    if request.audit_trail is None:
        request.audit_trail = []
    request.audit_trail = request.audit_trail + [entry]


@router.post("/", response_model=DataSubjectRequestPublicCreate, status_code=status.HTTP_201_CREATED, summary="Create data subject request (public)")
async def create_data_subject_request(
    data: DataSubjectRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new data subject request (public endpoint - no authentication required).
    
    LGPD Art. 18 rights: access, correction, deletion, portability, objection, restriction, explanation.
    SLA: 15 business days.
    """
    try:
        company_uuid = UUID(data.company_id)
        
        now = datetime.utcnow()
        sla_deadline = calculate_sla_deadline(now)
        
        request = DataSubjectRequest(
            company_id=company_uuid,
            request_type=data.request_type.value,
            status="pending",
            subject_name=data.subject_name,
            subject_email=data.subject_email,
            subject_phone=data.subject_phone,
            subject_identifier=data.subject_identifier,
            description=data.description,
            source_channel=data.source_channel.value,
            data_categories=data.data_categories or [],
            sla_deadline=sla_deadline,
            audit_trail=[]
        )
        
        add_audit_trail_entry(request, "created", details={
            "source_channel": data.source_channel.value,
            "request_type": data.request_type.value
        })
        
        db.add(request)
        await db.commit()
        await db.refresh(request)
        
        logger.info(f"LGPD: Data subject request created - ID: {request.id}, Type: {data.request_type.value}, Company: {data.company_id}")

        # Notificação de confirmação ao titular (LGPD Art. 18 §4º)
        if data.subject_email:
            tipo_label = _REQUEST_TYPE_LABELS.get(data.request_type.value, data.request_type.value)
            sla_fmt = request.sla_deadline.strftime("%d/%m/%Y") if request.sla_deadline else "15 dias úteis"
            await _notify_subject(
                subject_email=data.subject_email,
                subject_name=data.subject_name,
                subject=f"[WeDOTalent] Solicitação LGPD recebida — {tipo_label}",
                body=(
                    f"Olá{f', {data.subject_name}' if data.subject_name else ''},\n\n"
                    f"Recebemos sua solicitação de {tipo_label} (LGPD Art. 18).\n\n"
                    f"Número de protocolo: {request.id}\n"
                    f"Prazo de resposta: até {sla_fmt} (15 dias úteis conforme LGPD).\n\n"
                    f"Você pode acompanhar o status em: https://app.wedotalent.com/candidato/dsr/track/{request.id}\n\n"
                    f"Em caso de dúvidas: privacidade@wedotalent.com.br\n\n"
                    f"WeDOTalent — Proteção de Dados"
                ),
                company_id=data.company_id,
            )

        return DataSubjectRequestPublicCreate(
            id=str(request.id),
            status=request.status,
            request_type=request.request_type,
            sla_deadline=request.sla_deadline,
            created_at=request.created_at
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/track/{request_id}", response_model=DataSubjectRequestPublicTrack, summary="Track request status (public)")
async def track_request_status(
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Track the status of a data subject request (public endpoint).
    
    Returns limited information for security reasons.
    """
    try:
        request_uuid = UUID(request_id)
        
        query = select(DataSubjectRequest).where(DataSubjectRequest.id == request_uuid)
        result = await db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return DataSubjectRequestPublicTrack(
            id=str(request.id),
            status=request.status,
            request_type=request.request_type,
            created_at=request.created_at,
            sla_deadline=request.sla_deadline,
            days_remaining=request._days_remaining(),
            is_overdue=request._is_overdue(),
            response=request.response if request.status == "completed" else None,
            completed_at=request.completed_at
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DataSubjectRequestStats, summary="Get request statistics")
async def get_request_stats(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated statistics for data subject requests."""
    try:
        company_uuid = UUID(company_id)
        
        total_query = select(func.count(DataSubjectRequest.id)).where(
            DataSubjectRequest.company_id == company_uuid
        )
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        status_counts = {}
        for status_val in ["pending", "in_review", "processing", "completed", "rejected", "cancelled"]:
            count_query = select(func.count(DataSubjectRequest.id)).where(
                and_(
                    DataSubjectRequest.company_id == company_uuid,
                    DataSubjectRequest.status == status_val
                )
            )
            count_result = await db.execute(count_query)
            status_counts[status_val] = count_result.scalar() or 0
        
        overdue_query = select(func.count(DataSubjectRequest.id)).where(
            and_(
                DataSubjectRequest.company_id == company_uuid,
                DataSubjectRequest.status.in_(["pending", "in_review", "processing"]),
                DataSubjectRequest.sla_deadline < datetime.utcnow()
            )
        )
        overdue_result = await db.execute(overdue_query)
        overdue = overdue_result.scalar() or 0
        
        sla_met_query = select(func.count(DataSubjectRequest.id)).where(
            and_(
                DataSubjectRequest.company_id == company_uuid,
                DataSubjectRequest.sla_met
            )
        )
        sla_met_result = await db.execute(sla_met_query)
        sla_met = sla_met_result.scalar() or 0
        
        completed_count = status_counts.get("completed", 0) + status_counts.get("rejected", 0)
        sla_compliance_rate = (sla_met / completed_count * 100) if completed_count > 0 else 0.0
        
        type_counts = {}
        for type_val in ["access", "correction", "deletion", "portability", "objection", "restriction", "explanation"]:
            type_query = select(func.count(DataSubjectRequest.id)).where(
                and_(
                    DataSubjectRequest.company_id == company_uuid,
                    DataSubjectRequest.request_type == type_val
                )
            )
            type_result = await db.execute(type_query)
            type_counts[type_val] = type_result.scalar() or 0
        
        channel_counts = {}
        for channel_val in ["portal", "email", "whatsapp", "phone", "in_person", "api"]:
            channel_query = select(func.count(DataSubjectRequest.id)).where(
                and_(
                    DataSubjectRequest.company_id == company_uuid,
                    DataSubjectRequest.source_channel == channel_val
                )
            )
            channel_result = await db.execute(channel_query)
            channel_counts[channel_val] = channel_result.scalar() or 0
        
        return DataSubjectRequestStats(
            total_requests=total,
            pending_requests=status_counts.get("pending", 0),
            in_review_requests=status_counts.get("in_review", 0),
            processing_requests=status_counts.get("processing", 0),
            completed_requests=status_counts.get("completed", 0),
            rejected_requests=status_counts.get("rejected", 0),
            cancelled_requests=status_counts.get("cancelled", 0),
            overdue_requests=overdue,
            sla_compliance_rate=round(sla_compliance_rate, 2),
            requests_by_type=type_counts,
            requests_by_channel=channel_counts
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting data subject request stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DataSubjectRequestListResponse, summary="List data subject requests")
async def list_data_subject_requests(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    request_type: str | None = Query(None, description="Filter by request type"),
    date_from: datetime | None = Query(None, description="Filter by start date"),
    date_to: datetime | None = Query(None, description="Filter by end date"),
    subject_email: str | None = Query(None, description="Filter by subject email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List data subject requests with filters and pagination."""
    try:
        company_uuid = UUID(company_id)
        conditions = [DataSubjectRequest.company_id == company_uuid]
        
        if status_filter:
            conditions.append(DataSubjectRequest.status == status_filter)
        if request_type:
            conditions.append(DataSubjectRequest.request_type == request_type)
        if date_from:
            conditions.append(DataSubjectRequest.created_at >= date_from)
        if date_to:
            conditions.append(DataSubjectRequest.created_at <= date_to)
        if subject_email:
            conditions.append(DataSubjectRequest.subject_email.ilike(f"%{subject_email}%"))
        
        query = select(DataSubjectRequest).where(and_(*conditions))
        query = query.order_by(desc(DataSubjectRequest.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        requests = result.scalars().all()
        
        count_query = select(func.count(DataSubjectRequest.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return DataSubjectRequestListResponse(
            requests=[DataSubjectRequestResponse(**r.to_dict()) for r in requests],
            total=total,
            skip=skip,
            limit=limit
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing data subject requests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{request_id}", response_model=DataSubjectRequestResponse, summary="Get request details")
async def get_data_subject_request(
    request_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific data subject request."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)
        
        query = select(DataSubjectRequest).where(
            and_(
                DataSubjectRequest.id == request_uuid,
                DataSubjectRequest.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/assign", response_model=DataSubjectRequestResponse, summary="Assign request to user")
async def assign_request(
    request_id: str,
    data: DataSubjectRequestAssign,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Assign a data subject request to a user for handling."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)
        assigned_to_uuid = UUID(data.assigned_to)
        
        query = select(DataSubjectRequest).where(
            and_(
                DataSubjectRequest.id == request_uuid,
                DataSubjectRequest.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot assign request with status '{request.status}'")
        
        request.assigned_to = assigned_to_uuid
        if request.status == "pending":
            request.status = "in_review"
        
        add_audit_trail_entry(request, "assigned", user_id=company_id, details={
            "assigned_to": data.assigned_to,
            "previous_status": request.status
        })
        
        await db.commit()
        await db.refresh(request)
        
        logger.info(f"LGPD: Request {request_id} assigned to {data.assigned_to}")
        
        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error assigning data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/verify-identity", response_model=DataSubjectRequestResponse, summary="Verify subject identity")
async def verify_identity(
    request_id: str,
    data: DataSubjectRequestVerifyIdentity,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Verify the identity of the data subject making the request."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)
        
        query = select(DataSubjectRequest).where(
            and_(
                DataSubjectRequest.id == request_uuid,
                DataSubjectRequest.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot verify identity for request with status '{request.status}'")
        
        request.identity_verified = data.verified
        request.identity_verification_method = data.identity_verification_method
        request.identity_verified_at = datetime.utcnow() if data.verified else None
        
        add_audit_trail_entry(request, "identity_verified" if data.verified else "identity_verification_failed", 
                             user_id=company_id, details={
            "method": data.identity_verification_method,
            "verified": data.verified
        })
        
        await db.commit()
        await db.refresh(request)
        
        logger.info(f"LGPD: Request {request_id} identity verification: {data.verified} via {data.identity_verification_method}")
        
        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error verifying identity for data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/process", response_model=DataSubjectRequestResponse, summary="Start processing request")
async def start_processing(
    request_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Start processing a data subject request."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)
        
        query = select(DataSubjectRequest).where(
            and_(
                DataSubjectRequest.id == request_uuid,
                DataSubjectRequest.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot process request with status '{request.status}'")
        
        if request.status == "processing":
            raise HTTPException(status_code=400, detail="Request is already being processed")
        
        previous_status = request.status
        request.status = "processing"
        
        add_audit_trail_entry(request, "processing_started", user_id=company_id, details={
            "previous_status": previous_status
        })
        
        await db.commit()
        await db.refresh(request)
        
        logger.info(f"LGPD: Request {request_id} processing started")
        
        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error starting processing for data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/complete", response_model=DataSubjectRequestResponse, summary="Complete request")
async def complete_request(
    request_id: str,
    data: DataSubjectRequestComplete,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Complete a data subject request with a response."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)
        
        query = select(DataSubjectRequest).where(
            and_(
                DataSubjectRequest.id == request_uuid,
                DataSubjectRequest.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot complete request with status '{request.status}'")
        
        now = datetime.utcnow()
        previous_status = request.status
        
        request.status = "completed"
        request.response = data.response
        request.completed_at = now
        request.evidence_files = data.evidence_files or []
        
        request.sla_met = now <= request.sla_deadline if request.sla_deadline else True
        
        add_audit_trail_entry(request, "completed", user_id=company_id, details={
            "previous_status": previous_status,
            "sla_met": request.sla_met,
            "response_length": len(data.response)
        })
        
        await db.commit()
        await db.refresh(request)

        logger.info(f"LGPD: Request {request_id} completed. SLA met: {request.sla_met}.")

        # Notificação de conclusão ao titular
        if request.subject_email:
            tipo_label = _REQUEST_TYPE_LABELS.get(request.request_type, request.request_type)
            sla_status = "dentro do prazo" if request.sla_met else "fora do prazo"
            await _notify_subject(
                subject_email=request.subject_email,
                subject_name=request.subject_name,
                subject=f"[WeDOTalent] Sua solicitação LGPD foi concluída — {tipo_label}",
                body=(
                    f"Olá{f', {request.subject_name}' if request.subject_name else ''},\n\n"
                    f"Sua solicitação de {tipo_label} (protocolo {request_id}) foi concluída {sla_status}.\n\n"
                    f"Resposta:\n{data.response}\n\n"
                    f"Caso queira contestar esta resposta, acesse:\n"
                    f"https://app.wedotalent.com/candidato/dsr/track/{request_id}\n\n"
                    f"WeDOTalent — Proteção de Dados | privacidade@wedotalent.com.br"
                ),
                company_id=company_id,
            )

        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error completing data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/reject", response_model=DataSubjectRequestResponse, summary="Reject request")
async def reject_request(
    request_id: str,
    data: DataSubjectRequestReject,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Reject a data subject request with a reason."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)
        
        query = select(DataSubjectRequest).where(
            and_(
                DataSubjectRequest.id == request_uuid,
                DataSubjectRequest.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot reject request with status '{request.status}'")
        
        now = datetime.utcnow()
        previous_status = request.status
        
        request.status = "rejected"
        request.rejection_reason = data.rejection_reason
        request.completed_at = now
        
        request.sla_met = now <= request.sla_deadline if request.sla_deadline else True
        
        add_audit_trail_entry(request, "rejected", user_id=company_id, details={
            "previous_status": previous_status,
            "sla_met": request.sla_met,
            "rejection_reason_length": len(data.rejection_reason)
        })
        
        await db.commit()
        await db.refresh(request)

        logger.info(f"LGPD: Request {request_id} rejected. SLA met: {request.sla_met}.")

        # Notificação de indeferimento ao titular
        if request.subject_email:
            tipo_label = _REQUEST_TYPE_LABELS.get(request.request_type, request.request_type)
            await _notify_subject(
                subject_email=request.subject_email,
                subject_name=request.subject_name,
                subject=f"[WeDOTalent] Resultado da sua solicitação LGPD — {tipo_label}",
                body=(
                    f"Olá{f', {request.subject_name}' if request.subject_name else ''},\n\n"
                    f"Sua solicitação de {tipo_label} (protocolo {request_id}) foi analisada.\n\n"
                    f"Resultado: Indeferida\n"
                    f"Motivo: {data.rejection_reason}\n\n"
                    f"Você pode contestar esta decisão ou acionar a ANPD (Autoridade Nacional de Proteção de Dados):\n"
                    f"https://www.gov.br/anpd\n\n"
                    f"Para mais informações: privacidade@wedotalent.com.br\n\n"
                    f"WeDOTalent — Proteção de Dados"
                ),
                company_id=company_id,
            )

        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error rejecting data subject request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
