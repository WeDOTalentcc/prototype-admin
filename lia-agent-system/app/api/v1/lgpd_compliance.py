"""
LGPD Compliance API Endpoints.

Provides endpoints for:
- DPO Registry (Data Protection Officer management)
- Breach Notifications (48h LGPD requirement)
- Automated Decision Explanations (Article 20 compliance)
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.core.database import get_db
from app.models.observability import AutomatedDecisionExplanation, BreachNotification, DPORegistry
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
from app.services.lgpd_cleanup_service import (
    RETENTION_DAYS,
    get_pending_deletions_count,
    run_cleanup,
    schedule_deletion_for_candidate,
)
from app.shared.tenant_guard import get_verified_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lgpd", tags=["lgpd-compliance"])


@router.get("/stats", response_model=LGPDComplianceStats, summary="Get LGPD compliance statistics")
async def get_lgpd_stats(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated LGPD compliance statistics for the company."""
    try:
        company_uuid = UUID(company_id)
        
        dpo_query = select(DPORegistry).where(DPORegistry.company_id == company_uuid)
        dpo_result = await db.execute(dpo_query)
        dpo = dpo_result.scalar_one_or_none()
        
        breach_total_query = select(func.count(BreachNotification.id)).where(
            BreachNotification.company_id == company_uuid
        )
        breach_total_result = await db.execute(breach_total_query)
        total_breaches = breach_total_result.scalar() or 0
        
        breach_open_query = select(func.count(BreachNotification.id)).where(
            and_(
                BreachNotification.company_id == company_uuid,
                BreachNotification.status != "resolved"
            )
        )
        breach_open_result = await db.execute(breach_open_query)
        open_breaches = breach_open_result.scalar() or 0
        
        breach_pending_anpd_query = select(func.count(BreachNotification.id)).where(
            and_(
                BreachNotification.company_id == company_uuid,
                BreachNotification.notification_sent_to_anpd == False,
                BreachNotification.status != "resolved"
            )
        )
        breach_pending_anpd_result = await db.execute(breach_pending_anpd_query)
        breaches_pending_anpd = breach_pending_anpd_result.scalar() or 0
        
        decision_total_query = select(func.count(AutomatedDecisionExplanation.id)).where(
            AutomatedDecisionExplanation.company_id == company_uuid
        )
        decision_total_result = await db.execute(decision_total_query)
        total_decisions = decision_total_result.scalar() or 0
        
        pending_review_query = select(func.count(AutomatedDecisionExplanation.id)).where(
            and_(
                AutomatedDecisionExplanation.company_id == company_uuid,
                AutomatedDecisionExplanation.human_review_requested == True,
                AutomatedDecisionExplanation.human_review_completed_at == None
            )
        )
        pending_review_result = await db.execute(pending_review_query)
        pending_reviews = pending_review_result.scalar() or 0
        
        completed_review_query = select(func.count(AutomatedDecisionExplanation.id)).where(
            and_(
                AutomatedDecisionExplanation.company_id == company_uuid,
                AutomatedDecisionExplanation.human_review_completed_at != None
            )
        )
        completed_review_result = await db.execute(completed_review_query)
        completed_reviews = completed_review_result.scalar() or 0
        
        return LGPDComplianceStats(
            dpo_registered=dpo is not None,
            dpo_active=dpo.is_active if dpo else False,
            total_breaches=total_breaches,
            open_breaches=open_breaches,
            breaches_pending_anpd=breaches_pending_anpd,
            breaches_deadline_exceeded=0,
            total_automated_decisions=total_decisions,
            pending_human_reviews=pending_reviews,
            completed_human_reviews=completed_reviews
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting LGPD stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dpo", response_model=DPORegistryListResponse, summary="List DPO registry entries")
async def list_dpo_entries(
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List all DPO registry entries (admin view)."""
    try:
        conditions = []
        if is_active is not None:
            conditions.append(DPORegistry.is_active == is_active)
        
        query = select(DPORegistry)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(desc(DPORegistry.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        dpos = result.scalars().all()
        
        count_query = select(func.count(DPORegistry.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return DPORegistryListResponse(
            dpos=[DPORegistryResponse(**d.to_dict()) for d in dpos],
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error listing DPO entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dpo/{target_company_id}", response_model=DPORegistryResponse, summary="Get DPO for company")
async def get_dpo_for_company(
    target_company_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get DPO registry entry for a specific company."""
    try:
        target_uuid = UUID(target_company_id)
        
        query = select(DPORegistry).where(DPORegistry.company_id == target_uuid)
        result = await db.execute(query)
        dpo = result.scalar_one_or_none()
        
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
    db: AsyncSession = Depends(get_db)
):
    """Register or update DPO for the company."""
    try:
        company_uuid = UUID(company_id)
        
        existing_query = select(DPORegistry).where(DPORegistry.company_id == company_uuid)
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            existing.dpo_name = data.dpo_name
            existing.dpo_email = data.dpo_email
            existing.dpo_phone = data.dpo_phone
            existing.appointment_date = data.appointment_date
            existing.public_contact_url = data.public_contact_url
            existing.is_active = True
            
            await db.commit()
            await db.refresh(existing)
            
            logger.info(f"Updated DPO registry for company {company_id}")
            return DPORegistryResponse(**existing.to_dict())
        
        dpo = DPORegistry(
            company_id=company_uuid,
            dpo_name=data.dpo_name,
            dpo_email=data.dpo_email,
            dpo_phone=data.dpo_phone,
            appointment_date=data.appointment_date,
            public_contact_url=data.public_contact_url,
            is_active=True
        )
        
        db.add(dpo)
        await db.commit()
        await db.refresh(dpo)
        
        logger.info(f"Created DPO registry for company {company_id}")
        return DPORegistryResponse(**dpo.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating DPO registry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/dpo", response_model=DPORegistryResponse, summary="Update DPO")
async def update_dpo_registry(
    data: DPORegistryUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update DPO registry for the company."""
    try:
        company_uuid = UUID(company_id)
        
        query = select(DPORegistry).where(DPORegistry.company_id == company_uuid)
        result = await db.execute(query)
        dpo = result.scalar_one_or_none()
        
        if not dpo:
            raise HTTPException(status_code=404, detail="DPO not registered for this company")
        
        if data.dpo_name is not None:
            dpo.dpo_name = data.dpo_name
        if data.dpo_email is not None:
            dpo.dpo_email = data.dpo_email
        if data.dpo_phone is not None:
            dpo.dpo_phone = data.dpo_phone
        if data.is_active is not None:
            dpo.is_active = data.is_active
        if data.public_contact_url is not None:
            dpo.public_contact_url = data.public_contact_url
        
        await db.commit()
        await db.refresh(dpo)
        
        logger.info(f"Updated DPO registry for company {company_id}")
        return DPORegistryResponse(**dpo.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
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
    db: AsyncSession = Depends(get_db)
):
    """List breach notifications with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [BreachNotification.company_id == company_uuid]
        
        if severity:
            conditions.append(BreachNotification.severity == severity)
        if status_filter:
            conditions.append(BreachNotification.status == status_filter)
        if pending_anpd is not None:
            conditions.append(BreachNotification.notification_sent_to_anpd == (not pending_anpd))
        
        query = select(BreachNotification).where(and_(*conditions))
        query = query.order_by(desc(BreachNotification.breach_detected_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        breaches = result.scalars().all()
        
        count_query = select(func.count(BreachNotification.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return BreachNotificationListResponse(
            breaches=[BreachNotificationResponse(**b.to_dict()) for b in breaches],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing breach notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breaches/{breach_id}", response_model=BreachNotificationResponse, summary="Get breach notification")
async def get_breach_notification(
    breach_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific breach notification by ID."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == breach_uuid,
                BreachNotification.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        breach = result.scalar_one_or_none()
        
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
    db: AsyncSession = Depends(get_db)
):
    """Report a new data breach. LGPD requires ANPD notification within 48 hours."""
    try:
        company_uuid = UUID(company_id)
        
        breach = BreachNotification(
            company_id=company_uuid,
            breach_detected_at=data.breach_detected_at,
            breach_description=data.breach_description,
            affected_data_types=data.affected_data_types,
            affected_count=data.affected_count,
            severity=data.severity.value,
            status="detected"
        )
        
        db.add(breach)
        await db.commit()
        await db.refresh(breach)
        
        logger.warning(f"LGPD: Data breach reported for company {company_id} - Severity: {data.severity.value}")
        
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating breach notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}", response_model=BreachNotificationResponse, summary="Update breach notification")
async def update_breach_notification(
    breach_id: str,
    data: BreachNotificationUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a breach notification."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == breach_uuid,
                BreachNotification.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        breach = result.scalar_one_or_none()
        
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        
        if data.breach_description is not None:
            breach.breach_description = data.breach_description
        if data.affected_data_types is not None:
            breach.affected_data_types = data.affected_data_types
        if data.affected_count is not None:
            breach.affected_count = data.affected_count
        if data.severity is not None:
            breach.severity = data.severity.value
        if data.remediation_actions is not None:
            breach.remediation_actions = data.remediation_actions
        if data.status is not None:
            breach.status = data.status.value
            if data.status.value == "resolved":
                breach.resolved_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(breach)
        
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating breach notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}/notify-anpd", response_model=BreachNotificationResponse, summary="Mark ANPD notified")
async def mark_anpd_notified(
    breach_id: str,
    data: ANPDNotification,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Mark that ANPD has been notified about the breach (48h requirement)."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == breach_uuid,
                BreachNotification.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        breach = result.scalar_one_or_none()
        
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        
        breach.notification_sent_to_anpd = True
        breach.anpd_notification_at = datetime.utcnow()
        if breach.status == "detected":
            breach.status = "investigating"
        
        await db.commit()
        await db.refresh(breach)
        
        hours_since = breach._hours_since_detection()
        if hours_since and hours_since <= 48:
            logger.info(f"LGPD: ANPD notified within 48h deadline for breach {breach_id}")
        else:
            logger.warning(f"LGPD: ANPD notified AFTER 48h deadline for breach {breach_id} ({hours_since}h)")
        
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking ANPD notified: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}/notify-subjects", response_model=BreachNotificationResponse, summary="Mark subjects notified")
async def mark_subjects_notified(
    breach_id: str,
    data: SubjectsNotification,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Mark that affected data subjects have been notified about the breach."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == breach_uuid,
                BreachNotification.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        breach = result.scalar_one_or_none()
        
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        
        breach.notification_sent_to_subjects = True
        breach.subjects_notification_at = datetime.utcnow()
        if breach.notification_sent_to_anpd and breach.status in ["detected", "investigating"]:
            breach.status = "notified"
        
        await db.commit()
        await db.refresh(breach)
        
        logger.info(f"LGPD: Data subjects notified for breach {breach_id}")
        
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking subjects notified: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/breaches/{breach_id}/resolve", response_model=BreachNotificationResponse, summary="Resolve breach")
async def resolve_breach(
    breach_id: str,
    data: BreachResolution,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Mark a breach as resolved."""
    try:
        company_uuid = UUID(company_id)
        breach_uuid = UUID(breach_id)
        
        query = select(BreachNotification).where(
            and_(
                BreachNotification.id == breach_uuid,
                BreachNotification.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        breach = result.scalar_one_or_none()
        
        if not breach:
            raise HTTPException(status_code=404, detail="Breach notification not found")
        
        if data.remediation_actions:
            breach.remediation_actions = data.remediation_actions
        breach.status = "resolved"
        breach.resolved_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(breach)
        
        logger.info(f"LGPD: Breach {breach_id} resolved")
        
        return BreachNotificationResponse(**breach.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
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
    db: AsyncSession = Depends(get_db)
):
    """List automated decision explanations with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [AutomatedDecisionExplanation.company_id == company_uuid]
        
        if decision_type:
            conditions.append(AutomatedDecisionExplanation.decision_type == decision_type)
        if candidate_id:
            conditions.append(AutomatedDecisionExplanation.candidate_id == UUID(candidate_id))
        if vacancy_id:
            conditions.append(AutomatedDecisionExplanation.vacancy_id == UUID(vacancy_id))
        if pending_review is not None:
            if pending_review:
                conditions.append(AutomatedDecisionExplanation.human_review_requested == True)
                conditions.append(AutomatedDecisionExplanation.human_review_completed_at == None)
            else:
                conditions.append(AutomatedDecisionExplanation.human_review_completed_at != None)
        
        query = select(AutomatedDecisionExplanation).where(and_(*conditions))
        query = query.order_by(desc(AutomatedDecisionExplanation.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        decisions = result.scalars().all()
        
        count_query = select(func.count(AutomatedDecisionExplanation.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return AutomatedDecisionListResponse(
            decisions=[AutomatedDecisionResponse(**d.to_dict()) for d in decisions],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error listing automated decisions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{decision_id}", response_model=AutomatedDecisionResponse, summary="Get automated decision")
async def get_automated_decision(
    decision_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific automated decision explanation by ID."""
    try:
        company_uuid = UUID(company_id)
        decision_uuid = UUID(decision_id)
        
        query = select(AutomatedDecisionExplanation).where(
            and_(
                AutomatedDecisionExplanation.id == decision_uuid,
                AutomatedDecisionExplanation.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        decision = result.scalar_one_or_none()
        
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
    db: AsyncSession = Depends(get_db)
):
    """Record an automated decision for Article 20 compliance."""
    try:
        company_uuid = UUID(company_id)
        
        decision = AutomatedDecisionExplanation(
            company_id=company_uuid,
            decision_type=data.decision_type.value,
            candidate_id=UUID(data.candidate_id) if data.candidate_id else None,
            vacancy_id=UUID(data.vacancy_id) if data.vacancy_id else None,
            ai_model_used=data.ai_model_used,
            input_criteria=data.input_criteria,
            decision_criteria=data.decision_criteria,
            explanation_text=data.explanation_text
        )
        
        db.add(decision)
        await db.commit()
        await db.refresh(decision)
        
        logger.info(f"LGPD Art.20: Recorded automated decision {decision.id} for company {company_id}")
        
        return AutomatedDecisionResponse(**decision.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating automated decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions/{decision_id}/request-human-review", response_model=AutomatedDecisionResponse, summary="Request human review")
async def request_human_review(
    decision_id: str,
    data: HumanReviewRequest,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Request human review of an automated decision (LGPD Article 20)."""
    try:
        company_uuid = UUID(company_id)
        decision_uuid = UUID(decision_id)
        
        query = select(AutomatedDecisionExplanation).where(
            and_(
                AutomatedDecisionExplanation.id == decision_uuid,
                AutomatedDecisionExplanation.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        decision = result.scalar_one_or_none()
        
        if not decision:
            raise HTTPException(status_code=404, detail="Automated decision not found")
        
        if decision.human_review_requested:
            raise HTTPException(status_code=400, detail="Human review already requested")
        
        decision.human_review_requested = True
        decision.explanation_requested_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(decision)
        
        logger.info(f"LGPD Art.20: Human review requested for decision {decision_id}")
        
        return AutomatedDecisionResponse(**decision.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error requesting human review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decisions/{decision_id}/complete-human-review", response_model=AutomatedDecisionResponse, summary="Complete human review")
async def complete_human_review(
    decision_id: str,
    data: HumanReviewComplete,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Complete human review of an automated decision."""
    try:
        company_uuid = UUID(company_id)
        decision_uuid = UUID(decision_id)
        
        query = select(AutomatedDecisionExplanation).where(
            and_(
                AutomatedDecisionExplanation.id == decision_uuid,
                AutomatedDecisionExplanation.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        decision = result.scalar_one_or_none()
        
        if not decision:
            raise HTTPException(status_code=404, detail="Automated decision not found")
        
        if not decision.human_review_requested:
            raise HTTPException(status_code=400, detail="No human review was requested")
        
        if decision.human_review_completed_at:
            raise HTTPException(status_code=400, detail="Human review already completed")
        
        decision.human_review_decision = data.decision
        decision.human_reviewer_id = UUID(data.reviewer_id)
        decision.human_review_completed_at = datetime.utcnow()
        decision.explanation_provided_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(decision)
        
        logger.info(f"LGPD Art.20: Human review completed for decision {decision_id}")
        
        return AutomatedDecisionResponse(**decision.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error completing human review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# L4 — Data Deletion Scheduling (LGPD Art. 16 / Data Retention)
# ---------------------------------------------------------------------------

class ScheduleDeletionRequest(BaseModel):
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
    db: AsyncSession = Depends(get_db),
):
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

    days = data.retention_days or RETENTION_DAYS[data.reason]
    deletion_at = await schedule_deletion_for_candidate(db, data.candidate_id, data.reason, days)

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
):
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
    db: AsyncSession = Depends(get_db),
):
    """Return count of records pending deletion (monitoring/DPO dashboard)."""
    return await get_pending_deletions_count(db)
