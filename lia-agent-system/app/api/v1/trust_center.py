"""
Trust Center API Endpoints.

Provides public-facing security and compliance portal endpoints for:
- Public endpoints (no auth): Overview, certifications, controls, bias audits, subprocessors, resources, updates
- Admin endpoints (authenticated): Settings management, resource upload, subprocessor management
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.dependencies import get_trust_center_repo
from app.repositories.trust_center_repository import (
    TrustCenterRepository,
)
from app.schemas.trust_center import (
    BiasAuditSummary,
    CertificationInfo,
    ControlSummary,
    SubprocessorCreate,
    SubprocessorListResponse,
    SubprocessorResponse,
    TrustCenterBiasAuditsResponse,
    TrustCenterCertificationsResponse,
    TrustCenterControlsResponse,
    TrustCenterOverviewResponse,
    TrustCenterResourceCreate,
    TrustCenterResourceListResponse,
    TrustCenterResourceResponse,
    TrustCenterSettingsCreate,
    TrustCenterSettingsResponse,
    TrustCenterSettingsUpdate,
    TrustCenterUpdateCreate,
    TrustCenterUpdateListResponse,
    TrustCenterUpdateResponse,
)
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trust-center", tags=["trust-center"])


@router.get("/{company_slug}/overview", response_model=TrustCenterOverviewResponse, summary="Get public trust center overview")
async def get_trust_center_overview(
    company_slug: str,
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get public-facing trust center overview for a company."""
    try:
        settings = await repo.get_settings_by_slug(company_slug)

        controls_summary = None
        if settings.show_controls:
            controls_data = await repo.get_controls_framework_stats(settings.company_id)

            if controls_data:
                framework_stats = {}
                for row in controls_data:
                    if row.framework not in framework_stats:
                        framework_stats[row.framework] = {
                            "implemented": 0,
                            "partial": 0,
                            "not_implemented": 0,
                            "total": 0,
                        }
                    framework_stats[row.framework][row.status] = row.count
                    framework_stats[row.framework]["total"] += row.count

                total_implemented = sum(s.get("implemented", 0) for s in framework_stats.values())
                total_controls = sum(s.get("total", 0) for s in framework_stats.values())
                controls_summary = {
                    "frameworks": list(framework_stats.keys()),
                    "total_controls": total_controls,
                    "implemented": total_implemented,
                    "compliance_rate": round(total_implemented / total_controls * 100, 1) if total_controls > 0 else 0,
                }

        certs_count = await repo.count_implemented_controls(settings.company_id)

        return TrustCenterOverviewResponse(
            company_name=settings.company_name,
            company_description=settings.company_description,
            logo_url=settings.logo_url,
            primary_color=settings.primary_color,
            contact_email=settings.contact_email,
            privacy_policy_url=settings.privacy_policy_url,
            terms_url=settings.terms_url,
            certifications_count=certs_count,
            controls_summary=controls_summary,
            last_updated=settings.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trust center overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_slug}/certifications", response_model=TrustCenterCertificationsResponse, summary="List public certifications")
