"""
Data Subject Requests API — LGPD Art. 18 compliance.

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

from fastapi import Request, APIRouter, Depends, HTTPException, Query, status

from app.repositories.dependencies import get_data_subject_repo
from app.repositories.data_subject_repository import (
    DsrExecutorFailedError,
)
from app.repositories.data_subject_repository import DataSubjectRepository
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
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

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
            user_id=subject_email,
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


def _make_audit_entry(action: str, user_id: str | None = None, details: dict | None = None) -> dict:
    """Build a single audit trail entry dict."""
    return {
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "details": details or {},
    }




# ─────────────────────────────────────────────────────────────────────────────
# W3-017 (2026-05-23): DSR public POST rate-limit · IP-based sliding window.
# LGPD Art 18 endpoint público sem auth → vulnerável a spam/DoS sem este guard.
# Threshold: 5 requests/min per IP. Excede → HTTP 429.
# ─────────────────────────────────────────────────────────────────────────────

_DSR_RATE_LIMIT_PER_IP_PER_MIN = 5


async def _dsr_rate_limit_check(request: Request) -> None:
    """Rate limit by client IP for DSR public POST endpoint.

    Raises HTTPException(429) when over threshold.
    Uses canonical RateLimiter (Redis ZSET + in-memory fallback).
    """
    try:
        from app.middleware.rate_limiter import rate_limiter
    except ImportError:
        # Fail-open if rate_limiter unavailable (dev/test env)
        return

    client_ip = (
        request.client.host if request.client else "anonymous"
    )
    # Use canonical sliding window via rate_limiter._redis_sliding_window
    # Composite key: dsr:public:<ip>
    key = f"dsr:public:{client_ip}"
    try:
        allowed, current_count = await rate_limiter._redis_sliding_window(
            key, _DSR_RATE_LIMIT_PER_IP_PER_MIN, window_sec=60
        )
        if not allowed:
            logger.warning(
                "[DSR] Rate limit exceeded · ip=%s count=%d",
                client_ip, current_count,
            )
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many DSR requests from this IP "
                    f"(>{_DSR_RATE_LIMIT_PER_IP_PER_MIN}/min). "
                    "Aguarde 1 minuto antes de retentar."
                ),
                headers={"Retry-After": "60"},
            )
    except HTTPException:
        raise
    except Exception as exc:
        # Fail-open · rate_limiter erro NÃO bloqueia DSR (LGPD Art 18 rights protection)
        logger.warning("[DSR] Rate limit check skipped (fail-open): %s", exc)


@router.post("/", response_model=DataSubjectRequestPublicCreate, status_code=status.HTTP_201_CREATED, summary="Create data subject request (public)")
async def create_data_subject_request(
    request: Request,  # W3-017 (2026-05-23): for IP-based rate limit
    data: DataSubjectRequestCreate,
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
company_id: str = Depends(require_company_id)):
    # W3-017 (2026-05-23): public endpoint, no auth → IP rate limit
    await _dsr_rate_limit_check(request)
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a new data subject request (LGPD Art. 18).

    Onda 4.2d-P0-18 (2026-05-23): contradicao docstring vs deps RESOLVIDA.
    Endpoint require JWT (`require_company_id`). company_id usado vem do
    JWT, NAO do payload `data.company_id` (era cross-tenant create — user
    A criava DSR em company B mudando payload). Payload field IGNORADO
    (mantido no schema pra zero breaking change clientes).

    Rights: access, correction, deletion, portability, objection,
    restriction, explanation. SLA: 15 business days.
    """
    try:
        # Onda 4.2d-P0-18: company_id vem do JWT, payload e IGNORADO.
        company_uuid = UUID(company_id)

        now = datetime.utcnow()
        sla_deadline = calculate_sla_deadline(now)

        audit_entry = _make_audit_entry(
            "created",
            details={
                "source_channel": data.source_channel.value,
                "request_type": data.request_type.value,
            },
        )

        request = await repo.create_request({
            "company_id": company_uuid,
            "request_type": data.request_type.value,
            "status": "pending",
            "subject_name": data.subject_name,
            "subject_email": data.subject_email,
            "subject_phone": data.subject_phone,
            "subject_identifier": data.subject_identifier,
            "description": data.description,
            "source_channel": data.source_channel.value,
            "data_categories": data.data_categories or [],
            "sla_deadline": sla_deadline,
            "audit_trail": [audit_entry],
        })

        logger.info(
            "LGPD: Data subject request created - ID: %s, Type: %s, Company: %s",
            request.id, data.request_type.value, data.company_id,
        )

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
                    f"Você pode acompanhar o status em: https://app.wedotalent.cc/candidato/dsr/track/{request.id}\n\n"
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
            created_at=request.created_at,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error("Error creating data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/track/{request_id}", response_model=DataSubjectRequestPublicTrack, summary="Track request status (public)")
