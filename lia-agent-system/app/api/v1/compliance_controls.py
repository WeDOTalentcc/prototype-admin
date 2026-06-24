"""
Compliance Controls API Endpoints.

Provides endpoints for:
- Control Library Management (ISO 27001, SOC 2, SOX, etc.)
- Company Compliance Controls
- Compliance Audits
- SOX Controls
- Compliance Dashboard
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.dependencies import get_compliance_repo
from app.repositories.compliance_controls_repository import (
    ComplianceControlsRepository,
)
from app.models.observability import ComplianceControlLibrary
from app.schemas.compliance_controls import (
    CompanyControlCreate,
    CompanyControlListResponse,
    CompanyControlResponse,
    CompanyControlUpdate,
    ComplianceAuditCreate,
    ComplianceAuditListResponse,
    ComplianceAuditResponse,
    ComplianceDashboardResponse,
    ControlLibraryCreate,
    ControlLibraryListResponse,
    ControlLibraryResponse,
    EvidenceUpload,
    FrameworkStats,
    SeedDataResponse,
    SOXControlCreate,
    SOXControlListResponse,
    SOXControlResponse,
    SOXControlUpdate,
)
from app.shared.tenant_guard import get_verified_company_id
from app.schemas.envelope import ResponseEnvelope, ok_envelope
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance-controls"])


@router.get("/controls", response_model=ControlLibraryListResponse, summary="List control library entries")
async def list_control_library(
    framework: str | None = Query(None, description="Filter by framework"),
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search in name/description"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all controls in the library, optionally filtered by framework."""
    try:
        controls, total = await repo.list_control_library(
            framework=framework,
            category=category,
            search=search,
            limit=limit,
            offset=offset,
        )
        return ControlLibraryListResponse(
            controls=[ControlLibraryResponse(**c.to_dict()) for c in controls],
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing control library: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/controls", response_model=ControlLibraryResponse, summary="Create control library entry")
async def create_control_library(
    data: ControlLibraryCreate,
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new control in the library."""
    try:
        control = await repo.create_control_library(
            framework=data.framework,
            control_id=data.control_id,
            control_name=data.control_name,
            control_description=data.control_description,
            control_category=data.control_category,
            domain=data.domain,
            is_mandatory=data.is_mandatory,
            implementation_guidance=data.implementation_guidance,
            evidence_requirements=data.evidence_requirements or [],
            related_controls=data.related_controls or [],
        )
        return ControlLibraryResponse(**control.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating control library entry: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/controls/{framework}", response_model=ControlLibraryListResponse, summary="Get controls by framework")
async def get_controls_by_framework(
    framework: str,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all controls for a specific framework."""
    try:
        controls, total = await repo.get_controls_by_framework(
            framework=framework,
            limit=limit,
            offset=offset,
        )
        return ControlLibraryListResponse(
            controls=[ControlLibraryResponse(**c.to_dict()) for c in controls],
            total=total,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting controls by framework: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/company-controls", response_model=CompanyControlListResponse, summary="List company controls")
async def list_company_controls(
    framework: str | None = Query(None, description="Filter by framework"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List company's compliance controls with their status."""
    try:
        company_uuid = UUID(company_id)
        controls, total = await repo.list_company_controls(
            company_uuid=company_uuid,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )

        responses = []
        for ctrl in controls:
            ctrl_dict = ctrl.to_dict()
            lib_control = await repo.get_control_library_item(ctrl.control_library_id)
            if lib_control:
                ctrl_dict["control"] = lib_control.to_dict()
            responses.append(CompanyControlResponse(**ctrl_dict))

        return CompanyControlListResponse(
            controls=responses,
            total=total,
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing company controls: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/company-controls", response_model=CompanyControlResponse, summary="Create company control")
async def create_company_control(
    data: CompanyControlCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a company compliance control mapping."""
    try:
        company_uuid = UUID(company_id)

        lib_control = await repo.get_control_library_item(UUID(data.control_library_id))
        if not lib_control:
            raise HTTPException(status_code=404, detail="Control library entry not found")

        control = await repo.create_company_control(
            company_uuid=company_uuid,
            control_library_id=UUID(data.control_library_id),
            status=data.status or "not_started",
            owner_name=data.owner_name,
            owner_email=data.owner_email,
            notes=data.notes,
        )

        ctrl_dict = control.to_dict()
        ctrl_dict["control"] = lib_control.to_dict()
        return CompanyControlResponse(**ctrl_dict)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating company control: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/company-controls/{control_id}", response_model=CompanyControlResponse, summary="Update company control")
async def update_company_control(
    control_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: CompanyControlUpdate,
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a company's compliance control status."""
    try:
        company_uuid = UUID(company_id)
        control_uuid = UUID(control_id)

        control = await repo.get_company_control(control_uuid, company_uuid)
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")

        update_data = data.model_dump(exclude_unset=True)
        control = await repo.update_company_control(control, update_data)

        lib_control = await repo.get_control_library_item(control.control_library_id)

        ctrl_dict = control.to_dict()
        if lib_control:
            ctrl_dict["control"] = lib_control.to_dict()

        return CompanyControlResponse(**ctrl_dict)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error updating company control: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/company-controls/{control_id}/evidence", response_model=CompanyControlResponse, summary="Upload evidence")
async def upload_evidence(
    control_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: EvidenceUpload,
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Upload evidence file for a control."""
    try:
        company_uuid = UUID(company_id)
        control_uuid = UUID(control_id)

        control = await repo.get_company_control(control_uuid, company_uuid)
        if not control:
            raise HTTPException(status_code=404, detail="Control not found")

        evidence_files = control.evidence_files or []
        evidence_files.append({
            "filename": data.filename,
            "url": data.url,
            "uploaded_at": datetime.utcnow().isoformat(),
        })

        control = await repo.update_company_control_evidence(control, evidence_files)
        return CompanyControlResponse(**control.to_dict())
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error uploading evidence: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/audits", response_model=ComplianceAuditListResponse, summary="List compliance audits")
async def list_audits(
    framework: str | None = Query(None, description="Filter by framework"),
    audit_type: str | None = Query(None, description="Filter by audit type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List compliance audits."""
    try:
        company_uuid = UUID(company_id)
        audits, total = await repo.list_audits(
            company_uuid=company_uuid,
            framework=framework,
            audit_type=audit_type,
            limit=limit,
            offset=offset,
        )
        return ComplianceAuditListResponse(
            audits=[ComplianceAuditResponse(**a.to_dict()) for a in audits],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing audits: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/audits", response_model=ComplianceAuditResponse, summary="Create compliance audit")
async def create_audit(
    data: ComplianceAuditCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new compliance audit."""
    try:
        company_uuid = UUID(company_id)
        audit = await repo.create_audit(
            company_uuid=company_uuid,
            framework=data.framework,
            audit_type=data.audit_type,
            auditor_organization=data.auditor_organization,
            auditor_name=data.auditor_name,
            audit_start_date=data.audit_start_date,
            audit_end_date=data.audit_end_date,
            scope_description=data.scope_description,
        )
        return ComplianceAuditResponse(**audit.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating audit: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/audits/dashboard", response_model=ResponseEnvelope[ComplianceDashboardResponse], summary="Get compliance dashboard")
async def get_compliance_dashboard(
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get comprehensive compliance dashboard across all frameworks."""
    try:
        company_uuid = UUID(company_id)

        controls, upcoming_reviews, overdue_reviews, recent_audits, sox_summary = (
            await repo.get_compliance_dashboard_stats(company_uuid)
        )

        by_framework = {}
        total_controls = 0
        total_implemented = 0

        for company_ctrl, lib_ctrl in controls:
            fw = lib_ctrl.framework
            if fw not in by_framework:
                by_framework[fw] = FrameworkStats()

            by_framework[fw].total_controls += 1
            total_controls += 1

            status = company_ctrl.status
            if status == "implemented":
                by_framework[fw].implemented += 1
                total_implemented += 1
            elif status == "in_progress":
                by_framework[fw].in_progress += 1
            elif status == "not_started":
                by_framework[fw].not_started += 1
            elif status == "verified":
                by_framework[fw].verified += 1
                total_implemented += 1
            elif status == "not_applicable":
                by_framework[fw].not_applicable += 1

        for fw in by_framework:
            applicable = by_framework[fw].total_controls - by_framework[fw].not_applicable
            if applicable > 0:
                implemented = by_framework[fw].implemented + by_framework[fw].verified
                by_framework[fw].compliance_percentage = round(implemented / applicable * 100, 1)

        recent_audit_responses = [
            ComplianceAuditResponse(**a.to_dict()) for a in recent_audits
        ]

        applicable_total = total_controls - sum(s.not_applicable for s in by_framework.values())
        overall_pct = round(total_implemented / applicable_total * 100, 1) if applicable_total > 0 else 0.0

        return ok_envelope(ComplianceDashboardResponse(
            by_framework={k: v.model_dump() for k, v in by_framework.items()},
            total_controls=total_controls,
            total_implemented=total_implemented,
            overall_compliance_percentage=overall_pct,
            upcoming_reviews=upcoming_reviews,
            overdue_reviews=overdue_reviews,
            recent_audits=recent_audit_responses,
            sox_summary=sox_summary if sox_summary else None,
        ))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance dashboard: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/sox", response_model=SOXControlListResponse, summary="List SOX controls")
async def list_sox_controls(
    section: str | None = Query(None, description="Filter by SOX section"),
    test_result: str | None = Query(None, description="Filter by test result"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List SOX controls for a company."""
    try:
        company_uuid = UUID(company_id)
        controls, total = await repo.list_sox_controls(
            company_uuid=company_uuid,
            section=section,
            test_result=test_result,
            limit=limit,
            offset=offset,
        )
        return SOXControlListResponse(
            controls=[SOXControlResponse(**c.to_dict()) for c in controls],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing SOX controls: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/sox", response_model=SOXControlResponse, summary="Create SOX control")
async def create_sox_control(
    data: SOXControlCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new SOX control."""
    try:
        company_uuid = UUID(company_id)
        control = await repo.create_sox_control(
            company_uuid=company_uuid,
            section=data.section,
            control_id=data.control_id,
            control_name=data.control_name,
            control_objective=data.control_objective,
            key_control=data.key_control,
            frequency=data.frequency,
            control_owner=data.control_owner,
        )
        return SOXControlResponse(**control.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating SOX control: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.put("/sox/{control_id}", response_model=SOXControlResponse, summary="Update SOX control")
async def update_sox_control(
    control_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: SOXControlUpdate,
    company_id: str = Depends(get_verified_company_id),
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a SOX control."""
    try:
        company_uuid = UUID(company_id)
        control_uuid = UUID(control_id)

        control = await repo.get_sox_control(control_uuid, company_uuid)
        if not control:
            raise HTTPException(status_code=404, detail="SOX control not found")

        update_data = data.model_dump(exclude_unset=True)
        control = await repo.update_sox_control(control, update_data)
        return SOXControlResponse(**control.to_dict())
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error updating SOX control: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/seed", response_model=SeedDataResponse, summary="Seed control library data")
async def seed_control_library(
    repo: ComplianceControlsRepository = Depends(get_compliance_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Seed the control library with ISO 27001, SOC 2 TSC, and SOX controls."""
    try:
        iso_27001_controls = [
            {"control_id": "A.5.1", "control_name": "Policies for information security", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.2", "control_name": "Information security roles and responsibilities", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.3", "control_name": "Segregation of duties", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.4", "control_name": "Management responsibilities", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.5", "control_name": "Contact with authorities", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.6", "control_name": "Contact with special interest groups", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.7", "control_name": "Threat intelligence", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.8", "control_name": "Information security in project management", "control_category": "Information Security Policies", "domain": "Organizational Controls"},
            {"control_id": "A.5.9", "control_name": "Inventory of information and other associated assets", "control_category": "Asset Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.10", "control_name": "Acceptable use of information and other associated assets", "control_category": "Asset Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.11", "control_name": "Return of assets", "control_category": "Asset Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.12", "control_name": "Classification of information", "control_category": "Information Classification", "domain": "Organizational Controls"},
            {"control_id": "A.5.13", "control_name": "Labelling of information", "control_category": "Information Classification", "domain": "Organizational Controls"},
            {"control_id": "A.5.14", "control_name": "Information transfer", "control_category": "Information Classification", "domain": "Organizational Controls"},
            {"control_id": "A.5.15", "control_name": "Access control", "control_category": "Access Control", "domain": "Organizational Controls"},
            {"control_id": "A.5.16", "control_name": "Identity management", "control_category": "Access Control", "domain": "Organizational Controls"},
            {"control_id": "A.5.17", "control_name": "Authentication information", "control_category": "Access Control", "domain": "Organizational Controls"},
            {"control_id": "A.5.18", "control_name": "Access rights", "control_category": "Access Control", "domain": "Organizational Controls"},
            {"control_id": "A.5.19", "control_name": "Information security in supplier relationships", "control_category": "Supplier Relationships", "domain": "Organizational Controls"},
            {"control_id": "A.5.20", "control_name": "Addressing information security within supplier agreements", "control_category": "Supplier Relationships", "domain": "Organizational Controls"},
            {"control_id": "A.5.21", "control_name": "Managing information security in the ICT supply chain", "control_category": "Supplier Relationships", "domain": "Organizational Controls"},
            {"control_id": "A.5.22", "control_name": "Monitoring, review and change management of supplier services", "control_category": "Supplier Relationships", "domain": "Organizational Controls"},
            {"control_id": "A.5.23", "control_name": "Information security for use of cloud services", "control_category": "Cloud Security", "domain": "Organizational Controls"},
            {"control_id": "A.5.24", "control_name": "Information security incident management planning and preparation", "control_category": "Incident Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.25", "control_name": "Assessment and decision on information security events", "control_category": "Incident Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.26", "control_name": "Response to information security incidents", "control_category": "Incident Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.27", "control_name": "Learning from information security incidents", "control_category": "Incident Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.28", "control_name": "Collection of evidence", "control_category": "Incident Management", "domain": "Organizational Controls"},
            {"control_id": "A.5.29", "control_name": "Information security during disruption", "control_category": "Business Continuity", "domain": "Organizational Controls"},
            {"control_id": "A.5.30", "control_name": "ICT readiness for business continuity", "control_category": "Business Continuity", "domain": "Organizational Controls"},
            {"control_id": "A.5.31", "control_name": "Legal, statutory, regulatory and contractual requirements", "control_category": "Compliance", "domain": "Organizational Controls"},
            {"control_id": "A.5.32", "control_name": "Intellectual property rights", "control_category": "Compliance", "domain": "Organizational Controls"},
            {"control_id": "A.5.33", "control_name": "Protection of records", "control_category": "Compliance", "domain": "Organizational Controls"},
            {"control_id": "A.5.34", "control_name": "Privacy and protection of PII", "control_category": "Privacy", "domain": "Organizational Controls"},
            {"control_id": "A.5.35", "control_name": "Independent review of information security", "control_category": "Compliance", "domain": "Organizational Controls"},
            {"control_id": "A.5.36", "control_name": "Compliance with policies, rules and standards for information security", "control_category": "Compliance", "domain": "Organizational Controls"},
            {"control_id": "A.5.37", "control_name": "Documented operating procedures", "control_category": "Operations Security", "domain": "Organizational Controls"},
            {"control_id": "A.6.1", "control_name": "Screening", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.6.2", "control_name": "Terms and conditions of employment", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.6.3", "control_name": "Information security awareness, education and training", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.6.4", "control_name": "Disciplinary process", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.6.5", "control_name": "Responsibilities after termination or change of employment", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.6.6", "control_name": "Confidentiality or non-disclosure agreements", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.6.7", "control_name": "Remote working", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.6.8", "control_name": "Information security event reporting", "control_category": "People Security", "domain": "People Controls"},
            {"control_id": "A.7.1", "control_name": "Physical security perimeters", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.2", "control_name": "Physical entry", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.3", "control_name": "Securing offices, rooms and facilities", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.4", "control_name": "Physical security monitoring", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.5", "control_name": "Protecting against physical and environmental threats", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.6", "control_name": "Working in secure areas", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.7", "control_name": "Clear desk and clear screen", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.8", "control_name": "Equipment siting and protection", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.9", "control_name": "Security of assets off-premises", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.10", "control_name": "Storage media", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.11", "control_name": "Supporting utilities", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.12", "control_name": "Cabling security", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.13", "control_name": "Equipment maintenance", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.7.14", "control_name": "Secure disposal or re-use of equipment", "control_category": "Physical Security", "domain": "Physical Controls"},
            {"control_id": "A.8.1", "control_name": "User endpoint devices", "control_category": "Technology Controls", "domain": "Technological Controls"},
            {"control_id": "A.8.2", "control_name": "Privileged access rights", "control_category": "Access Control", "domain": "Technological Controls"},
            {"control_id": "A.8.3", "control_name": "Information access restriction", "control_category": "Access Control", "domain": "Technological Controls"},
            {"control_id": "A.8.4", "control_name": "Access to source code", "control_category": "Access Control", "domain": "Technological Controls"},
            {"control_id": "A.8.5", "control_name": "Secure authentication", "control_category": "Access Control", "domain": "Technological Controls"},
            {"control_id": "A.8.6", "control_name": "Capacity management", "control_category": "Operations Security", "domain": "Technological Controls"},
            {"control_id": "A.8.7", "control_name": "Protection against malware", "control_category": "Operations Security", "domain": "Technological Controls"},
            {"control_id": "A.8.8", "control_name": "Management of technical vulnerabilities", "control_category": "Operations Security", "domain": "Technological Controls"},
            {"control_id": "A.8.9", "control_name": "Configuration management", "control_category": "Operations Security", "domain": "Technological Controls"},
            {"control_id": "A.8.10", "control_name": "Information deletion", "control_category": "Data Protection", "domain": "Technological Controls"},
            {"control_id": "A.8.11", "control_name": "Data masking", "control_category": "Data Protection", "domain": "Technological Controls"},
            {"control_id": "A.8.12", "control_name": "Data leakage prevention", "control_category": "Data Protection", "domain": "Technological Controls"},
            {"control_id": "A.8.13", "control_name": "Information backup", "control_category": "Data Protection", "domain": "Technological Controls"},
            {"control_id": "A.8.14", "control_name": "Redundancy of information processing facilities", "control_category": "Business Continuity", "domain": "Technological Controls"},
            {"control_id": "A.8.15", "control_name": "Logging", "control_category": "Monitoring", "domain": "Technological Controls"},
            {"control_id": "A.8.16", "control_name": "Monitoring activities", "control_category": "Monitoring", "domain": "Technological Controls"},
            {"control_id": "A.8.17", "control_name": "Clock synchronization", "control_category": "Monitoring", "domain": "Technological Controls"},
            {"control_id": "A.8.18", "control_name": "Use of privileged utility programs", "control_category": "Operations Security", "domain": "Technological Controls"},
            {"control_id": "A.8.19", "control_name": "Installation of software on operational systems", "control_category": "Operations Security", "domain": "Technological Controls"},
            {"control_id": "A.8.20", "control_name": "Networks security", "control_category": "Network Security", "domain": "Technological Controls"},
            {"control_id": "A.8.21", "control_name": "Security of network services", "control_category": "Network Security", "domain": "Technological Controls"},
            {"control_id": "A.8.22", "control_name": "Segregation of networks", "control_category": "Network Security", "domain": "Technological Controls"},
            {"control_id": "A.8.23", "control_name": "Web filtering", "control_category": "Network Security", "domain": "Technological Controls"},
            {"control_id": "A.8.24", "control_name": "Use of cryptography", "control_category": "Cryptography", "domain": "Technological Controls"},
            {"control_id": "A.8.25", "control_name": "Secure development life cycle", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.26", "control_name": "Application security requirements", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.27", "control_name": "Secure system architecture and engineering principles", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.28", "control_name": "Secure coding", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.29", "control_name": "Security testing in development and acceptance", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.30", "control_name": "Outsourced development", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.31", "control_name": "Separation of development, test and production environments", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.32", "control_name": "Change management", "control_category": "Change Management", "domain": "Technological Controls"},
            {"control_id": "A.8.33", "control_name": "Test information", "control_category": "Development Security", "domain": "Technological Controls"},
            {"control_id": "A.8.34", "control_name": "Protection of information systems during audit testing", "control_category": "Audit", "domain": "Technological Controls"},
        ]

        soc2_controls = [
            {"control_id": "CC1.1", "control_name": "COSO Principle 1: Demonstrates Commitment to Integrity and Ethical Values", "control_category": "Control Environment", "domain": "Common Criteria"},
            {"control_id": "CC1.2", "control_name": "COSO Principle 2: Board Exercises Oversight Responsibility", "control_category": "Control Environment", "domain": "Common Criteria"},
            {"control_id": "CC1.3", "control_name": "COSO Principle 3: Establishes Structure, Authority, and Responsibility", "control_category": "Control Environment", "domain": "Common Criteria"},
            {"control_id": "CC1.4", "control_name": "COSO Principle 4: Demonstrates Commitment to Competence", "control_category": "Control Environment", "domain": "Common Criteria"},
            {"control_id": "CC1.5", "control_name": "COSO Principle 5: Enforces Accountability", "control_category": "Control Environment", "domain": "Common Criteria"},
            {"control_id": "CC2.1", "control_name": "COSO Principle 13: Obtains or Generates and Uses Relevant, Quality Information", "control_category": "Communication and Information", "domain": "Common Criteria"},
            {"control_id": "CC2.2", "control_name": "COSO Principle 14: Internally Communicates Information", "control_category": "Communication and Information", "domain": "Common Criteria"},
            {"control_id": "CC2.3", "control_name": "COSO Principle 15: Communicates With External Parties", "control_category": "Communication and Information", "domain": "Common Criteria"},
            {"control_id": "CC3.1", "control_name": "COSO Principle 6: Specifies Suitable Objectives", "control_category": "Risk Assessment", "domain": "Common Criteria"},
            {"control_id": "CC3.2", "control_name": "COSO Principle 7: Identifies and Analyzes Risk", "control_category": "Risk Assessment", "domain": "Common Criteria"},
            {"control_id": "CC3.3", "control_name": "COSO Principle 8: Assesses Fraud Risk", "control_category": "Risk Assessment", "domain": "Common Criteria"},
            {"control_id": "CC3.4", "control_name": "COSO Principle 9: Identifies and Analyzes Significant Change", "control_category": "Risk Assessment", "domain": "Common Criteria"},
            {"control_id": "CC4.1", "control_name": "COSO Principle 16: Selects, Develops, and Performs Ongoing and/or Separate Evaluations", "control_category": "Monitoring Activities", "domain": "Common Criteria"},
            {"control_id": "CC4.2", "control_name": "COSO Principle 17: Evaluates and Communicates Deficiencies", "control_category": "Monitoring Activities", "domain": "Common Criteria"},
            {"control_id": "CC5.1", "control_name": "COSO Principle 10: Selects and Develops Control Activities", "control_category": "Control Activities", "domain": "Common Criteria"},
            {"control_id": "CC5.2", "control_name": "COSO Principle 11: Selects and Develops General Controls Over Technology", "control_category": "Control Activities", "domain": "Common Criteria"},
            {"control_id": "CC5.3", "control_name": "COSO Principle 12: Deploys Through Policies and Procedures", "control_category": "Control Activities", "domain": "Common Criteria"},
            {"control_id": "CC6.1", "control_name": "Logical and Physical Access Controls", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC6.2", "control_name": "Prior to Issuing System Credentials and Granting System Access", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC6.3", "control_name": "Based on Authorization, Removes Access to Protected Information Assets", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC6.4", "control_name": "Restricts Physical Access", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC6.5", "control_name": "Disposes of Protected Information Assets", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC6.6", "control_name": "Logical Access Security Measures Against Threats", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC6.7", "control_name": "Transmission of Data is Restricted to Authorized Users", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC6.8", "control_name": "Controls Against Malicious Software", "control_category": "Logical and Physical Access Controls", "domain": "Common Criteria"},
            {"control_id": "CC7.1", "control_name": "Detection and Monitoring Procedures", "control_category": "System Operations", "domain": "Common Criteria"},
            {"control_id": "CC7.2", "control_name": "Monitors System Components for Anomalies", "control_category": "System Operations", "domain": "Common Criteria"},
            {"control_id": "CC7.3", "control_name": "Evaluates Security Events", "control_category": "System Operations", "domain": "Common Criteria"},
            {"control_id": "CC7.4", "control_name": "Responds to Identified Security Incidents", "control_category": "System Operations", "domain": "Common Criteria"},
            {"control_id": "CC7.5", "control_name": "Recovers from Identified Security Incidents", "control_category": "System Operations", "domain": "Common Criteria"},
            {"control_id": "CC8.1", "control_name": "Changes to Infrastructure, Data, and Software", "control_category": "Change Management", "domain": "Common Criteria"},
            {"control_id": "CC9.1", "control_name": "Identifies and Mitigates Risks Related to Vendors and Business Partners", "control_category": "Risk Mitigation", "domain": "Common Criteria"},
            {"control_id": "CC9.2", "control_name": "Manages Risks Associated with Vendors and Business Partners", "control_category": "Risk Mitigation", "domain": "Common Criteria"},
            {"control_id": "A1.1", "control_name": "Availability: Maintains Processing Capacity", "control_category": "Availability", "domain": "Additional Criteria"},
            {"control_id": "A1.2", "control_name": "Availability: Environmental Protections", "control_category": "Availability", "domain": "Additional Criteria"},
            {"control_id": "A1.3", "control_name": "Availability: Recovery Processes", "control_category": "Availability", "domain": "Additional Criteria"},
            {"control_id": "C1.1", "control_name": "Confidentiality: Identifies and Maintains Confidential Information", "control_category": "Confidentiality", "domain": "Additional Criteria"},
            {"control_id": "C1.2", "control_name": "Confidentiality: Disposes of Confidential Information", "control_category": "Confidentiality", "domain": "Additional Criteria"},
            {"control_id": "PI1.1", "control_name": "Processing Integrity: Obtains or Generates Data", "control_category": "Processing Integrity", "domain": "Additional Criteria"},
            {"control_id": "PI1.2", "control_name": "Processing Integrity: Implements Policies and Procedures Over System Processing", "control_category": "Processing Integrity", "domain": "Additional Criteria"},
            {"control_id": "PI1.3", "control_name": "Processing Integrity: Implements Policies and Procedures for Error Detection and Correction", "control_category": "Processing Integrity", "domain": "Additional Criteria"},
            {"control_id": "PI1.4", "control_name": "Processing Integrity: Implements Policies and Procedures for Processing Outputs", "control_category": "Processing Integrity", "domain": "Additional Criteria"},
            {"control_id": "PI1.5", "control_name": "Processing Integrity: Stores Inputs, Items in Processing, and Outputs Completely and Accurately", "control_category": "Processing Integrity", "domain": "Additional Criteria"},
            {"control_id": "P1.1", "control_name": "Privacy: Privacy Notice", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P2.1", "control_name": "Privacy: Choice and Consent", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P3.1", "control_name": "Privacy: Collection", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P3.2", "control_name": "Privacy: Collection Limited to Purpose", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P4.1", "control_name": "Privacy: Uses Personal Information for Purpose Specified", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P4.2", "control_name": "Privacy: Retains Personal Information", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P4.3", "control_name": "Privacy: Disposes of Personal Information", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P5.1", "control_name": "Privacy: Access to Modify Personal Information", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P5.2", "control_name": "Privacy: Addresses Access Denials", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P6.1", "control_name": "Privacy: Discloses Personal Information to Third Parties", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P6.2", "control_name": "Privacy: Records Disclosures", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P6.3", "control_name": "Privacy: Creates Criteria for Third Party Disclosure", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P6.4", "control_name": "Privacy: Obtains Commitments from Third Parties", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P6.5", "control_name": "Privacy: Third Party Privacy Compliance", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P6.6", "control_name": "Privacy: Notifies Affected Parties of Unauthorized Disclosures", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P6.7", "control_name": "Privacy: Data Breach Notification", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P7.1", "control_name": "Privacy: Maintains Accurate Personal Information", "control_category": "Privacy", "domain": "Additional Criteria"},
            {"control_id": "P8.1", "control_name": "Privacy: Complaints Process", "control_category": "Privacy", "domain": "Additional Criteria"},
        ]

        sox_controls_seed = [
            {"section": "302", "control_id": "SOX-302-01", "control_name": "CEO/CFO Certification of Financial Statements", "control_objective": "Ensure executive certification of accuracy", "key_control": True, "frequency": "quarterly"},
            {"section": "302", "control_id": "SOX-302-02", "control_name": "Disclosure Controls and Procedures", "control_objective": "Maintain effective disclosure controls", "key_control": True, "frequency": "quarterly"},
            {"section": "302", "control_id": "SOX-302-03", "control_name": "Internal Controls Evaluation", "control_objective": "Evaluate internal controls effectiveness", "key_control": True, "frequency": "quarterly"},
            {"section": "302", "control_id": "SOX-302-04", "control_name": "Material Changes Disclosure", "control_objective": "Disclose material changes in internal controls", "key_control": True, "frequency": "quarterly"},
            {"section": "302", "control_id": "SOX-302-05", "control_name": "Fraud Disclosure Requirements", "control_objective": "Disclose any fraud involving management", "key_control": True, "frequency": "quarterly"},
            {"section": "404", "control_id": "SOX-404-01", "control_name": "Management Assessment of Internal Controls", "control_objective": "Annual assessment of ICFR effectiveness", "key_control": True, "frequency": "annual"},
            {"section": "404", "control_id": "SOX-404-02", "control_name": "External Auditor Attestation", "control_objective": "Independent auditor attestation on ICFR", "key_control": True, "frequency": "annual"},
            {"section": "404", "control_id": "SOX-404-03", "control_name": "Documentation of Internal Controls", "control_objective": "Maintain comprehensive control documentation", "key_control": True, "frequency": "annual"},
            {"section": "404", "control_id": "SOX-404-04", "control_name": "Control Testing Program", "control_objective": "Regular testing of key controls", "key_control": True, "frequency": "quarterly"},
            {"section": "404", "control_id": "SOX-404-05", "control_name": "Deficiency Remediation", "control_objective": "Timely remediation of control deficiencies", "key_control": True, "frequency": "monthly"},
            {"section": "404", "control_id": "SOX-404-HR-01", "control_name": "HR Master Data Controls", "control_objective": "Ensure accuracy of employee master data", "key_control": True, "frequency": "monthly"},
            {"section": "404", "control_id": "SOX-404-HR-02", "control_name": "Payroll Processing Controls", "control_objective": "Accurate and authorized payroll processing", "key_control": True, "frequency": "monthly"},
            {"section": "404", "control_id": "SOX-404-HR-03", "control_name": "Payroll Reconciliation", "control_objective": "Reconcile payroll to GL entries", "key_control": True, "frequency": "monthly"},
            {"section": "404", "control_id": "SOX-404-HR-04", "control_name": "Employee Onboarding/Offboarding", "control_objective": "Proper setup and termination procedures", "key_control": True, "frequency": "daily"},
            {"section": "404", "control_id": "SOX-404-HR-05", "control_name": "Access Management Reviews", "control_objective": "Periodic access reviews for HR systems", "key_control": True, "frequency": "quarterly"},
            {"section": "404", "control_id": "SOX-404-HR-06", "control_name": "Benefits Administration", "control_objective": "Accurate benefits enrollment and deductions", "key_control": True, "frequency": "monthly"},
            {"section": "404", "control_id": "SOX-404-HR-07", "control_name": "Time and Attendance", "control_objective": "Accurate tracking of time worked", "key_control": True, "frequency": "weekly"},
            {"section": "404", "control_id": "SOX-404-HR-08", "control_name": "Compensation Changes", "control_objective": "Authorized compensation modifications", "key_control": True, "frequency": "monthly"},
            {"section": "409", "control_id": "SOX-409-01", "control_name": "Real-Time Disclosure", "control_objective": "Timely disclosure of material changes", "key_control": True, "frequency": "daily"},
            {"section": "409", "control_id": "SOX-409-02", "control_name": "Material Event Monitoring", "control_objective": "Monitor for reportable events", "key_control": True, "frequency": "daily"},
            {"section": "802", "control_id": "SOX-802-01", "control_name": "Document Retention", "control_objective": "Retain audit workpapers for 7 years", "key_control": True, "frequency": "annual"},
            {"section": "802", "control_id": "SOX-802-02", "control_name": "Document Destruction Prevention", "control_objective": "Prevent destruction during investigations", "key_control": True, "frequency": "monthly"},
            {"section": "802", "control_id": "SOX-802-03", "control_name": "Electronic Records Management", "control_objective": "Proper electronic records storage", "key_control": True, "frequency": "monthly"},
        ]

        iso_count = 0
        for ctrl in iso_27001_controls:
            exists = await repo.check_control_library_exists("ISO_27001", ctrl["control_id"])
            if not exists:
                await repo.add_library_entry_no_commit(ComplianceControlLibrary(
                    framework="ISO_27001",
                    control_id=ctrl["control_id"],
                    control_name=ctrl["control_name"],
                    control_category=ctrl["control_category"],
                    domain=ctrl["domain"],
                    is_mandatory=True,
                    evidence_requirements=["Policy document", "Implementation evidence", "Review records"],
                    related_controls=[],
                ))
                iso_count += 1

        soc2_count = 0
        for ctrl in soc2_controls:
            exists = await repo.check_control_library_exists("SOC_2_TYPE_II", ctrl["control_id"])
            if not exists:
                await repo.add_library_entry_no_commit(ComplianceControlLibrary(
                    framework="SOC_2_TYPE_II",
                    control_id=ctrl["control_id"],
                    control_name=ctrl["control_name"],
                    control_category=ctrl["control_category"],
                    domain=ctrl["domain"],
                    is_mandatory=True,
                    evidence_requirements=["Control description", "Testing evidence", "Exception reports"],
                    related_controls=[],
                ))
                soc2_count += 1

        sox_count = 0
        for ctrl in sox_controls_seed:
            exists = await repo.check_control_library_exists("SOX", ctrl["control_id"])
            if not exists:
                await repo.add_library_entry_no_commit(ComplianceControlLibrary(
                    framework="SOX",
                    control_id=ctrl["control_id"],
                    control_name=ctrl["control_name"],
                    control_description=ctrl.get("control_objective"),
                    control_category=f"Section {ctrl['section']}",
                    domain="SOX Compliance",
                    is_mandatory=ctrl.get("key_control", True),
                    evidence_requirements=["Test results", "Supporting documentation", "Approval records"],
                    related_controls=[],
                ))
                sox_count += 1

        await repo.commit()

        total = iso_count + soc2_count + sox_count
        return SeedDataResponse(
            message=f"Successfully seeded {total} controls",
            iso_27001_controls=iso_count,
            soc_2_controls=soc2_count,
            sox_controls=sox_count,
            total_controls=total,
        )
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error seeding control library: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
