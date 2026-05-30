import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.modules.services.module_service import get_module_service, ModuleService
from lia_models.billing import AVAILABLE_MODULES, MODULE_STATUS_OPTIONS, ModuleStatus, ModuleTier
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modules", tags=["modules"])


def _get_company_id(request: Request) -> str:
    company_id = getattr(request.state, "company_id", None)
    if not company_id:
        raise HTTPException(status_code=401, detail="Company context required")
    return company_id


def _enforce_tenant(request: Request, company_id: str) -> None:
    tenant_id = getattr(request.state, "company_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Company context required")
    is_admin = getattr(request.state, "is_admin", False)
    if is_admin:
        return
    if tenant_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied: company mismatch")


def _validate_status(status: str) -> None:
    valid = [s.value for s in ModuleStatus]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Valid: {valid}")


def _validate_tier(tier: str) -> None:
    valid = [t.value for t in ModuleTier]
    if tier not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Valid: {valid}")


class ModuleUpdateRequest(WeDoBaseModel):
    status: Optional[str] = Field(None, description="New status: beta, trial, active, expired, disabled")
    tier: Optional[str] = Field(None, description="New tier: free, basic, pro, enterprise")
    expires_at: Optional[str] = Field(None, description="ISO date for expiry")


class ModuleActivateRequest(WeDoBaseModel):
    module_name: str
    status: str = Field(default="beta")
    tier: str = Field(default="free")
    expires_at: Optional[str] = None


@router.get("")
@router.get("/catalog")
async def get_module_catalog(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    items = []
    for name, info in AVAILABLE_MODULES.items():
        items.append({
            "module_name": name,
            "label": info["label"],
            "description": info["description"],
            "initial_status": info["initial_status"],
        })
    return {"modules": items, "status_options": MODULE_STATUS_OPTIONS}


@router.get("/{company_id}")
@router.get("/company/{company_id}")
async def get_company_modules(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: Request,
    include_catalog: bool = False,
    db: AsyncSession = Depends(get_db),
    svc: ModuleService = Depends(get_module_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _enforce_tenant(request, company_id)
    modules = await svc.get_company_modules(db, company_id, include_catalog=include_catalog)
    return {"company_id": company_id, "modules": modules, "count": len(modules)}


@router.get("/company/{company_id}/check/{module_name}")
async def check_module_active(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    module_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    svc: ModuleService = Depends(get_module_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _enforce_tenant(request, company_id)
    active = await svc.is_module_active(db, company_id, module_name)
    status = await svc.get_module_status(db, company_id, module_name)
    tier = await svc.get_module_tier(db, company_id, module_name)
    return {
        "company_id": company_id,
        "module_name": module_name,
        "is_active": active,
        "status": status,
        "tier": tier,
    }


@router.post("/company/{company_id}/activate")
async def activate_module(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: ModuleActivateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    svc: ModuleService = Depends(get_module_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _enforce_tenant(request, company_id)
    _validate_status(body.status)
    _validate_tier(body.tier)

    expires = None
    if body.expires_at:
        try:
            expires = datetime.fromisoformat(body.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format (use ISO 8601)")

    result = await svc.activate_module(
        db,
        company_id,
        body.module_name,
        status=body.status,
        tier=body.tier,
        expires_at=expires,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Activation failed"))
    return result


@router.post("/company/{company_id}/deactivate/{module_name}")
async def deactivate_module(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    module_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    svc: ModuleService = Depends(get_module_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _enforce_tenant(request, company_id)
    result = await svc.deactivate_module(db, company_id, module_name)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Deactivation failed"))
    return result


@router.patch("/company/{company_id}/{module_name}")
async def update_module(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    module_name: str,
    body: ModuleUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    svc: ModuleService = Depends(get_module_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _enforce_tenant(request, company_id)

    expires = None
    if body.expires_at:
        try:
            expires = datetime.fromisoformat(body.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format")

    if body.status:
        _validate_status(body.status)
    if body.tier:
        _validate_tier(body.tier)

    result = await svc.update_module(
        db,
        company_id,
        module_name,
        status=body.status,
        tier=body.tier,
        expires_at=expires,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/company/{company_id}/seed")
async def seed_company_modules(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: Request,
    db: AsyncSession = Depends(get_db),
    svc: ModuleService = Depends(get_module_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _enforce_tenant(request, company_id)
    created = await svc.seed_beta_modules(db, company_id)
    return {
        "company_id": company_id,
        "seeded": created,
        "count": len(created),
    }


@router.patch("/{module_id}")
async def update_module_by_id(
    module_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: ModuleUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_tenant_db),
    svc: ModuleService = Depends(get_module_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    mod = await svc.get_module_by_id(db, module_id)
    if not mod:
        raise HTTPException(status_code=404, detail=f"Module {module_id} not found")
    _enforce_tenant(request, mod.company_id)

    expires = None
    if body.expires_at:
        try:
            expires = datetime.fromisoformat(body.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format")

    if body.status:
        _validate_status(body.status)
    if body.tier:
        _validate_tier(body.tier)

    result = await svc.update_module_by_id(
        db,
        module_id,
        status=body.status,
        tier=body.tier,
        expires_at=expires,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/company/{company_id}/billing/{module_name}")
async def get_module_billing_context(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    module_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    svc: ModuleService = Depends(get_module_service),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _enforce_tenant(request, company_id)
    ctx = await svc.get_billing_context(db, company_id, module_name)
    if not ctx:
        raise HTTPException(status_code=404, detail="Module not found")
    return ctx

reorder_collection_before_item(router)
