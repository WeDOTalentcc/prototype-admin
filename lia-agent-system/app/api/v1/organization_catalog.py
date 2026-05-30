"""
Organization Catalog API Endpoints.

Provides endpoints to query the organizational catalog with areas,
roles, seniority levels, and competencies.
"""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.shared.services.organization_catalog_service import (
    OrganizationCatalogService,
    get_organization_catalog_service,
)
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/catalog", tags=["organization-catalog"])


@router.get("/areas", response_model=None)
async def get_areas(
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all organizational areas/departments."""
    areas = catalog_svc.get_all_areas()
    return {
        "total": len(areas),
        "areas": areas
    }


@router.get("/areas/{area_id}", response_model=None)
async def get_area(
    area_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a specific area by ID."""
    area = catalog_svc.get_area_by_id(area_id)
    if not area:
        return {"error": "Area not found", "area_id": area_id}
    return area


@router.get("/areas/detect", response_model=None)
async def detect_area(
    text: str = Query(..., description="Text to analyze for area detection"),
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Detect the most likely area from a text."""
    area = catalog_svc.detect_area_from_text(text)
    return {
        "input_text": text,
        "detected_area": area
    }


@router.get("/seniority-levels", response_model=None)
async def get_seniority_levels(
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all seniority levels."""
    levels = catalog_svc.get_all_seniority_levels()
    return {
        "total": len(levels),
        "levels": levels
    }


@router.get("/roles", response_model=None)
async def get_roles(
    area_id: str | None = Query(None, description="Filter by area ID"),
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all roles, optionally filtered by area."""
    if area_id:
        roles = catalog_svc.get_roles_by_area(area_id)
    else:
        roles = catalog_svc.get_all_roles()

    return {
        "total": len(roles),
        "area_id": area_id,
        "roles": roles
    }


@router.get("/roles/{area_id}", response_model=None)
async def get_roles_by_area(
    area_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all roles for a specific area."""
    roles = catalog_svc.get_roles_by_area(area_id)
    area = catalog_svc.get_area_by_id(area_id)
    return {
        "area": area,
        "total": len(roles),
        "roles": roles
    }


@router.get("/roles/search/{role_name}", response_model=None)
async def search_role(
    role_name: str,
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Search for a role by name."""
    role = catalog_svc.get_role_by_name(role_name)
    return {
        "query": role_name,
        "role": role
    }


@router.get("/skills/technical", response_model=None)
async def get_technical_skills(
    area_id: str | None = Query(None, description="Filter by area ID"),
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all technical skills, optionally filtered by area."""
    if area_id:
        skills = catalog_svc.get_technical_skills_by_area(area_id)
    else:
        skills = catalog_svc.get_all_technical_skills()

    return {
        "total": len(skills),
        "area_id": area_id,
        "skills": skills
    }


@router.get("/skills/technical/{area_id}", response_model=None)
async def get_technical_skills_by_area(
    area_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all technical skills for a specific area."""
    skills = catalog_svc.get_technical_skills_by_area(area_id)
    area = catalog_svc.get_area_by_id(area_id)
    return {
        "area": area,
        "total": len(skills),
        "skills": skills
    }


@router.get("/skills/behavioral", response_model=None)
async def get_behavioral_skills(
    category: str | None = Query(None, description="Filter by category"),
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all behavioral competencies, optionally filtered by category."""
    if category:
        skills = catalog_svc.get_behavioral_skills_by_category(category)
    else:
        skills = catalog_svc.get_all_behavioral_skills()

    return {
        "total": len(skills),
        "category": category,
        "skills": skills
    }


@router.get("/skills/search", response_model=None)
async def search_skills(
    q: str = Query(..., min_length=2, description="Search query"),
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Search for skills by name or keyword."""
    results = catalog_svc.search_skills(q)
    return {
        "query": q,
        "technical_matches": len(results["technical"]),
        "behavioral_matches": len(results["behavioral"]),
        "results": results
    }


@router.get("/suggest-skills", response_model=None)
async def suggest_skills(
    role_name: str = Query(..., description="Role name"),
    seniority: str | None = Query(None, description="Seniority level ID"),
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Suggest skills for a role and seniority level."""
    suggestions = catalog_svc.suggest_skills_for_role(role_name, seniority)
    return {
        "role_name": role_name,
        "seniority": seniority,
        "technical_skills_count": len(suggestions["technical"]),
        "behavioral_skills_count": len(suggestions["behavioral"]),
        "suggestions": suggestions
    }


@router.get("/summary", response_model=None)
async def get_catalog_summary(
    catalog_svc: OrganizationCatalogService = Depends(get_organization_catalog_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a complete summary of the catalog for review."""
    return catalog_svc.get_catalog_summary()

reorder_collection_before_item(router)