async def track_request_status(
    request_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Track the status of a data subject request (public endpoint).

    Returns limited information for security reasons.
    """
    try:
        request_uuid = UUID(request_id)
        company_uuid = UUID(company_id)

        # WT-2022 P1.5: /track endpoint MUST be tenant-scoped (was vazando cross-tenant via UUID guess)
        request = await repo.get_by_id_and_company(request_uuid, company_uuid)

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
            completed_at=request.completed_at,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error tracking data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DataSubjectRequestStats, summary="Get request statistics")
async def get_request_stats(
    company_id: str = Depends(get_verified_company_id),
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get aggregated statistics for data subject requests."""
    try:
        company_uuid = UUID(company_id)

        stats = await repo.get_stats(company_uuid)

        status_counts = stats["status_counts"]
        completed_count = status_counts.get("completed", 0) + status_counts.get("rejected", 0)
        sla_compliance_rate = (stats["sla_met"] / completed_count * 100) if completed_count > 0 else 0.0

        return DataSubjectRequestStats(
            total_requests=stats["total"],
            pending_requests=status_counts.get("pending", 0),
            in_review_requests=status_counts.get("in_review", 0),
            processing_requests=status_counts.get("processing", 0),
            completed_requests=status_counts.get("completed", 0),
            rejected_requests=status_counts.get("rejected", 0),
            cancelled_requests=status_counts.get("cancelled", 0),
            overdue_requests=stats["overdue"],
            sla_compliance_rate=round(sla_compliance_rate, 2),
            requests_by_type=stats["type_counts"],
            requests_by_channel=stats["channel_counts"],
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting data subject request stats: %s", e, exc_info=True)
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
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List data subject requests with filters and pagination."""
    try:
        company_uuid = UUID(company_id)

        requests, total = await repo.list_requests(
            company_id=company_uuid,
            status_filter=status_filter,
            request_type=request_type,
            date_from=date_from,
            date_to=date_to,
            subject_email=subject_email,
            skip=skip,
            limit=limit,
        )

        return DataSubjectRequestListResponse(
            requests=[DataSubjectRequestResponse(**r.to_dict()) for r in requests],
            total=total,
            skip=skip,
            limit=limit,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing data subject requests: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{request_id}", response_model=DataSubjectRequestResponse, summary="Get request details")
async def get_data_subject_request(
    request_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get detailed information about a specific data subject request."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)

        request = await repo.get_by_id_and_company(request_uuid, company_uuid)

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/assign", response_model=DataSubjectRequestResponse, summary="Assign request to user")
async def assign_request(
    request_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: DataSubjectRequestAssign,
    company_id: str = Depends(get_verified_company_id),
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Assign a data subject request to a user for handling."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)
        assigned_to_uuid = UUID(data.assigned_to)

        request = await repo.get_by_id_and_company(request_uuid, company_uuid)

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Cannot assign request with status '{request.status}'")

        audit_entry = _make_audit_entry(
            "assigned",
            user_id=company_id,
            details={
                "assigned_to": data.assigned_to,
                "previous_status": request.status,
            },
        )

        request = await repo.assign_request(request, assigned_to_uuid, audit_entry)

        logger.info("LGPD: Request %s assigned to %s", request_id, data.assigned_to)

        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error("Error assigning data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/verify-identity", response_model=DataSubjectRequestResponse, summary="Verify subject identity")
async def verify_identity(
    request_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: DataSubjectRequestVerifyIdentity,
    company_id: str = Depends(get_verified_company_id),
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Verify the identity of the data subject making the request."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)

        request = await repo.get_by_id_and_company(request_uuid, company_uuid)

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot verify identity for request with status '{request.status}'",
            )

        action = "identity_verified" if data.verified else "identity_verification_failed"
        audit_entry = _make_audit_entry(
            action,
            user_id=company_id,
            details={
                "method": data.identity_verification_method,
                "verified": data.verified,
            },
        )

        request = await repo.verify_identity(
            request,
            verified=data.verified,
            method=data.identity_verification_method,
            audit_entry=audit_entry,
        )

        logger.info(
            "LGPD: Request %s identity verification: %s via %s",
            request_id, data.verified, data.identity_verification_method,
        )

        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error("Error verifying identity for data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/process", response_model=DataSubjectRequestResponse, summary="Start processing request")
async def start_processing(
    request_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Start processing a data subject request."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)

        request = await repo.get_by_id_and_company(request_uuid, company_uuid)

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot process request with status '{request.status}'",
            )

        if request.status == "processing":
            raise HTTPException(status_code=400, detail="Request is already being processed")

        previous_status = request.status
        audit_entry = _make_audit_entry(
            "processing_started",
            user_id=company_id,
            details={"previous_status": previous_status},
        )

        request = await repo.start_processing(request, audit_entry)

        logger.info("LGPD: Request %s processing started", request_id)

        return DataSubjectRequestResponse(**request.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error("Error starting processing for data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/complete", response_model=DataSubjectRequestResponse, summary="Complete request")
async def complete_request(
    request_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: DataSubjectRequestComplete,
    company_id: str = Depends(get_verified_company_id),
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Complete a data subject request with a response."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)

        request = await repo.get_by_id_and_company(request_uuid, company_uuid)

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete request with status '{request.status}'",
            )

        previous_status = request.status

        # Build audit entry before mutation (sla_met computed inside repo)
        audit_entry = _make_audit_entry(
            "completed",
            user_id=company_id,
            details={
                "previous_status": previous_status,
                "response_length": len(data.response),
            },
        )

        try:
            request = await repo.complete_request(
                request,
                response=data.response,
                evidence_files=data.evidence_files or [],
                audit_entry=audit_entry,
            )
        except DsrExecutorFailedError as exc:
            # WT-2022 P2.1: side-effect failed (e.g., deletion no candidate) - fail-loud
            logger.warning(
                "DSR completion blocked by executor for %s: %s",
                request_id, exc,
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    f"DSR side-effect execution failed: {exc}. "
                    f"Status NOT updated to 'completed' - LGPD compliance gap prevented. "
                    f"Manual investigation required (see audit_trail)."
                ),
            )

        logger.info("LGPD: Request %s completed. SLA met: %s.", request_id, request.sla_met)

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
                    f"https://app.wedotalent.cc/candidato/dsr/track/{request_id}\n\n"
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
        await repo.rollback()
        logger.error("Error completing data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{request_id}/reject", response_model=DataSubjectRequestResponse, summary="Reject request")
async def reject_request(
    request_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: DataSubjectRequestReject,
    company_id: str = Depends(get_verified_company_id),
    repo: DataSubjectRepository = Depends(get_data_subject_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Reject a data subject request with a reason."""
    try:
        company_uuid = UUID(company_id)
        request_uuid = UUID(request_id)

        request = await repo.get_by_id_and_company(request_uuid, company_uuid)

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        if request.status in ["completed", "rejected", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reject request with status '{request.status}'",
            )

        previous_status = request.status

        audit_entry = _make_audit_entry(
            "rejected",
            user_id=company_id,
            details={
                "previous_status": previous_status,
                "rejection_reason_length": len(data.rejection_reason),
            },
        )

        request = await repo.reject_request(
            request,
            rejection_reason=data.rejection_reason,
            audit_entry=audit_entry,
        )

        logger.info("LGPD: Request %s rejected. SLA met: %s.", request_id, request.sla_met)

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
        await repo.rollback()
        logger.error("Error rejecting data subject request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
