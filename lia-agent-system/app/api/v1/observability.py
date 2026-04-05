"""
Observability and Governance API Endpoints.

Provides endpoints for:
- AI Inference Logs (explainability)
- Data Access Logs (LGPD compliance)
- Consent Records (LGPD/GDPR)
- Incident Reports (SOC2, ISO27001)
- Model Evaluations (AI Ethics, bias/fairness)
- Compliance Controls (ISO27001, SOC2, LGPD)
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from uuid import UUID

from app.core.database import get_db
from app.shared.tenant_guard import get_verified_company_id
from app.models.observability import (
    AIInferenceLog, DataAccessLog, ConsentRecord,
    IncidentReport, ModelEvaluation, ComplianceControl, BiasAuditReport
)
from app.schemas.observability import (
    AIInferenceLogResponse, AIInferenceLogListResponse, AIInferenceStatsResponse,
    DataAccessLogResponse, DataAccessLogListResponse, DataAccessStatsResponse,
    ConsentRecordResponse, ConsentRecordListResponse, ConsentCreate, ConsentRevoke,
    IncidentReportResponse, IncidentReportListResponse, IncidentCreate, IncidentUpdate, IncidentResolve,
    ModelEvaluationResponse, ModelEvaluationListResponse, ModelEvaluationSummaryResponse,
    ComplianceControlResponse, ComplianceControlListResponse, ComplianceSummaryResponse, ComplianceControlUpdate,
    ObservabilityDashboardResponse,
    BiasAuditReportResponse, BiasAuditReportListResponse, BiasAuditCreate, BiasAuditPublish, BiasAuditSummaryResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observability", tags=["observability"])


def log_cross_tenant_attempt(requested_id: str, company_id: str, resource_type: str):
    """Log potential cross-tenant access attempts for security auditing."""
    logger.warning(
        f"SECURITY AUDIT: Cross-tenant access attempt detected. "
        f"Company {company_id} attempted to access {resource_type} {requested_id}"
    )


@router.get("/ai-logs/stats", response_model=AIInferenceStatsResponse, summary="Get AI inference statistics")
async def get_ai_inference_stats(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated statistics for AI inference logs."""
    try:
        company_uuid = UUID(company_id)
        conditions = [AIInferenceLog.company_id == company_uuid]
        
        if agent_type:
            conditions.append(AIInferenceLog.agent_type == agent_type)
        if start_date:
            conditions.append(AIInferenceLog.created_at >= start_date)
        if end_date:
            conditions.append(AIInferenceLog.created_at <= end_date)
        
        total_query = select(func.count(AIInferenceLog.id)).where(and_(*conditions))
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        agent_type_query = select(
            AIInferenceLog.agent_type,
            func.count(AIInferenceLog.id).label('count')
        ).where(and_(*conditions)).group_by(AIInferenceLog.agent_type)
        agent_type_result = await db.execute(agent_type_query)
        by_agent_type = {row.agent_type: row.count for row in agent_type_result}
        
        decision_type_query = select(
            AIInferenceLog.decision_type,
            func.count(AIInferenceLog.id).label('count')
        ).where(and_(*conditions)).group_by(AIInferenceLog.decision_type)
        decision_type_result = await db.execute(decision_type_query)
        by_decision_type = {row.decision_type or "unknown": row.count for row in decision_type_result}
        
        avg_query = select(
            func.avg(AIInferenceLog.latency_ms).label('avg_latency'),
            func.avg(AIInferenceLog.confidence_score).label('avg_confidence'),
            func.sum(AIInferenceLog.tokens_used).label('total_tokens')
        ).where(and_(*conditions))
        avg_result = await db.execute(avg_query)
        avg_row = avg_result.one()
        
        override_query = select(func.count(AIInferenceLog.id)).where(
            and_(*conditions, AIInferenceLog.human_override == True)
        )
        override_result = await db.execute(override_query)
        override_count = override_result.scalar() or 0
        
        return AIInferenceStatsResponse(
            total_inferences=total,
            by_agent_type=by_agent_type,
            by_decision_type=by_decision_type,
            avg_latency_ms=float(avg_row.avg_latency) if avg_row.avg_latency else None,
            avg_confidence=float(avg_row.avg_confidence) if avg_row.avg_confidence else None,
            total_tokens_used=int(avg_row.total_tokens) if avg_row.total_tokens else 0,
            human_override_count=override_count,
            human_override_rate=round(override_count / total * 100, 2) if total > 0 else 0,
            bias_flags_count=0
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting AI inference stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-logs", response_model=AIInferenceLogListResponse, summary="List AI inference logs")
async def list_ai_inference_logs(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List AI inference logs with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [AIInferenceLog.company_id == company_uuid]
        
        if agent_type:
            conditions.append(AIInferenceLog.agent_type == agent_type)
        if candidate_id:
            conditions.append(AIInferenceLog.candidate_id == UUID(candidate_id))
        if vacancy_id:
            conditions.append(AIInferenceLog.vacancy_id == UUID(vacancy_id))
        if start_date:
            conditions.append(AIInferenceLog.created_at >= start_date)
        if end_date:
            conditions.append(AIInferenceLog.created_at <= end_date)
        
        query = select(AIInferenceLog).where(and_(*conditions))
        query = query.order_by(desc(AIInferenceLog.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        count_query = select(func.count(AIInferenceLog.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return AIInferenceLogListResponse(
            logs=[AIInferenceLogResponse(**log.to_dict()) for log in logs],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error listing AI inference logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-logs/{log_id}", response_model=AIInferenceLogResponse, summary="Get AI inference log by ID")
async def get_ai_inference_log(
    log_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific AI inference log by ID."""
    try:
        company_uuid = UUID(company_id)
        log_uuid = UUID(log_id)
        
        query = select(AIInferenceLog).where(
            and_(
                AIInferenceLog.id == log_uuid,
                AIInferenceLog.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        log = result.scalar_one_or_none()
        
        if not log:
            log_cross_tenant_attempt(log_id, company_id, "AIInferenceLog")
            raise HTTPException(status_code=404, detail="AI inference log not found")
        
        return AIInferenceLogResponse(**log.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI inference log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-access/stats", response_model=DataAccessStatsResponse, summary="Get data access statistics")
async def get_data_access_stats(
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    operation: Optional[str] = Query(None, description="Filter by operation"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated statistics for data access logs (LGPD)."""
    try:
        company_uuid = UUID(company_id)
        conditions = [DataAccessLog.company_id == company_uuid]
        
        if data_type:
            conditions.append(DataAccessLog.data_type == data_type)
        if operation:
            conditions.append(DataAccessLog.operation == operation)
        if start_date:
            conditions.append(DataAccessLog.created_at >= start_date)
        if end_date:
            conditions.append(DataAccessLog.created_at <= end_date)
        
        total_query = select(func.count(DataAccessLog.id)).where(and_(*conditions))
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        data_type_query = select(
            DataAccessLog.data_type,
            func.count(DataAccessLog.id).label('count')
        ).where(and_(*conditions)).group_by(DataAccessLog.data_type)
        data_type_result = await db.execute(data_type_query)
        by_data_type = {row.data_type: row.count for row in data_type_result}
        
        operation_query = select(
            DataAccessLog.operation,
            func.count(DataAccessLog.id).label('count')
        ).where(and_(*conditions)).group_by(DataAccessLog.operation)
        operation_result = await db.execute(operation_query)
        by_operation = {row.operation: row.count for row in operation_result}
        
        legal_basis_query = select(
            DataAccessLog.legal_basis,
            func.count(DataAccessLog.id).label('count')
        ).where(and_(*conditions)).group_by(DataAccessLog.legal_basis)
        legal_basis_result = await db.execute(legal_basis_query)
        by_legal_basis = {row.legal_basis or "unknown": row.count for row in legal_basis_result}
        
        unique_users_query = select(func.count(func.distinct(DataAccessLog.user_id))).where(and_(*conditions))
        unique_users_result = await db.execute(unique_users_query)
        unique_users = unique_users_result.scalar() or 0
        
        unique_subjects_query = select(func.count(func.distinct(DataAccessLog.data_subject_id))).where(and_(*conditions))
        unique_subjects_result = await db.execute(unique_subjects_query)
        unique_subjects = unique_subjects_result.scalar() or 0
        
        return DataAccessStatsResponse(
            total_accesses=total,
            by_data_type=by_data_type,
            by_operation=by_operation,
            by_legal_basis=by_legal_basis,
            unique_users=unique_users,
            unique_data_subjects=unique_subjects
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting data access stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-access", response_model=DataAccessLogListResponse, summary="List data access logs")
async def list_data_access_logs(
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    operation: Optional[str] = Query(None, description="Filter by operation"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    data_subject_id: Optional[str] = Query(None, description="Filter by data subject ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List data access logs with optional filters (LGPD compliance)."""
    try:
        company_uuid = UUID(company_id)
        conditions = [DataAccessLog.company_id == company_uuid]
        
        if data_type:
            conditions.append(DataAccessLog.data_type == data_type)
        if operation:
            conditions.append(DataAccessLog.operation == operation)
        if user_id:
            conditions.append(DataAccessLog.user_id == UUID(user_id))
        if data_subject_id:
            conditions.append(DataAccessLog.data_subject_id == UUID(data_subject_id))
        if start_date:
            conditions.append(DataAccessLog.created_at >= start_date)
        if end_date:
            conditions.append(DataAccessLog.created_at <= end_date)
        
        query = select(DataAccessLog).where(and_(*conditions))
        query = query.order_by(desc(DataAccessLog.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        count_query = select(func.count(DataAccessLog.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return DataAccessLogListResponse(
            logs=[DataAccessLogResponse(**log.to_dict()) for log in logs],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error listing data access logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consents", response_model=ConsentRecordListResponse, summary="List consent records")
async def list_consent_records(
    consent_type: Optional[str] = Query(None, description="Filter by consent type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List consent records with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [ConsentRecord.company_id == company_uuid]
        
        if consent_type:
            conditions.append(ConsentRecord.consent_type == consent_type)
        if is_active is not None:
            conditions.append(ConsentRecord.is_active == is_active)
        
        query = select(ConsentRecord).where(and_(*conditions))
        query = query.order_by(desc(ConsentRecord.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        consents = result.scalars().all()
        
        count_query = select(func.count(ConsentRecord.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return ConsentRecordListResponse(
            consents=[ConsentRecordResponse(**c.to_dict()) for c in consents],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing consent records: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consents/{candidate_id}", response_model=ConsentRecordListResponse, summary="Get consents by candidate")
async def get_candidate_consents(
    candidate_id: str,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all consent records for a specific candidate."""
    try:
        company_uuid = UUID(company_id)
        candidate_uuid = UUID(candidate_id)
        conditions = [
            ConsentRecord.company_id == company_uuid,
            ConsentRecord.candidate_id == candidate_uuid
        ]
        
        if is_active is not None:
            conditions.append(ConsentRecord.is_active == is_active)
        
        query = select(ConsentRecord).where(and_(*conditions))
        query = query.order_by(desc(ConsentRecord.created_at))
        
        result = await db.execute(query)
        consents = result.scalars().all()
        
        return ConsentRecordListResponse(
            consents=[ConsentRecordResponse(**c.to_dict()) for c in consents],
            total=len(consents),
            limit=100,
            offset=0
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error getting candidate consents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consents", response_model=ConsentRecordResponse, status_code=status.HTTP_201_CREATED, summary="Create consent record")
async def create_consent_record(
    data: ConsentCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Register a new consent record."""
    try:
        company_uuid = UUID(company_id)
        candidate_uuid = UUID(data.candidate_id)
        
        consent = ConsentRecord(
            company_id=company_uuid,
            candidate_id=candidate_uuid,
            consent_type=data.consent_type,
            version=data.version,
            granted_at=datetime.utcnow(),
            expires_at=data.expires_at,
            ip_address=data.ip_address,
            source=data.source,
            legal_basis=data.legal_basis,
            consent_text=data.consent_text,
            is_active=True
        )
        
        db.add(consent)
        await db.commit()
        await db.refresh(consent)
        
        logger.info(f"Created consent record: {consent.id} for candidate {candidate_uuid}")
        
        return ConsentRecordResponse(**consent.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating consent record: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/consents/{consent_id}/revoke", response_model=ConsentRecordResponse, summary="Revoke consent")
async def revoke_consent(
    consent_id: str,
    data: ConsentRevoke,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an existing consent record."""
    try:
        company_uuid = UUID(company_id)
        consent_uuid = UUID(consent_id)
        
        query = select(ConsentRecord).where(
            and_(
                ConsentRecord.id == consent_uuid,
                ConsentRecord.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        consent = result.scalar_one_or_none()
        
        if not consent:
            log_cross_tenant_attempt(consent_id, company_id, "ConsentRecord")
            raise HTTPException(status_code=404, detail="Consent record not found")
        
        consent.is_active = False
        consent.revoked_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(consent)
        
        logger.info(f"Revoked consent: {consent_id} for company {company_id}")
        
        return ConsentRecordResponse(**consent.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error revoking consent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents", response_model=IncidentReportListResponse, summary="List incidents")
async def list_incidents(
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List incident reports with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [IncidentReport.company_id == company_uuid]
        
        if incident_type:
            conditions.append(IncidentReport.incident_type == incident_type)
        if severity:
            conditions.append(IncidentReport.severity == severity)
        if status_filter:
            conditions.append(IncidentReport.status == status_filter)
        if start_date:
            conditions.append(IncidentReport.detected_at >= start_date)
        if end_date:
            conditions.append(IncidentReport.detected_at <= end_date)
        
        query = select(IncidentReport).where(and_(*conditions))
        query = query.order_by(desc(IncidentReport.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        incidents = result.scalars().all()
        
        count_query = select(func.count(IncidentReport.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return IncidentReportListResponse(
            incidents=[IncidentReportResponse(**i.to_dict()) for i in incidents],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing incidents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents", response_model=IncidentReportResponse, status_code=status.HTTP_201_CREATED, summary="Create incident")
async def create_incident(
    data: IncidentCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new incident report."""
    try:
        company_uuid = UUID(company_id)
        
        incident = IncidentReport(
            company_id=company_uuid,
            incident_type=data.incident_type,
            severity=data.severity,
            description=data.description,
            affected_resources=data.affected_resources or [],
            detected_at=data.detected_at or datetime.utcnow(),
            status="open"
        )
        
        db.add(incident)
        await db.commit()
        await db.refresh(incident)
        
        logger.info(f"Created incident: {incident.id} - {data.incident_type}")
        
        return IncidentReportResponse(**incident.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/incidents/{incident_id}", response_model=IncidentReportResponse, summary="Update incident")
async def update_incident(
    incident_id: str,
    data: IncidentUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing incident report."""
    try:
        company_uuid = UUID(company_id)
        incident_uuid = UUID(incident_id)
        
        query = select(IncidentReport).where(
            and_(
                IncidentReport.id == incident_uuid,
                IncidentReport.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            log_cross_tenant_attempt(incident_id, company_id, "IncidentReport")
            raise HTTPException(status_code=404, detail="Incident not found")
        
        if data.severity is not None:
            incident.severity = data.severity
        if data.description is not None:
            incident.description = data.description
        if data.root_cause is not None:
            incident.root_cause = data.root_cause
        if data.remediation_actions is not None:
            incident.remediation_actions = data.remediation_actions
        if data.notified_parties is not None:
            incident.notified_parties = data.notified_parties
        if data.status is not None:
            incident.status = data.status
        if data.assigned_to is not None:
            incident.assigned_to = UUID(data.assigned_to)
        
        await db.commit()
        await db.refresh(incident)
        
        logger.info(f"Updated incident: {incident_id}")
        
        return IncidentReportResponse(**incident.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/incidents/{incident_id}/resolve", response_model=IncidentReportResponse, summary="Resolve incident")
async def resolve_incident(
    incident_id: str,
    data: IncidentResolve,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Mark an incident as resolved."""
    try:
        company_uuid = UUID(company_id)
        incident_uuid = UUID(incident_id)
        
        query = select(IncidentReport).where(
            and_(
                IncidentReport.id == incident_uuid,
                IncidentReport.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            log_cross_tenant_attempt(incident_id, company_id, "IncidentReport")
            raise HTTPException(status_code=404, detail="Incident not found")
        
        incident.status = "resolved"
        incident.resolved_at = datetime.utcnow()
        
        if data.root_cause:
            incident.root_cause = data.root_cause
        if data.remediation_actions:
            incident.remediation_actions = data.remediation_actions
        
        await db.commit()
        await db.refresh(incident)
        
        logger.info(f"Resolved incident: {incident_id}")
        
        return IncidentReportResponse(**incident.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error resolving incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluations/summary", response_model=ModelEvaluationSummaryResponse, summary="Get evaluation summary")
async def get_evaluation_summary(
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of model evaluations by dimension."""
    try:
        company_uuid = UUID(company_id)
        conditions = [ModelEvaluation.company_id == company_uuid]
        
        if model_version:
            conditions.append(ModelEvaluation.model_version == model_version)
        
        total_query = select(func.count(ModelEvaluation.id)).where(and_(*conditions))
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        dimension_query = select(
            ModelEvaluation.dimension,
            func.count(ModelEvaluation.id).label('count'),
            func.avg(ModelEvaluation.metric_value).label('avg_value'),
            func.sum(func.cast(ModelEvaluation.passed, Integer)).label('passed_count')
        ).where(and_(*conditions)).group_by(ModelEvaluation.dimension)
        
        from sqlalchemy import Integer
        dimension_query = select(
            ModelEvaluation.dimension,
            func.count(ModelEvaluation.id).label('count')
        ).where(and_(*conditions)).group_by(ModelEvaluation.dimension)
        dimension_result = await db.execute(dimension_query)
        by_dimension = {}
        for row in dimension_result:
            by_dimension[row.dimension or "general"] = {"count": row.count}
        
        type_query = select(
            ModelEvaluation.evaluation_type,
            func.count(ModelEvaluation.id).label('count')
        ).where(and_(*conditions)).group_by(ModelEvaluation.evaluation_type)
        type_result = await db.execute(type_query)
        by_type = {row.evaluation_type: row.count for row in type_result}
        
        passed_query = select(func.count(ModelEvaluation.id)).where(
            and_(*conditions, ModelEvaluation.passed == True)
        )
        passed_result = await db.execute(passed_query)
        passed_count = passed_result.scalar() or 0
        
        latest_query = select(func.max(ModelEvaluation.evaluation_date)).where(and_(*conditions))
        latest_result = await db.execute(latest_query)
        latest_date = latest_result.scalar()
        
        return ModelEvaluationSummaryResponse(
            total_evaluations=total,
            by_dimension=by_dimension,
            by_evaluation_type=by_type,
            pass_rate=round(passed_count / total * 100, 2) if total > 0 else 0,
            latest_evaluation_date=latest_date
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting evaluation summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluations", response_model=ModelEvaluationListResponse, summary="List model evaluations")
async def list_model_evaluations(
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    evaluation_type: Optional[str] = Query(None, description="Filter by evaluation type"),
    dimension: Optional[str] = Query(None, description="Filter by dimension"),
    passed: Optional[bool] = Query(None, description="Filter by pass status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List model evaluations with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [ModelEvaluation.company_id == company_uuid]
        
        if model_version:
            conditions.append(ModelEvaluation.model_version == model_version)
        if evaluation_type:
            conditions.append(ModelEvaluation.evaluation_type == evaluation_type)
        if dimension:
            conditions.append(ModelEvaluation.dimension == dimension)
        if passed is not None:
            conditions.append(ModelEvaluation.passed == passed)
        
        query = select(ModelEvaluation).where(and_(*conditions))
        query = query.order_by(desc(ModelEvaluation.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        evaluations = result.scalars().all()
        
        count_query = select(func.count(ModelEvaluation.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return ModelEvaluationListResponse(
            evaluations=[ModelEvaluationResponse(**e.to_dict()) for e in evaluations],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing model evaluations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/summary", response_model=ComplianceSummaryResponse, summary="Get compliance summary")
async def get_compliance_summary(
    framework: Optional[str] = Query(None, description="Filter by framework"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of compliance controls by framework."""
    try:
        company_uuid = UUID(company_id)
        conditions = [ComplianceControl.company_id == company_uuid]
        
        if framework:
            conditions.append(ComplianceControl.framework == framework)
        
        total_query = select(func.count(ComplianceControl.id)).where(and_(*conditions))
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        framework_query = select(
            ComplianceControl.framework,
            ComplianceControl.status,
            func.count(ComplianceControl.id).label('count')
        ).where(and_(*conditions)).group_by(
            ComplianceControl.framework,
            ComplianceControl.status
        )
        framework_result = await db.execute(framework_query)
        
        by_framework = {}
        for row in framework_result:
            if row.framework not in by_framework:
                by_framework[row.framework] = {}
            by_framework[row.framework][row.status] = row.count
        
        status_query = select(
            ComplianceControl.status,
            func.count(ComplianceControl.id).label('count')
        ).where(and_(*conditions)).group_by(ComplianceControl.status)
        status_result = await db.execute(status_query)
        by_status = {row.status: row.count for row in status_result}
        
        now = datetime.utcnow()
        overdue_query = select(func.count(ComplianceControl.id)).where(
            and_(*conditions, ComplianceControl.next_review_at < now)
        )
        overdue_result = await db.execute(overdue_query)
        overdue = overdue_result.scalar() or 0
        
        upcoming_date = now + timedelta(days=30)
        upcoming_query = select(func.count(ComplianceControl.id)).where(
            and_(
                *conditions,
                ComplianceControl.next_review_at >= now,
                ComplianceControl.next_review_at <= upcoming_date
            )
        )
        upcoming_result = await db.execute(upcoming_query)
        upcoming = upcoming_result.scalar() or 0
        
        return ComplianceSummaryResponse(
            total_controls=total,
            by_framework=by_framework,
            by_status=by_status,
            overdue_reviews=overdue,
            upcoming_reviews=upcoming
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance", response_model=ComplianceControlListResponse, summary="List compliance controls")
async def list_compliance_controls(
    framework: Optional[str] = Query(None, description="Filter by framework"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List compliance controls with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [ComplianceControl.company_id == company_uuid]
        
        if framework:
            conditions.append(ComplianceControl.framework == framework)
        if status_filter:
            conditions.append(ComplianceControl.status == status_filter)
        if risk_level:
            conditions.append(ComplianceControl.risk_level == risk_level)
        
        query = select(ComplianceControl).where(and_(*conditions))
        query = query.order_by(ComplianceControl.framework, ComplianceControl.control_id)
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        controls = result.scalars().all()
        
        count_query = select(func.count(ComplianceControl.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return ComplianceControlListResponse(
            controls=[ComplianceControlResponse(**c.to_dict()) for c in controls],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing compliance controls: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/compliance/{control_id}", response_model=ComplianceControlResponse, summary="Update compliance control")
async def update_compliance_control(
    control_id: str,
    data: ComplianceControlUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a compliance control."""
    try:
        company_uuid = UUID(company_id)
        control_uuid = UUID(control_id)
        
        query = select(ComplianceControl).where(
            and_(
                ComplianceControl.id == control_uuid,
                ComplianceControl.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        control = result.scalar_one_or_none()
        
        if not control:
            log_cross_tenant_attempt(control_id, company_id, "ComplianceControl")
            raise HTTPException(status_code=404, detail="Compliance control not found")
        
        if data.status is not None:
            control.status = data.status
        if data.evidence_url is not None:
            control.evidence_url = data.evidence_url
        if data.evidence_notes is not None:
            control.evidence_notes = data.evidence_notes
        if data.owner is not None:
            control.owner = data.owner
        if data.owner_email is not None:
            control.owner_email = data.owner_email
        if data.next_review_at is not None:
            control.next_review_at = data.next_review_at
        
        control.last_reviewed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(control)
        
        logger.info(f"Updated compliance control: {control_id}")
        
        return ComplianceControlResponse(**control.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating compliance control: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_model=ObservabilityDashboardResponse, summary="Get dashboard data")
async def get_observability_dashboard(
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get consolidated dashboard data for observability."""
    try:
        company_uuid = UUID(company_id)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        ai_total_query = select(func.count(AIInferenceLog.id)).where(
            and_(
                AIInferenceLog.company_id == company_uuid,
                AIInferenceLog.created_at >= start_date
            )
        )
        ai_total_result = await db.execute(ai_total_query)
        ai_total = ai_total_result.scalar() or 0
        
        data_access_total_query = select(func.count(DataAccessLog.id)).where(
            and_(
                DataAccessLog.company_id == company_uuid,
                DataAccessLog.created_at >= start_date
            )
        )
        data_access_total_result = await db.execute(data_access_total_query)
        data_access_total = data_access_total_result.scalar() or 0
        
        active_consents_query = select(func.count(ConsentRecord.id)).where(
            and_(
                ConsentRecord.company_id == company_uuid,
                ConsentRecord.is_active == True
            )
        )
        active_consents_result = await db.execute(active_consents_query)
        active_consents = active_consents_result.scalar() or 0
        
        open_incidents_query = select(func.count(IncidentReport.id)).where(
            and_(
                IncidentReport.company_id == company_uuid,
                IncidentReport.status == "open"
            )
        )
        open_incidents_result = await db.execute(open_incidents_query)
        open_incidents = open_incidents_result.scalar() or 0
        
        critical_incidents_query = select(func.count(IncidentReport.id)).where(
            and_(
                IncidentReport.company_id == company_uuid,
                IncidentReport.status == "open",
                IncidentReport.severity == "critical"
            )
        )
        critical_incidents_result = await db.execute(critical_incidents_query)
        critical_incidents = critical_incidents_result.scalar() or 0
        
        eval_count_query = select(func.count(ModelEvaluation.id)).where(
            ModelEvaluation.company_id == company_uuid
        )
        eval_count_result = await db.execute(eval_count_query)
        eval_count = eval_count_result.scalar() or 0
        
        passed_count_query = select(func.count(ModelEvaluation.id)).where(
            and_(
                ModelEvaluation.company_id == company_uuid,
                ModelEvaluation.passed == True
            )
        )
        passed_count_result = await db.execute(passed_count_query)
        passed_count = passed_count_result.scalar() or 0
        
        compliance_total_query = select(func.count(ComplianceControl.id)).where(
            ComplianceControl.company_id == company_uuid
        )
        compliance_total_result = await db.execute(compliance_total_query)
        compliance_total = compliance_total_result.scalar() or 0
        
        implemented_query = select(func.count(ComplianceControl.id)).where(
            and_(
                ComplianceControl.company_id == company_uuid,
                ComplianceControl.status == "implemented"
            )
        )
        implemented_result = await db.execute(implemented_query)
        implemented = implemented_result.scalar() or 0
        
        alerts = []
        if critical_incidents > 0:
            alerts.append({
                "type": "critical",
                "message": f"{critical_incidents} critical incident(s) require immediate attention",
                "category": "incidents"
            })
        if open_incidents > 5:
            alerts.append({
                "type": "warning",
                "message": f"{open_incidents} open incidents pending resolution",
                "category": "incidents"
            })
        
        return ObservabilityDashboardResponse(
            ai_inference={
                "total_inferences": ai_total,
                "period_days": period_days
            },
            data_access={
                "total_accesses": data_access_total,
                "period_days": period_days
            },
            consents={
                "active_consents": active_consents
            },
            incidents={
                "open_count": open_incidents,
                "critical_count": critical_incidents
            },
            evaluations={
                "total_evaluations": eval_count,
                "pass_rate": round(passed_count / eval_count * 100, 2) if eval_count > 0 else 0
            },
            compliance={
                "total_controls": compliance_total,
                "implemented_count": implemented,
                "compliance_rate": round(implemented / compliance_total * 100, 2) if compliance_total > 0 else 0
            },
            alerts=alerts
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bias-audits/latest", response_model=BiasAuditReportResponse, summary="Get latest bias audit")
async def get_latest_bias_audit(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent bias audit report for the company."""
    try:
        company_uuid = UUID(company_id)
        
        query = select(BiasAuditReport).where(
            BiasAuditReport.company_id == company_uuid
        ).order_by(desc(BiasAuditReport.audit_date)).limit(1)
        
        result = await db.execute(query)
        audit = result.scalar_one_or_none()
        
        if not audit:
            raise HTTPException(status_code=404, detail="No bias audit found for this company")
        
        return BiasAuditReportResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest bias audit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bias-audits/summary", response_model=BiasAuditSummaryResponse, summary="Get bias audit summary")
async def get_bias_audit_summary(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a summary of all bias audits for the company."""
    try:
        company_uuid = UUID(company_id)
        
        total_query = select(func.count(BiasAuditReport.id)).where(
            BiasAuditReport.company_id == company_uuid
        )
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0
        
        audit_type_query = select(
            BiasAuditReport.audit_type,
            func.count(BiasAuditReport.id).label('count')
        ).where(BiasAuditReport.company_id == company_uuid).group_by(BiasAuditReport.audit_type)
        audit_type_result = await db.execute(audit_type_query)
        by_audit_type = {row.audit_type: row.count for row in audit_type_result}
        
        public_query = select(func.count(BiasAuditReport.id)).where(
            and_(
                BiasAuditReport.company_id == company_uuid,
                BiasAuditReport.is_public == True
            )
        )
        public_result = await db.execute(public_query)
        public_count = public_result.scalar() or 0
        
        latest_query = select(BiasAuditReport).where(
            BiasAuditReport.company_id == company_uuid
        ).order_by(desc(BiasAuditReport.audit_date)).limit(1)
        latest_result = await db.execute(latest_query)
        latest_audit = latest_result.scalar_one_or_none()
        
        frameworks_query = select(BiasAuditReport.compliance_frameworks).where(
            BiasAuditReport.company_id == company_uuid
        )
        frameworks_result = await db.execute(frameworks_query)
        all_frameworks = set()
        for row in frameworks_result:
            if row.compliance_frameworks:
                all_frameworks.update(row.compliance_frameworks)
        
        status_counts = {"clear": 0, "consider": 0, "concern": 0}
        if latest_audit:
            status_counts["clear"] = latest_audit.clear_count or 0
            status_counts["consider"] = latest_audit.consider_count or 0
            status_counts["concern"] = latest_audit.concern_count or 0
        
        return BiasAuditSummaryResponse(
            total_audits=total,
            latest_audit_date=latest_audit.audit_date if latest_audit else None,
            latest_overall_score=float(latest_audit.overall_score) if latest_audit and latest_audit.overall_score else None,
            by_audit_type=by_audit_type,
            by_status=status_counts,
            compliance_coverage=list(all_frameworks),
            public_audits_count=public_count
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting bias audit summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bias-audits", response_model=BiasAuditReportListResponse, summary="List bias audits")
async def list_bias_audits(
    audit_type: Optional[str] = Query(None, description="Filter by audit type"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List bias audit reports with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [BiasAuditReport.company_id == company_uuid]
        
        if audit_type:
            conditions.append(BiasAuditReport.audit_type == audit_type)
        if is_public is not None:
            conditions.append(BiasAuditReport.is_public == is_public)
        if start_date:
            conditions.append(BiasAuditReport.audit_date >= start_date.date())
        if end_date:
            conditions.append(BiasAuditReport.audit_date <= end_date.date())
        
        query = select(BiasAuditReport).where(and_(*conditions))
        query = query.order_by(desc(BiasAuditReport.audit_date))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        audits = result.scalars().all()
        
        count_query = select(func.count(BiasAuditReport.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return BiasAuditReportListResponse(
            audits=[BiasAuditReportResponse(**audit.to_dict()) for audit in audits],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing bias audits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bias-audits/{audit_id}", response_model=BiasAuditReportResponse, summary="Get bias audit by ID")
async def get_bias_audit(
    audit_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific bias audit report by ID."""
    try:
        company_uuid = UUID(company_id)
        audit_uuid = UUID(audit_id)
        
        query = select(BiasAuditReport).where(
            and_(
                BiasAuditReport.id == audit_uuid,
                BiasAuditReport.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        audit = result.scalar_one_or_none()
        
        if not audit:
            log_cross_tenant_attempt(audit_id, company_id, "BiasAuditReport")
            raise HTTPException(status_code=404, detail="Bias audit report not found")
        
        return BiasAuditReportResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bias audit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bias-audits", response_model=BiasAuditReportResponse, status_code=status.HTTP_201_CREATED, summary="Create bias audit")
async def create_bias_audit(
    data: BiasAuditCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new bias audit report."""
    try:
        company_uuid = UUID(company_id)
        
        clear_count = 0
        consider_count = 0
        concern_count = 0
        for category, result in data.bias_results.items():
            if isinstance(result, dict) and 'status' in result:
                status_val = result['status'].lower()
                if status_val == 'clear':
                    clear_count += 1
                elif status_val == 'consider':
                    consider_count += 1
                elif status_val == 'concern':
                    concern_count += 1
        
        audit = BiasAuditReport(
            company_id=company_uuid,
            audit_type=data.audit_type,
            audit_date=data.audit_date,
            sample_size=data.sample_size,
            auditor=data.auditor,
            auditor_name=data.auditor_name,
            auditor_organization=data.auditor_organization,
            bias_results=data.bias_results,
            overall_score=data.overall_score,
            clear_count=clear_count,
            consider_count=consider_count,
            concern_count=concern_count,
            compliance_frameworks=data.compliance_frameworks or [],
            report_url=data.report_url,
            notes=data.notes,
            recommendations=data.recommendations or [],
            is_public=False
        )
        
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        
        logger.info(f"Created bias audit report: {audit.id} for company {company_uuid}")
        
        return BiasAuditReportResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating bias audit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bias-audits/{audit_id}/publish", response_model=BiasAuditReportResponse, summary="Publish bias audit")
async def publish_bias_audit(
    audit_id: str,
    data: BiasAuditPublish,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Publish or unpublish a bias audit report."""
    try:
        company_uuid = UUID(company_id)
        audit_uuid = UUID(audit_id)
        
        query = select(BiasAuditReport).where(
            and_(
                BiasAuditReport.id == audit_uuid,
                BiasAuditReport.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        audit = result.scalar_one_or_none()
        
        if not audit:
            log_cross_tenant_attempt(audit_id, company_id, "BiasAuditReport")
            raise HTTPException(status_code=404, detail="Bias audit report not found")
        
        audit.is_public = data.is_public
        if data.report_url:
            audit.report_url = data.report_url
        
        await db.commit()
        await db.refresh(audit)
        
        action = "published" if data.is_public else "unpublished"
        logger.info(f"Bias audit {audit_id} {action} for company {company_id}")
        
        return BiasAuditReportResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error publishing bias audit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
