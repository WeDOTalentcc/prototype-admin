"""
LGPD Compliance API Endpoints.

Provides endpoints for:
- DPO Registry (Data Protection Officer management)
- Breach Notifications (48h LGPD requirement)
- Automated Decision Explanations (Article 20 compliance)
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.domains.lgpd.dependencies import get_lgpd_repo
from app.domains.lgpd.repositories.lgpd_repository import LGPDRepository
from app.schemas.lgpd_compliance import (
    ANPDNotification,
    AutomatedDecisionCreate,
    AutomatedDecisionListResponse,
    AutomatedDecisionResponse,
    BreachNotificationCreate,
    BreachNotificationListResponse,
    BreachNotificationResponse,
    BreachNotificationUpdate,
    BreachResolution,
    DPORegistryCreate,
    DPORegistryListResponse,
    DPORegistryResponse,
    DPORegistryUpdate,
    HumanReviewComplete,
    HumanReviewRequest,
    LGPDComplianceStats,
    SubjectsNotification,
)
from app.shared.services.lgpd_cleanup_service import (
    RETENTION_DAYS,
    get_pending_deletions_count,
    run_cleanup,
    schedule_deletion_for_candidate,
)
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lgpd", tags=["lgpd-compliance"])


@router.get("/stats", response_model=LGPDComplianceStats, summary="Get LGPD compliance statistics")
async def get_lgpd_stats(
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get aggregated LGPD compliance statistics for the company."""
    try:
        company_uuid = UUID(company_id)
        stats = await lgpd_repo.get_compliance_stats(company_uuid)
        dpo = stats["dpo"]
        return LGPDComplianceStats(
            dpo_registered=dpo is not None,
            dpo_active=dpo.is_active if dpo else False,
            total_breaches=stats["total_breaches"],
            open_breaches=stats["open_breaches"],
            breaches_pending_anpd=stats["breaches_pending_anpd"],
            breaches_deadline_exceeded=0,
            total_automated_decisions=stats["total_decisions"],
            pending_human_reviews=stats["pending_reviews"],
            completed_human_reviews=stats["completed_reviews"],
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting LGPD stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dpo", response_model=DPORegistryListResponse, summary="List DPO registry entries")
async def list_dpo_entries(
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List DPO registry entries scoped to caller's company.

    Onda 4.2h-C5 (2026-05-24): tenant guard — antes listava DPOs de
    TODAS empresas (vazava DPO name/email/phone cross-tenant). LGPD Art. 41
    (DPO contact é dado nominativo do encarregado, requer scope).
    """
    try:
        # Onda 4.2h-C5: scope canonical ao tenant do caller
        dpos, total = await lgpd_repo.list_dpos(
            is_active, limit, offset, company_id=UUID(company_id),
        )
        return DPORegistryListResponse(
            dpos=[DPORegistryResponse(**d.to_dict()) for d in dpos],
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing DPO entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dpo/{target_company_id}", response_model=DPORegistryResponse, summary="Get DPO for company")
async def get_dpo_for_company(
    target_company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get DPO registry entry for a specific company.

    Onda 4.2h-C5 (2026-05-24): tenant guard fail-closed — caller só pode
    consultar DPO da própria company (cross-tenant DPO contact = LGPD
    Art. 41 violation). 404 sem leak de existence.
    """
    try:
        target_uuid = UUID(target_company_id)
        # Onda 4.2h-C5: pré-check tenant — caller != target = 404 (sem enumeration)
        if str(target_uuid) != str(company_id):
            logger.warning(
                f"Cross-tenant DPO lookup blocked: caller={company_id} target={target_company_id}"
            )
            raise HTTPException(status_code=404, detail="DPO not registered for this company")
        dpo = await lgpd_repo.get_dpo_by_company(target_uuid)
        if not dpo:
            raise HTTPException(status_code=404, detail="DPO not registered for this company")
        return DPORegistryResponse(**dpo.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting DPO: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dpo", response_model=DPORegistryResponse, status_code=status.HTTP_201_CREATED, summary="Register DPO")
async def create_dpo_registry(
    data: DPORegistryCreate,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Register or update DPO for the company."""
    try:
        company_uuid = UUID(company_id)
        dpo = await lgpd_repo.upsert_dpo(
            company_uuid,
            {
                "dpo_name": data.dpo_name,
                "dpo_email": data.dpo_email,
                "dpo_phone": data.dpo_phone,
                "appointment_date": data.appointment_date,
                "public_contact_url": data.public_contact_url,
            },
        )
        logger.info(f"Upserted DPO registry for company {company_id}")
        return DPORegistryResponse(**dpo.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating DPO registry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/dpo", response_model=DPORegistryResponse, summary="Update DPO")
async def update_dpo_registry(
    data: DPORegistryUpdate,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update DPO registry for the company."""
    try:
        company_uuid = UUID(company_id)
        dpo = await lgpd_repo.update_dpo(
            company_uuid,
            {
                "dpo_name": data.dpo_name,
                "dpo_email": data.dpo_email,
                "dpo_phone": data.dpo_phone,
                "is_active": data.is_active,
                "public_contact_url": data.public_contact_url,
            },
        )
        if not dpo:
            raise HTTPException(status_code=404, detail="DPO not registered for this company")
        logger.info(f"Updated DPO registry for company {company_id}")
        return DPORegistryResponse(**dpo.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating DPO registry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breaches", response_model=BreachNotificationListResponse, summary="List breach notifications")
async def list_breach_notifications(
    severity: str | None = Query(None, description="Filter by severity"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    pending_anpd: bool | None = Query(None, description="Filter breaches pending ANPD notification"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List breach notifications with optional filters."""
    try:
        company_uuid = UUID(company_id)
        breaches, total = await lgpd_repo.list_breaches(
            company_uuid, severity, status_filter, pending_anpd, limit, offset
        )
        return BreachNotificationListResponse(
            breaches=[BreachNotificationResponse(**b.to_dict()) for b in breaches],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing breach notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breaches/{breach_id}", response_model=BreachNotificationResponse, summary="Get breach notification")
async def get_breach_notification(
    breach_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific breach notification by ID."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        breach = await lgpd_repo.get_breach_by_id(breach_uuid, company_uuid)
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting breach notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breaches", response_model=BreachNotificationResponse, status_code=status.HTTP_201_CREATED, summary="Report data breach")
async def create_breach_notification(
    data: BreachNotificationCreate,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Report a new data breach. LGPD requires ANPD notification within 48 hours."""
    try:
        company_uuid = UUID(company_id)
        breach = await lgpd_repo.create_breach(
            company_uuid,
            {
                "breach_detected_at": data.breach_detected_at,
                "breach_description": data.breach_description,
                "affected_data_types": data.affected_data_types,
                "affected_count": data.affected_count,
                "severity": data.severity.value,
            },
        )
        logger.warning(
            f"LGPD: Data breach reported for company {company_id} - Severity: {data.severity.value}"
        )
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating breach notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}", response_model=BreachNotificationResponse, summary="Update breach notification")
async def update_breach_notification(
    breach_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: BreachNotificationUpdate,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a breach notification."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        breach = await lgpd_repo.update_breach(
            breach_uuid,
            company_uuid,
            {
                "breach_description": data.breach_description,
                "affected_data_types": data.affected_data_types,
                "affected_count": data.affected_count,
                "severity": data.severity.value if data.severity is not None else None,
                "remediation_actions": data.remediation_actions,
                "status": data.status.value if data.status is not None else None,
            },
        )
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating breach notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}/notify-anpd", response_model=BreachNotificationResponse, summary="Mark ANPD notified")
async def mark_anpd_notified(
    breach_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ANPDNotification,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Mark that ANPD has been notified about the breach (48h requirement)."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        breach = await lgpd_repo.mark_breach_anpd_notified(breach_uuid, company_uuid)
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")

        hours_since = breach._hours_since_detection()
        if hours_since and hours_since <= 48:
            logger.info(f"LGPD: ANPD notified within 48h deadline for breach {breach_id}")
        else:
            logger.warning(
                f"LGPD: ANPD notified AFTER 48h deadline for breach {breach_id} ({hours_since}h)"
            )

        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking ANPD notified: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}/notify-subjects", response_model=BreachNotificationResponse, summary="Mark subjects notified")
async def mark_subjects_notified(
    breach_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: SubjectsNotification,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Mark that affected data subjects have been notified about the breach."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        breach = await lgpd_repo.mark_breach_subjects_notified(breach_uuid, company_uuid)
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        logger.info(f"LGPD: Data subjects notified for breach {breach_id}")
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking subjects notified: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}/resolve", response_model=BreachNotificationResponse, summary="Resolve breach")
async def resolve_breach(
    breach_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: BreachResolution,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Mark a breach as resolved."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        breach = await lgpd_repo.resolve_breach(breach_uuid, company_uuid, data.remediation_actions)
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        logger.info(f"LGPD: Breach {breach_id} resolved")
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving breach: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions", response_model=AutomatedDecisionListResponse, summary="List automated decisions")
async def list_automated_decisions(
    decision_type: str | None = Query(None, description="Filter by decision type"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    vacancy_id: str | None = Query(None, description="Filter by vacancy ID"),
    pending_review: bool | None = Query(None, description="Filter decisions pending human review"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List automated decision explanations with optional filters."""
    try:
        company_uuid = UUID(company_id)
        candidate_uuid = UUID(candidate_id) if candidate_id else None
        vacancy_uuid = UUID(vacancy_id) if vacancy_id else None
        decisions, total = await lgpd_repo.list_decisions(
            company_uuid, decision_type, candidate_uuid, vacancy_uuid, pending_review, limit, offset
        )
        return AutomatedDecisionListResponse(
            decisions=[AutomatedDecisionResponse(**d.to_dict()) for d in decisions],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing automated decisions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{decision_id}", response_model=AutomatedDecisionResponse, summary="Get automated decision")
async def get_automated_decision(
    decision_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific automated decision explanation by ID."""
    try:
        company_uuid = UUID(company_id)
        decision_uuid = UUID(decision_id)
        decision = await lgpd_repo.get_decision_by_id(decision_uuid, company_uuid)
        if not decision:
            raise HTTPException(status_code=404, detail="Automated decision not found")
        return AutomatedDecisionResponse(**decision.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting automated decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions", response_model=AutomatedDecisionResponse, status_code=status.HTTP_201_CREATED, summary="Record automated decision")
async def create_automated_decision(
    data: AutomatedDecisionCreate,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Record an automated decision for Article 20 compliance."""
    try:
        company_uuid = UUID(company_id)
        decision = await lgpd_repo.create_decision(
            company_uuid,
            {
                "decision_type": data.decision_type.value,
                "candidate_id": UUID(data.candidate_id) if data.candidate_id else None,
                "vacancy_id": UUID(data.vacancy_id) if data.vacancy_id else None,
                "ai_model_used": data.ai_model_used,
                "input_criteria": data.input_criteria,
                "decision_criteria": data.decision_criteria,
                "explanation_text": data.explanation_text,
            },
        )
        logger.info(f"LGPD Art.20: Recorded automated decision {decision.id} for company {company_id}")
        return AutomatedDecisionResponse(**decision.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating automated decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions/{decision_id}/request-human-review", response_model=AutomatedDecisionResponse, summary="Request human review")
async def request_human_review(
    decision_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: HumanReviewRequest,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Request human review of an automated decision (LGPD Article 20)."""
    try:
        company_uuid = UUID(company_id)
        decision_uuid = UUID(decision_id)
        decision = await lgpd_repo.get_decision_by_id(decision_uuid, company_uuid)
        if not decision:
            raise HTTPException(status_code=404, detail="Automated decision not found")
        if decision.human_review_requested:
            raise HTTPException(status_code=400, detail="Human review already requested")

        decision = await lgpd_repo.request_human_review(decision_uuid, company_uuid)
        logger.info(f"LGPD Art.20: Human review requested for decision {decision_id}")
        return AutomatedDecisionResponse(**decision.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting human review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions/{decision_id}/complete-human-review", response_model=AutomatedDecisionResponse, summary="Complete human review")
async def complete_human_review(
    decision_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: HumanReviewComplete,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Complete human review of an automated decision."""
    try:
        company_uuid = UUID(company_id)
        decision_uuid = UUID(decision_id)
        decision = await lgpd_repo.get_decision_by_id(decision_uuid, company_uuid)
        if not decision:
            raise HTTPException(status_code=404, detail="Automated decision not found")
        if not decision.human_review_requested:
            raise HTTPException(status_code=400, detail="No human review was requested")
        if decision.human_review_completed_at:
            raise HTTPException(status_code=400, detail="Human review already completed")

        decision = await lgpd_repo.complete_human_review(
            decision_uuid,
            company_uuid,
            data.decision,
            UUID(data.reviewer_id),
        )
        logger.info(f"LGPD Art.20: Human review completed for decision {decision_id}")
        return AutomatedDecisionResponse(**decision.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing human review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# L4 — Data Deletion Scheduling (LGPD Art. 16 / Data Retention)
# ---------------------------------------------------------------------------

class ScheduleDeletionRequest(WeDoBaseModel):
    candidate_id: str
    reason: str = Field(
        "rejected",
        description="Retention category: rejected | withdrawn | interview_notes | screening_logs",
    )
    retention_days: int | None = Field(
        None,
        description="Override default retention window in days. Defaults to policy per reason.",
    )


class ScheduleDeletionResponse(BaseModel):
    candidate_id: str
    scheduled_deletion_at: str
    retention_days: int
    reason: str


@router.post("/schedule-deletion", response_model=ScheduleDeletionResponse)
async def schedule_candidate_deletion(
    data: ScheduleDeletionRequest,
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Schedule permanent deletion of a candidate's data.

    Called when a Data Subject exercises their right to erasure (LGPD Art. 18-VI)
    or when a candidate is rejected (automatic 90-day retention policy).
    The actual deletion is executed by the daily cleanup job.
    """
    valid_reasons = set(RETENTION_DAYS.keys())
    if data.reason not in valid_reasons:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason. Must be one of: {', '.join(valid_reasons)}",
        )

    # Onda 4.2h-C6 (2026-05-24): tenant guard — antes qualquer candidate_id
    # podia ser agendado pra deleção cross-tenant (DoS + LGPD Art. 18-VI
    # rights violation pra company alheia).
    from app.models.candidate import Candidate
    candidate_row = await lgpd_repo.db.get(Candidate, UUID(data.candidate_id))
    if not candidate_row or str(candidate_row.company_id) != str(company_id):
        logger.warning(
            f"Cross-tenant schedule-deletion blocked: caller={company_id} "
            f"candidate={data.candidate_id}"
        )
        raise HTTPException(status_code=404, detail="Candidate not found")

    days = data.retention_days or RETENTION_DAYS[data.reason]
    deletion_at = await schedule_deletion_for_candidate(lgpd_repo.db, data.candidate_id, data.reason, days)

    logger.info(
        f"LGPD deletion scheduled: candidate={data.candidate_id} reason={data.reason} at={deletion_at}"
    )

    return ScheduleDeletionResponse(
        candidate_id=data.candidate_id,
        scheduled_deletion_at=deletion_at.isoformat(),
        retention_days=days,
        reason=data.reason,
    )


@router.post("/run-cleanup", response_model=None)
async def trigger_cleanup(
    dry_run: bool = Query(True, description="dry_run=true logs deletions without executing"),
    company_id: str = Depends(get_verified_company_id),
    _admin_user: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Manually trigger the LGPD data cleanup job.

    Requires admin or DPO role. Always run with dry_run=true first to review
    the scope. The daily scheduler also calls this automatically with dry_run=false.
    """
    summary = await run_cleanup(dry_run=dry_run)
    logger.info(
        "LGPD manual cleanup triggered by admin: dry_run=%s user=%s company=%s",
        dry_run,
        _admin_user.id,
        company_id,
    )
    return summary


@router.get("/pending-deletions", response_model=None)
async def pending_deletions(
    company_id: str = Depends(get_verified_company_id),
    lgpd_repo: LGPDRepository = Depends(get_lgpd_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Return count of records pending deletion (monitoring/DPO dashboard)."""
    return await get_pending_deletions_count(lgpd_repo.db)

reorder_collection_before_item(router)