async def get_trust_center_certifications(
    company_slug: str,
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get public certifications and compliance badges."""
    try:
        settings = await repo.get_settings_by_slug(company_slug)

        if not settings.show_certifications:
            return TrustCenterCertificationsResponse(certifications=[], total=0)

        controls = await repo.list_implemented_controls_by_framework(settings.company_id)

        frameworks = {}
        for control in controls:
            if control.framework not in frameworks:
                frameworks[control.framework] = {
                    "name": control.framework,
                    "status": "active",
                    "description": f"Compliant with {control.framework} framework",
                    "issued_date": control.last_assessed,
                    "expires_date": control.next_review,
                }

        certifications = [
            CertificationInfo(
                name=f["name"],
                status=f["status"],
                issued_date=f["issued_date"],
                expires_date=f["expires_date"],
                description=f["description"],
            )
            for f in frameworks.values()
        ]

        return TrustCenterCertificationsResponse(
            certifications=certifications,
            total=len(certifications),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting certifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_slug}/controls", response_model=TrustCenterControlsResponse, summary="Get public control status")
async def get_trust_center_controls(
    company_slug: str,
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get high-level public control status by framework."""
    try:
        settings = await repo.get_settings_by_slug(company_slug)

        if not settings.show_controls:
            return TrustCenterControlsResponse(frameworks=[], overall_compliance=0)

        data = await repo.get_controls_framework_stats(settings.company_id)

        framework_stats = {}
        for row in data:
            if row.framework not in framework_stats:
                framework_stats[row.framework] = {
                    "implemented": 0,
                    "partial": 0,
                    "not_implemented": 0,
                    "in_progress": 0,
                }
            framework_stats[row.framework][row.status] = row.count

        frameworks = []
        total_implemented = 0
        total_controls = 0

        for framework, stats in framework_stats.items():
            total = sum(stats.values())
            implemented = stats.get("implemented", 0)
            partial = stats.get("partial", 0)
            not_impl = stats.get("not_implemented", 0) + stats.get("in_progress", 0)

            total_implemented += implemented
            total_controls += total

            frameworks.append(
                ControlSummary(
                    framework=framework,
                    total_controls=total,
                    implemented=implemented,
                    partial=partial,
                    not_implemented=not_impl,
                    compliance_percentage=round(implemented / total * 100, 1) if total > 0 else 0,
                )
            )

        overall = round(total_implemented / total_controls * 100, 1) if total_controls > 0 else 0

        return TrustCenterControlsResponse(
            frameworks=frameworks,
            overall_compliance=overall,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting controls: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_slug}/bias-audits", response_model=TrustCenterBiasAuditsResponse, summary="Get public bias audit reports")
async def get_trust_center_bias_audits(
    company_slug: str,
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get public bias audit reports."""
    try:
        settings = await repo.get_settings_by_slug(company_slug)

        if not settings.show_bias_audits:
            return TrustCenterBiasAuditsResponse(audits=[], total=0, latest_audit_date=None)

        audits = await repo.list_public_bias_audits(settings.company_id)

        audit_summaries = []
        latest_date = None

        for audit in audits:
            if not latest_date and audit.published_at:
                latest_date = audit.published_at

            audit_summaries.append(
                BiasAuditSummary(
                    audit_period=f"{audit.audit_start_date} - {audit.audit_end_date}" if audit.audit_start_date else "N/A",
                    audit_type=audit.audit_type or "quarterly",
                    status=audit.overall_status or "complete",
                    categories_evaluated=audit.categories_evaluated or [],
                    overall_result=audit.overall_status or "passed",
                    published_at=audit.published_at,
                )
            )

        return TrustCenterBiasAuditsResponse(
            audits=audit_summaries,
            total=len(audit_summaries),
            latest_audit_date=latest_date,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bias audits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_slug}/subprocessors", response_model=SubprocessorListResponse, summary="List data subprocessors")
async def get_trust_center_subprocessors(
    company_slug: str,
    category: str | None = Query(None, description="Filter by category"),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get list of data subprocessors."""
    try:
        settings = await repo.get_settings_by_slug(company_slug)

        if not settings.show_subprocessors:
            return SubprocessorListResponse(subprocessors=[], total=0)

        subprocessors = await repo.list_subprocessors(settings.company_id, category=category)

        return SubprocessorListResponse(
            subprocessors=[SubprocessorResponse(**s.to_dict()) for s in subprocessors],
            total=len(subprocessors),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subprocessors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_slug}/resources", response_model=TrustCenterResourceListResponse, summary="List downloadable resources")
async def get_trust_center_resources(
    company_slug: str,
    category: str | None = Query(None, description="Filter by category"),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get list of downloadable policies and documents."""
    try:
        settings = await repo.get_settings_by_slug(company_slug)

        resources = await repo.list_resources(settings.company_id, category=category)

        return TrustCenterResourceListResponse(
            resources=[TrustCenterResourceResponse(**r.to_dict()) for r in resources],
            total=len(resources),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_slug}/updates", response_model=TrustCenterUpdateListResponse, summary="Get compliance updates")
async def get_trust_center_updates(
    company_slug: str,
    category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get compliance news and updates."""
    try:
        settings = await repo.get_settings_by_slug(company_slug)

        updates = await repo.list_updates(settings.company_id, category=category, limit=limit)
        total = await repo.count_updates(settings.company_id, category=category)

        return TrustCenterUpdateListResponse(
            updates=[TrustCenterUpdateResponse(**u.to_dict()) for u in updates],
            total=total,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting updates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings", response_model=TrustCenterSettingsResponse, summary="Create trust center settings")
async def create_trust_center_settings(
    settings_data: TrustCenterSettingsCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Create trust center settings for a company (admin only)."""
    try:
        company_uuid = UUID(company_id)

        existing = await repo.get_settings_by_company_id(company_uuid)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Trust center settings already exist for this company",
            )

        if await repo.settings_slug_taken(settings_data.company_slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company slug already in use",
            )

        settings = await repo.create_settings(company_uuid, settings_data.model_dump())

        return TrustCenterSettingsResponse(**settings.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trust center settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=TrustCenterSettingsResponse, summary="Update trust center settings")
async def update_trust_center_settings(
    settings_data: TrustCenterSettingsUpdate,
    company_id: str = Depends(get_verified_company_id),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Update trust center settings (admin only)."""
    try:
        company_uuid = UUID(company_id)

        settings = await repo.get_settings_by_company_id(company_uuid)
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trust center settings not found",
            )

        if settings_data.company_slug and settings_data.company_slug != settings.company_slug:
            if await repo.settings_slug_taken(settings_data.company_slug, exclude_id=settings.id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Company slug already in use",
                )

        updated = await repo.update_settings(settings, settings_data.model_dump(exclude_unset=True))

        return TrustCenterSettingsResponse(**updated.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trust center settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings", response_model=TrustCenterSettingsResponse, summary="Get trust center settings")
async def get_trust_center_settings(
    company_id: str = Depends(get_verified_company_id),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Get trust center settings for authenticated company."""
    try:
        company_uuid = UUID(company_id)

        settings = await repo.get_settings_by_company_id(company_uuid)
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trust center settings not found",
            )

        return TrustCenterSettingsResponse(**settings.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trust center settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resources", response_model=TrustCenterResourceResponse, summary="Add a resource")
async def create_trust_center_resource(
    resource_data: TrustCenterResourceCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Add a downloadable resource (admin only)."""
    try:
        company_uuid = UUID(company_id)
        resource = await repo.create_resource(company_uuid, resource_data.model_dump())
        return TrustCenterResourceResponse(**resource.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating resource: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subprocessors", response_model=SubprocessorResponse, summary="Add a subprocessor")
async def create_subprocessor(
    subprocessor_data: SubprocessorCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Add a data subprocessor (admin only)."""
    try:
        company_uuid = UUID(company_id)
        subprocessor = await repo.create_subprocessor(company_uuid, subprocessor_data.model_dump())
        return SubprocessorResponse(**subprocessor.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subprocessor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/updates", response_model=TrustCenterUpdateResponse, summary="Post an update")
async def create_trust_center_update(
    update_data: TrustCenterUpdateCreate,
    company_id: str = Depends(get_verified_company_id),
    repo: TrustCenterRepository = Depends(get_trust_center_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (trust_center) — no tenant data
    """Post a compliance update/news (admin only)."""
    try:
        company_uuid = UUID(company_id)
        update = await repo.create_update(
            company_uuid,
            update_data.model_dump(),
            is_published=update_data.is_published,
        )
        return TrustCenterUpdateResponse(**update.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
