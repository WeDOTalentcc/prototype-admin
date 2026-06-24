
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
import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.dependencies import get_observability_repo
from app.repositories.observability_repository import ObservabilityRepository
from app.schemas.observability import (
    AIInferenceLogListResponse,
    AIInferenceLogResponse,
    AIInferenceStatsResponse,
    BiasAuditCreate,
    BiasAuditPublish,
    BiasAuditReportListResponse,
    BiasAuditReportResponse,
    BiasAuditSummaryResponse,
    ComplianceControlListResponse,
    ComplianceControlResponse,
    ComplianceControlUpdate,
    ComplianceSummaryResponse,
    ConsentCreate,
    ConsentRecordListResponse,
    ConsentRecordResponse,
    ConsentRevoke,
    DataAccessLogListResponse,
    DataAccessLogResponse,
    DataAccessStatsResponse,
    IncidentCreate,
    IncidentReportListResponse,
    IncidentReportResponse,
    IncidentResolve,
    IncidentUpdate,
    ModelEvaluationListResponse,
    ModelEvaluationResponse,
    ModelEvaluationSummaryResponse,
    ObservabilityDashboardResponse,
)
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError

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
    agent_type: str | None = Query(None, description="Filter by agent type"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get aggregated statistics for AI inference logs."""
    try:
        company_uuid = UUID(company_id)
        stats = await repo.get_ai_inference_stats(
            company_uuid=company_uuid,
            agent_type=agent_type,
            start_date=start_date,
            end_date=end_date,
        )
        total = stats["total"]
        override_count = stats["override_count"]
        return AIInferenceStatsResponse(
            total_inferences=total,
            by_agent_type=stats["by_agent_type"],
            by_decision_type=stats["by_decision_type"],
            avg_latency_ms=float(stats["avg_latency"]) if stats["avg_latency"] else None,
            avg_confidence=float(stats["avg_confidence"]) if stats["avg_confidence"] else None,
            total_tokens_used=int(stats["total_tokens"]) if stats["total_tokens"] else 0,
            human_override_count=override_count,
            human_override_rate=round(override_count / total * 100, 2) if total > 0 else 0,
            bias_flags_count=0
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI inference stats: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/ai-logs", response_model=AIInferenceLogListResponse, summary="List AI inference logs")
async def list_ai_inference_logs(
    agent_type: str | None = Query(None, description="Filter by agent type"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    vacancy_id: str | None = Query(None, description="Filter by vacancy ID"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List AI inference logs with optional filters."""
    try:
        company_uuid = UUID(company_id)
        logs, total = await repo.list_ai_inference_logs(
            company_uuid=company_uuid,
            agent_type=agent_type,
            candidate_id=UUID(candidate_id) if candidate_id else None,
            vacancy_id=UUID(vacancy_id) if vacancy_id else None,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return AIInferenceLogListResponse(
            logs=[AIInferenceLogResponse(**log.to_dict()) for log in logs],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing AI inference logs: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/ai-logs/{log_id}", response_model=AIInferenceLogResponse, summary="Get AI inference log by ID")
async def get_ai_inference_log(
    log_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific AI inference log by ID."""
    try:
        company_uuid = UUID(company_id)
        log_uuid = UUID(log_id)
        log = await repo.get_ai_inference_log(log_uuid, company_uuid)
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
        raise LIAError(message="Erro interno do servidor")


@router.get("/data-access/stats", response_model=DataAccessStatsResponse, summary="Get data access statistics")
async def get_data_access_stats(
    data_type: str | None = Query(None, description="Filter by data type"),
    operation: str | None = Query(None, description="Filter by operation"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get aggregated statistics for data access logs (LGPD)."""
    try:
        company_uuid = UUID(company_id)
        stats = await repo.get_data_access_stats(
            company_uuid=company_uuid,
            data_type=data_type,
            operation=operation,
            start_date=start_date,
            end_date=end_date,
        )
        return DataAccessStatsResponse(
            total_accesses=stats["total"],
            by_data_type=stats["by_data_type"],
            by_operation=stats["by_operation"],
            by_legal_basis=stats["by_legal_basis"],
            unique_users=stats["unique_users"],
            unique_data_subjects=stats["unique_subjects"]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data access stats: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/data-access", response_model=DataAccessLogListResponse, summary="List data access logs")
async def list_data_access_logs(
    data_type: str | None = Query(None, description="Filter by data type"),
    operation: str | None = Query(None, description="Filter by operation"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    data_subject_id: str | None = Query(None, description="Filter by data subject ID"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List data access logs with optional filters (LGPD compliance)."""
    try:
        company_uuid = UUID(company_id)
        logs, total = await repo.list_data_access_logs(
            company_uuid=company_uuid,
            data_type=data_type,
            operation=operation,
            user_id=UUID(user_id) if user_id else None,
            data_subject_id=UUID(data_subject_id) if data_subject_id else None,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return DataAccessLogListResponse(
            logs=[DataAccessLogResponse(**log.to_dict()) for log in logs],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing data access logs: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/consents", response_model=ConsentRecordListResponse, summary="List consent records")
async def list_consent_records(
    consent_type: str | None = Query(None, description="Filter by consent type"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List consent records with optional filters."""
    try:
        company_uuid = UUID(company_id)
        consents, total = await repo.list_consent_records(
            company_uuid=company_uuid,
            consent_type=consent_type,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        return ConsentRecordListResponse(
            consents=[ConsentRecordResponse(**c.to_dict()) for c in consents],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing consent records: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/consents/{candidate_id}", response_model=ConsentRecordListResponse, summary="Get consents by candidate")
async def get_candidate_consents(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    is_active: bool | None = Query(None, description="Filter by active status"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get all consent records for a specific candidate."""
    try:
        company_uuid = UUID(company_id)
        candidate_uuid = UUID(candidate_id)
        consents = await repo.list_consents_by_candidate(
            company_uuid=company_uuid,
            candidate_uuid=candidate_uuid,
            is_active=is_active,
        )
        return ConsentRecordListResponse(
            consents=[ConsentRecordResponse(**c.to_dict()) for c in consents],
            total=len(consents),
            limit=100,
            offset=0
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate consents: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/consents", response_model=ConsentRecordResponse, status_code=status.HTTP_201_CREATED, summary="Create consent record")
async def create_consent_record(
    data: ConsentCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Register a new consent record."""
    try:
        company_uuid = UUID(company_id)
        candidate_uuid = UUID(data.candidate_id)
        consent = await repo.create_consent({
            "company_id": company_uuid,
            "candidate_id": candidate_uuid,
            "consent_type": data.consent_type,
            "version": data.version,
            "granted_at": datetime.utcnow(),
            "expires_at": data.expires_at,
            "ip_address": data.ip_address,
            "source": data.source,
            "legal_basis": data.legal_basis,
            "consent_text": data.consent_text,
            "is_active": True,
        })
        logger.info(f"Created consent record: {consent.id} for candidate {candidate_uuid}")
        return ConsentRecordResponse(**consent.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating consent record: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/consents/{consent_id}/revoke", response_model=ConsentRecordResponse, summary="Revoke consent")
async def revoke_consent(
    consent_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ConsentRevoke,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Revoke an existing consent record."""
    try:
        company_uuid = UUID(company_id)
        consent_uuid = UUID(consent_id)
        consent = await repo.get_consent(consent_uuid, company_uuid)
        if not consent:
            log_cross_tenant_attempt(consent_id, company_id, "ConsentRecord")
            raise HTTPException(status_code=404, detail="Consent record not found")
        consent = await repo.revoke_consent(consent)
        logger.info(f"Revoked consent: {consent_id} for company {company_id}")
        return ConsentRecordResponse(**consent.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking consent: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/incidents", response_model=IncidentReportListResponse, summary="List incidents")
async def list_incidents(
    incident_type: str | None = Query(None, description="Filter by incident type"),
    severity: str | None = Query(None, description="Filter by severity"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List incident reports with optional filters."""
    try:
        company_uuid = UUID(company_id)
        incidents, total = await repo.list_incidents(
            company_uuid=company_uuid,
            incident_type=incident_type,
            severity=severity,
            status_filter=status_filter,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return IncidentReportListResponse(
            incidents=[IncidentReportResponse(**i.to_dict()) for i in incidents],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing incidents: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/incidents", response_model=IncidentReportResponse, status_code=status.HTTP_201_CREATED, summary="Create incident")
async def create_incident(
    data: IncidentCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new incident report."""
    try:
        company_uuid = UUID(company_id)
        incident = await repo.create_incident({
            "company_id": company_uuid,
            "incident_type": data.incident_type,
            "severity": data.severity,
            "description": data.description,
            "affected_resources": data.affected_resources or [],
            "detected_at": data.detected_at or datetime.utcnow(),
            "status": "open",
        })
        logger.info(f"Created incident: {incident.id} - {data.incident_type}")
        return IncidentReportResponse(**incident.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating incident: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/incidents/{incident_id}", response_model=IncidentReportResponse, summary="Update incident")
async def update_incident(
    incident_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: IncidentUpdate,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing incident report."""
    try:
        company_uuid = UUID(company_id)
        incident_uuid = UUID(incident_id)
        incident = await repo.get_incident(incident_uuid, company_uuid)
        if not incident:
            log_cross_tenant_attempt(incident_id, company_id, "IncidentReport")
            raise HTTPException(status_code=404, detail="Incident not found")

        update_data = {}
        if data.severity is not None:
            update_data["severity"] = data.severity
        if data.description is not None:
            update_data["description"] = data.description
        if data.root_cause is not None:
            update_data["root_cause"] = data.root_cause
        if data.remediation_actions is not None:
            update_data["remediation_actions"] = data.remediation_actions
        if data.notified_parties is not None:
            update_data["notified_parties"] = data.notified_parties
        if data.status is not None:
            update_data["status"] = data.status
        if data.assigned_to is not None:
            update_data["assigned_to"] = UUID(data.assigned_to)

        incident = await repo.update_incident(incident, update_data)
        logger.info(f"Updated incident: {incident_id}")
        return IncidentReportResponse(**incident.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating incident: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/incidents/{incident_id}/resolve", response_model=IncidentReportResponse, summary="Resolve incident")
async def resolve_incident(
    incident_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: IncidentResolve,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Mark an incident as resolved."""
    try:
        company_uuid = UUID(company_id)
        incident_uuid = UUID(incident_id)
        incident = await repo.get_incident(incident_uuid, company_uuid)
        if not incident:
            log_cross_tenant_attempt(incident_id, company_id, "IncidentReport")
            raise HTTPException(status_code=404, detail="Incident not found")

        update_data: dict = {
            "status": "resolved",
            "resolved_at": datetime.utcnow(),
        }
        if data.root_cause:
            update_data["root_cause"] = data.root_cause
        if data.remediation_actions:
            update_data["remediation_actions"] = data.remediation_actions

        incident = await repo.update_incident(incident, update_data)
        logger.info(f"Resolved incident: {incident_id}")
        return IncidentReportResponse(**incident.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving incident: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/evaluations/summary", response_model=ModelEvaluationSummaryResponse, summary="Get evaluation summary")
async def get_evaluation_summary(
    model_version: str | None = Query(None, description="Filter by model version"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get summary of model evaluations by dimension."""
    try:
        company_uuid = UUID(company_id)
        summary = await repo.get_evaluation_summary(company_uuid, model_version)
        total = summary["total"]
        passed_count = summary["passed_count"]
        return ModelEvaluationSummaryResponse(
            total_evaluations=total,
            by_dimension=summary["by_dimension"],
            by_evaluation_type=summary["by_type"],
            pass_rate=round(passed_count / total * 100, 2) if total > 0 else 0,
            latest_evaluation_date=summary["latest_date"]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evaluation summary: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/evaluations", response_model=ModelEvaluationListResponse, summary="List model evaluations")
async def list_model_evaluations(
    model_version: str | None = Query(None, description="Filter by model version"),
    evaluation_type: str | None = Query(None, description="Filter by evaluation type"),
    dimension: str | None = Query(None, description="Filter by dimension"),
    passed: bool | None = Query(None, description="Filter by pass status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List model evaluations with optional filters."""
    try:
        company_uuid = UUID(company_id)
        evaluations, total = await repo.list_model_evaluations(
            company_uuid=company_uuid,
            model_version=model_version,
            evaluation_type=evaluation_type,
            dimension=dimension,
            passed=passed,
            limit=limit,
            offset=offset,
        )
        return ModelEvaluationListResponse(
            evaluations=[ModelEvaluationResponse(**e.to_dict()) for e in evaluations],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing model evaluations: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/compliance/summary", response_model=ComplianceSummaryResponse, summary="Get compliance summary")
async def get_compliance_summary(
    framework: str | None = Query(None, description="Filter by framework"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get summary of compliance controls by framework."""
    try:
        company_uuid = UUID(company_id)
        summary = await repo.get_compliance_summary(company_uuid, framework)
        return ComplianceSummaryResponse(
            total_controls=summary["total"],
            by_framework=summary["by_framework"],
            by_status=summary["by_status"],
            overdue_reviews=summary["overdue"],
            upcoming_reviews=summary["upcoming"]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/compliance", response_model=ComplianceControlListResponse, summary="List compliance controls")
async def list_compliance_controls(
    framework: str | None = Query(None, description="Filter by framework"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    risk_level: str | None = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List compliance controls with optional filters."""
    try:
        company_uuid = UUID(company_id)
        controls, total = await repo.list_compliance_controls(
            company_uuid=company_uuid,
            framework=framework,
            status_filter=status_filter,
            risk_level=risk_level,
            limit=limit,
            offset=offset,
        )
        return ComplianceControlListResponse(
            controls=[ComplianceControlResponse(**c.to_dict()) for c in controls],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing compliance controls: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/compliance/{control_id}", response_model=ComplianceControlResponse, summary="Update compliance control")
async def update_compliance_control(
    control_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: ComplianceControlUpdate,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a compliance control."""
    try:
        company_uuid = UUID(company_id)
        control_uuid = UUID(control_id)
        control = await repo.get_compliance_control(control_uuid, company_uuid)
        if not control:
            log_cross_tenant_attempt(control_id, company_id, "ComplianceControl")
            raise HTTPException(status_code=404, detail="Compliance control not found")

        update_data = {}
        if data.status is not None:
            update_data["status"] = data.status
        if data.evidence_url is not None:
            update_data["evidence_url"] = data.evidence_url
        if data.evidence_notes is not None:
            update_data["evidence_notes"] = data.evidence_notes
        if data.owner is not None:
            update_data["owner"] = data.owner
        if data.owner_email is not None:
            update_data["owner_email"] = data.owner_email
        if data.next_review_at is not None:
            update_data["next_review_at"] = data.next_review_at

        control = await repo.update_compliance_control(control, update_data)
        logger.info(f"Updated compliance control: {control_id}")
        return ComplianceControlResponse(**control.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating compliance control: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/dashboard", response_model=ObservabilityDashboardResponse, summary="Get dashboard data")
async def get_observability_dashboard(
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get consolidated dashboard data for observability."""
    try:
        company_uuid = UUID(company_id)
        start_date = datetime.utcnow() - timedelta(days=period_days)

        data = await repo.get_dashboard_data(company_uuid, start_date)

        ai_total = data["ai_total"]
        data_access_total = data["data_access_total"]
        active_consents = data["active_consents"]
        open_incidents = data["open_incidents"]
        critical_incidents = data["critical_incidents"]
        eval_count = data["eval_count"]
        passed_count = data["passed_count"]
        compliance_total = data["compliance_total"]
        implemented = data["implemented"]

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/bias-audits/latest", response_model=BiasAuditReportResponse, summary="Get latest bias audit")
async def get_latest_bias_audit(
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get the most recent bias audit report for the company."""
    try:
        company_uuid = UUID(company_id)
        audit = await repo.get_latest_bias_audit(company_uuid)
        if not audit:
            raise HTTPException(status_code=404, detail="No bias audit found for this company")
        return BiasAuditReportResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest bias audit: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/bias-audits/summary", response_model=BiasAuditSummaryResponse, summary="Get bias audit summary")
async def get_bias_audit_summary(
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a summary of all bias audits for the company."""
    try:
        company_uuid = UUID(company_id)
        summary = await repo.get_bias_audit_summary(company_uuid)
        latest_audit = summary["latest_audit"]
        status_counts = {"clear": 0, "consider": 0, "concern": 0}
        if latest_audit:
            status_counts["clear"] = latest_audit.clear_count or 0
            status_counts["consider"] = latest_audit.consider_count or 0
            status_counts["concern"] = latest_audit.concern_count or 0

        return BiasAuditSummaryResponse(
            total_audits=summary["total"],
            latest_audit_date=latest_audit.audit_date if latest_audit else None,
            latest_overall_score=float(latest_audit.overall_score) if latest_audit and latest_audit.overall_score else None,
            by_audit_type=summary["by_audit_type"],
            by_status=status_counts,
            compliance_coverage=list(summary["all_frameworks"]),
            public_audits_count=summary["public_count"]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bias audit summary: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/bias-audits", response_model=BiasAuditReportListResponse, summary="List bias audits")
async def list_bias_audits(
    audit_type: str | None = Query(None, description="Filter by audit type"),
    is_public: bool | None = Query(None, description="Filter by public status"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List bias audit reports with optional filters."""
    try:
        company_uuid = UUID(company_id)
        audits, total = await repo.list_bias_audits(
            company_uuid=company_uuid,
            audit_type=audit_type,
            is_public=is_public,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return BiasAuditReportListResponse(
            audits=[BiasAuditReportResponse(**audit.to_dict()) for audit in audits],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing bias audits: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/bias-audits/{audit_id}", response_model=BiasAuditReportResponse, summary="Get bias audit by ID")
async def get_bias_audit(
    audit_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific bias audit report by ID."""
    try:
        company_uuid = UUID(company_id)
        audit_uuid = UUID(audit_id)
        audit = await repo.get_bias_audit(audit_uuid, company_uuid)
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
        raise LIAError(message="Erro interno do servidor")


@router.post("/bias-audits", response_model=BiasAuditReportResponse, status_code=status.HTTP_201_CREATED, summary="Create bias audit")
async def create_bias_audit(
    data: BiasAuditCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

        audit = await repo.create_bias_audit({
            "company_id": company_uuid,
            "audit_type": data.audit_type,
            "audit_date": data.audit_date,
            "sample_size": data.sample_size,
            "auditor": data.auditor,
            "auditor_name": data.auditor_name,
            "auditor_organization": data.auditor_organization,
            "bias_results": data.bias_results,
            "overall_score": data.overall_score,
            "clear_count": clear_count,
            "consider_count": consider_count,
            "concern_count": concern_count,
            "compliance_frameworks": data.compliance_frameworks or [],
            "report_url": data.report_url,
            "notes": data.notes,
            "recommendations": data.recommendations or [],
            "is_public": False,
        })

        logger.info(f"Created bias audit report: {audit.id} for company {company_uuid}")
        return BiasAuditReportResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bias audit: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/bias-audits/{audit_id}/publish", response_model=BiasAuditReportResponse, summary="Publish bias audit")
async def publish_bias_audit(
    audit_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: BiasAuditPublish,
    company_id: str = Depends(get_verified_company_id),
    repo: ObservabilityRepository = Depends(get_observability_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Publish or unpublish a bias audit report."""
    try:
        company_uuid = UUID(company_id)
        audit_uuid = UUID(audit_id)
        audit = await repo.get_bias_audit(audit_uuid, company_uuid)
        if not audit:
            log_cross_tenant_attempt(audit_id, company_id, "BiasAuditReport")
            raise HTTPException(status_code=404, detail="Bias audit report not found")

        update_data: dict = {"is_public": data.is_public}
        if data.report_url:
            update_data["report_url"] = data.report_url

        audit = await repo.update_bias_audit(audit, update_data)

        action = "published" if data.is_public else "unpublished"
        logger.info(f"Bias audit {audit_id} {action} for company {company_id}")
        return BiasAuditReportResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing bias audit: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
