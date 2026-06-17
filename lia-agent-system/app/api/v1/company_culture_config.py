"""
Company Culture Config API endpoints.
Handles CRUD for culture values and ideal profiles (config data, not analysis).
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from app.domains.company.dependencies import (
    get_culture_value_repo,
    get_ideal_profile_repo,
)
from app.domains.company.repositories.culture_value_repository import CultureValueRepository
from app.domains.company.repositories.ideal_profile_repository import IdealProfileRepository
from app.schemas.company import (
    CultureValueCreate,
    CultureValueResponse,
    CultureValueUpdate,
    IdealProfileCreate,
    IdealProfileResponse,
    IdealProfileUpdate,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


@router.get("/culture-values", response_model=list[CultureValueResponse])
async def list_culture_values(
    company_id: uuid.UUID | None = Query(None),
    category: str | None = Query(None),
    include_inactive: bool = Query(False),
    cv_repo: CultureValueRepository = Depends(get_culture_value_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all culture values for a company."""
    try:
        if not company_id:
            return []
        values = await cv_repo.list_for_company(company_id)
        if category:
            values = [v for v in values if v.category == category]
        if not include_inactive:
            values = [v for v in values if v.is_active]
        return values
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): preserve full traceback (was hidden by f-string
        # of `str(e)`) and do not leak internal error message to the client.
        logger.exception("Error listing culture values")
        raise LIAError(message="internal error") from e


@router.post("/culture-values", response_model=CultureValueResponse)
async def create_culture_value(
    company_id: uuid.UUID,
    data: CultureValueCreate,
    cv_repo: CultureValueRepository = Depends(get_culture_value_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new culture value."""
    try:
        cv = await cv_repo.create({"company_id": company_id, **data.model_dump()})
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created culture value: {cv.name}")
        return cv
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error creating culture value")
        raise LIAError(message="internal error") from e


@router.put("/culture-values/{value_id}", response_model=CultureValueResponse)
async def update_culture_value(
    value_id: uuid.UUID,
    data: CultureValueUpdate,
    cv_repo: CultureValueRepository = Depends(get_culture_value_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update a culture value."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        cv = await cv_repo.update(value_id, update_data)
        if not cv:
            raise HTTPException(status_code=404, detail="Culture value not found")
        return cv
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error updating culture value")
        raise LIAError(message="internal error") from e


@router.delete("/culture-values/{value_id}", response_model=None)
async def delete_culture_value(
    value_id: uuid.UUID,
    cv_repo: CultureValueRepository = Depends(get_culture_value_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Soft delete a culture value."""
    try:
        deleted = await cv_repo.delete(value_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Culture value not found")
        return {"success": True, "message": "Culture value deleted"}
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error deleting culture value")
        raise LIAError(message="internal error") from e


@router.get("/ideal-profiles", response_model=list[IdealProfileResponse])
async def list_ideal_profiles(
    company_id: uuid.UUID | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    role_type: str | None = Query(None),
    seniority_level: str | None = Query(None),
    include_inactive: bool = Query(False),
    ip_repo: IdealProfileRepository = Depends(get_ideal_profile_repo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all ideal profiles."""
    try:
        if not company_id:
            return []
        profiles = await ip_repo.list_for_company(company_id)
        if department_id:
            profiles = [p for p in profiles if p.department_id == department_id]
        if role_type:
            profiles = [p for p in profiles if p.role_type == role_type]
        if seniority_level:
            profiles = [p for p in profiles if p.seniority_level == seniority_level]
        if not include_inactive:
            profiles = [p for p in profiles if p.is_active]
        return profiles
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error listing ideal profiles")
        raise LIAError(message="internal error") from e


@router.post("/ideal-profiles", response_model=IdealProfileResponse)
async def create_ideal_profile(
    company_id: uuid.UUID,
    data: IdealProfileCreate,
    ip_repo: IdealProfileRepository = Depends(get_ideal_profile_repo),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new ideal profile."""
    try:
        profile = await ip_repo.create({"company_id": company_id, **data.model_dump()})
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created ideal profile: {profile.name}")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error creating ideal profile")
        raise LIAError(message="internal error") from e


@router.get("/ideal-profiles/{profile_id}", response_model=IdealProfileResponse)
async def get_ideal_profile(
    profile_id: uuid.UUID,
    ip_repo: IdealProfileRepository = Depends(get_ideal_profile_repo),
    company_id: str = Depends(require_company_id),
):
    # Sprint 4 v3 (2026-05-25): canonical endpoint para o SourcingTab
    # do TalentPoolPage pre-popular inputs a partir do arquetipo vinculado ao pool.
    # Multi-tenancy: 404 quando profile pertence a outro tenant (nao 403,
    # para nao vazar existencia cross-tenant).
    try:
        profile = await ip_repo.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Ideal profile not found")
        if str(profile.company_id) != str(company_id):
            raise HTTPException(status_code=404, detail="Ideal profile not found")
        return profile
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching ideal profile")
        raise LIAError(message="internal error") from None

@router.put("/ideal-profiles/{profile_id}", response_model=IdealProfileResponse)
async def update_ideal_profile(
    profile_id: uuid.UUID,
    data: IdealProfileUpdate,
    ip_repo: IdealProfileRepository = Depends(get_ideal_profile_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an ideal profile."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        existing = await ip_repo.get_by_id(profile_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Ideal profile not found")
        if data.validated and not existing.validated_at:
            update_data["validated_at"] = datetime.utcnow()
        update_data["updated_at"] = datetime.utcnow()
        profile = await ip_repo.update(profile_id, update_data)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error updating ideal profile")
        raise LIAError(message="internal error") from e


@router.delete("/ideal-profiles/{profile_id}", response_model=None)
async def delete_ideal_profile(
    profile_id: uuid.UUID,
    ip_repo: IdealProfileRepository = Depends(get_ideal_profile_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Soft delete an ideal profile."""
    try:
        deleted = await ip_repo.delete(profile_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ideal profile not found")
        return {"success": True, "message": "Ideal profile deleted"}
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error deleting ideal profile")
        raise LIAError(message="internal error") from e
