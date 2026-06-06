"""Per-role PII field visibility defaults (company-level, admin-only).

Companion to app/shared/rbac/pii_field_resolver.py (resolution) — this persists the
{role: {field: bool}} defaults read by candidates_crud._load_role_pii_defaults.
Multi-tenancy: company_id from JWT only. LGPD Art. 6 III minimização.

Routes:
  GET  /api/v1/pii-visibility-defaults   → read defaults (any authenticated tenant user)
  PUT  /api/v1/pii-visibility-defaults   → replace defaults for provided roles (admin only)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_role
from app.auth.models import UserRole, User
from app.core.database import AsyncSessionLocal
from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository
from app.shared.rbac.pii_field_catalog import GATEABLE_PII_FIELDS
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

_VALID_ROLES = {r.value for r in UserRole}
_VALID_FIELDS = set(GATEABLE_PII_FIELDS)

router = APIRouter(prefix="/pii-visibility-defaults", tags=["pii-visibility"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PiiVisibilityDefaultsPayload(WeDoBaseModel):
    defaults: dict[str, dict[str, bool]]


# ---------------------------------------------------------------------------
# Pure validator (no DB — directly unit-testable)
# ---------------------------------------------------------------------------

def validate_pii_defaults(defaults: dict) -> None:
    """Raise HTTPException(422) if any role/field/value is invalid. Pure (no DB)."""
    for role, field_map in defaults.items():
        if role not in _VALID_ROLES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid role: {role!r}. Valid roles: {sorted(_VALID_ROLES)}",
            )
        if not isinstance(field_map, dict):
            raise HTTPException(
                status_code=422,
                detail=f"Role {role!r} must map to an object (dict), got {type(field_map).__name__}",
            )
        for field, value in field_map.items():
            if field not in _VALID_FIELDS:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid PII field: {field!r}. Valid fields: {sorted(_VALID_FIELDS)}",
                )
            if not isinstance(value, bool):
                raise HTTPException(
                    status_code=422,
                    detail=f"Value for {role}.{field} must be boolean, got {type(value).__name__}",
                )


def validate_pii_field_override(value: dict) -> None:
    """Raise HTTPException(422) if a per-user override map has invalid field/value. Pure."""
    for field, v in value.items():
        if field not in _VALID_FIELDS:
            raise HTTPException(status_code=422, detail=f"Invalid PII field: {field!r}")
        if not isinstance(v, bool):
            raise HTTPException(status_code=422, detail=f"Value for {field!r} must be boolean")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def get_pii_visibility_defaults(
    company_id: str = Depends(require_company_id),
):
    """Return per-role PII visibility defaults for the JWT company.

    Returns empty dict if no defaults have been set yet (all-visible by default
    — consumer falls back to pii_field_resolver deny-list logic).
    """
    async with AsyncSessionLocal() as db:
        policy = await HiringPolicyRepository(db).get_by_company(company_id)
    stored = (getattr(policy, "pii_visibility_defaults", None) or {}) if policy else {}
    return {"defaults": stored}


@router.put("")
async def put_pii_visibility_defaults(
    payload: PiiVisibilityDefaultsPayload,
    current_user: User = Depends(require_role([UserRole.admin, UserRole.wedotalent_admin])),
    company_id: str = Depends(require_company_id),
):
    """Replace per-role PII visibility defaults (admin-only, company-scoped).

    Shallow-merge semantics: provided role keys replace their sub-maps; omitted
    role keys are preserved unchanged (upsert does per-key merge at the
    pii_visibility_defaults level).

    Body: {"defaults": {"manager": {"cpf": false, "current_salary": true}, ...}}
    """
    validate_pii_defaults(payload.defaults)
    user_id = str(getattr(current_user, "id", None)) if getattr(current_user, "id", None) else None
    async with AsyncSessionLocal() as db:
        repo = HiringPolicyRepository(db)
        policy = await repo.upsert(
            company_id,
            {"pii_visibility_defaults": payload.defaults},
            valid_blocks=["pii_visibility_defaults"],
            user_id=user_id,
        )
        await db.commit()
        stored = (getattr(policy, "pii_visibility_defaults", None) or {}) if policy else payload.defaults
    logger.info(
        "[pii-visibility] company=%s user=%s roles_updated=%s",
        company_id, user_id, list(payload.defaults.keys()),
    )
    return {"defaults": stored}
