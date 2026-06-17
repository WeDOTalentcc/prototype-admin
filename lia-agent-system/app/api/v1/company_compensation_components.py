"""Endpoints do catalogo item-centric de verbas variaveis (compensation components).

Espelha company_benefits.py. company_id SEMPRE do JWT (require_company_id_strict_match).
GET /active retorna o catalogo com flag matches_vaga (compativeis pre-marcados na vaga).
POST faz dedup case-insensitive (promote-back vaga->catalogo) + audit + history.
"""
from app.middleware.request_id import get_correlation_id
import logging
import uuid as _uuid_module
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.company.repositories.compensation_component_repository import (
    CompensationComponentRepository,
)
from app.shared.security.require_company_id import require_company_id_strict_match
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company/compensation-components", tags=["compensation-components"])

_DATE_FIELDS = ("valid_from", "valid_until")


class CompensationComponentCreate(WeDoBaseModel):
    kind: str = "bonus"
    name: str
    description: str | None = None
    icon: str | None = None
    value_type: str = "percent"
    target_pct: float | None = None
    min_pct: float | None = None
    max_pct: float | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str = "BRL"
    frequency: str | None = None
    trigger: str | None = None
    spec: dict | None = None
    seniority_levels: list[str] = Field(default_factory=list)
    contract_types: list[str] = Field(default_factory=list)
    departments: dict | None = None
    subsidiaries: list | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool = True
    is_highlighted: bool = False
    order: int = 0


class CompensationComponentUpdate(WeDoBaseModel):
    kind: str | None = None
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    value_type: str | None = None
    target_pct: float | None = None
    min_pct: float | None = None
    max_pct: float | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    frequency: str | None = None
    trigger: str | None = None
    spec: dict | None = None
    seniority_levels: list[str] | None = None
    contract_types: list[str] | None = None
    departments: dict | None = None
    subsidiaries: list | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool | None = None
    is_highlighted: bool | None = None
    order: int | None = None


class CompensationComponentResponse(BaseModel):
    id: str
    company_id: str
    kind: str
    name: str
    description: str | None = None
    icon: str | None = None
    value_type: str | None = None
    target_pct: float | None = None
    min_pct: float | None = None
    max_pct: float | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    frequency: str | None = None
    trigger: str | None = None
    spec: dict | None = None
    seniority_levels: list | None = None
    contract_types: list | None = None
    departments: dict | None = None
    subsidiaries: list | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool = True
    is_highlighted: bool = False
    order: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    matches_vaga: bool | None = None

    class Config:
        from_attributes = True


def _coerce_dates(payload: dict) -> dict:
    for f in _DATE_FIELDS:
        v = payload.get(f)
        if isinstance(v, str) and v:
            try:
                payload[f] = date.fromisoformat(v[:10])
            except ValueError:
                payload[f] = None
    return payload


def _to_response(c, matches_vaga=None) -> CompensationComponentResponse:
    deps = getattr(c, "departments", None)
    return CompensationComponentResponse(
        id=str(c.id),
        company_id=c.company_id,
        kind=c.kind,
        name=c.name,
        description=c.description,
        icon=c.icon,
        value_type=c.value_type,
        target_pct=c.target_pct,
        min_pct=c.min_pct,
        max_pct=c.max_pct,
        min_amount=c.min_amount,
        max_amount=c.max_amount,
        currency=c.currency,
        frequency=c.frequency,
        trigger=c.trigger,
        spec=c.spec if isinstance(c.spec, dict) else None,
        seniority_levels=c.seniority_levels,
        contract_types=c.contract_types,
        departments=deps if isinstance(deps, dict) else None,
        subsidiaries=c.subsidiaries if isinstance(c.subsidiaries, list) else None,
        valid_from=c.valid_from.isoformat() if getattr(c, "valid_from", None) else None,
        valid_until=c.valid_until.isoformat() if getattr(c, "valid_until", None) else None,
        is_active=c.is_active,
        is_highlighted=c.is_highlighted,
        order=c.order,
        created_at=c.created_at.isoformat() if c.created_at else None,
        updated_at=c.updated_at.isoformat() if c.updated_at else None,
        matches_vaga=matches_vaga,
    )


async def _append_history(db, component_id, company_id, changed_by, change_type, previous_snapshot=None):
    try:
        from lia_models.compensation_component import CompensationComponentHistory
        db.add(CompensationComponentHistory(
            component_id=component_id,
            company_id=str(company_id),
            changed_by=changed_by,
            change_type=change_type,
            previous_snapshot=previous_snapshot,
        ))
    except Exception as hist_err:
        logger.error("Comp history insert failed component_id=%s: %s", component_id, hist_err)


async def _audit(current_user, company_id, target_id, operation, name):
    try:
        from app.shared.compliance.audit_service import AuditService as _AS
        await _AS().log_action(
            trace_id=get_correlation_id(),
            company_id=str(company_id),
            action_type="compensation_components_update",
            actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
            target_id=str(target_id),
            target_type="compensation_component",
            metadata={"source": f"rest_{operation}", "operation": operation, "name": name},
        )
    except Exception as e:
        logger.error("Audit log failed compensation_components (%s): %s", operation, e)


@router.get("/active", response_model=list[CompensationComponentResponse])
async def list_active_components(
    company_id: str | None = Query(None),
    seniority_level: str | None = Query(None),
    department: str | None = Query(None),
    contract_type: str | None = Query(None),
    subsidiary: str | None = Query(None),
    cnpj: str | None = Query(None),
    with_matches: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    """Registrado ANTES de /{component_id} (evita colisao de rota)."""
    try:
        eff = gated_company_id
        if not eff or eff in ("default", "unknown"):
            return []
        repo = CompensationComponentRepository(db)
        if with_matches or department or contract_type or seniority_level or subsidiary or cnpj:
            pairs = await repo.list_matching(
                eff,
                seniority_level=seniority_level,
                department=department,
                contract_type=contract_type,
                subsidiary=subsidiary,
                subsidiary_cnpj=cnpj,
                active_only=True,
            )
            return [_to_response(c, matches_vaga=flag) for c, flag in pairs]
        comps = await repo.list_for_company(eff, active_only=True)
        return [_to_response(c) for c in comps]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing active compensation components: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/", response_model=list[CompensationComponentResponse])
async def list_components(
    company_id: str | None = Query(None),
    kind: str | None = Query(None),
    search: str | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = CompensationComponentRepository(db)
        comps = await repo.list_for_company(gated_company_id, active_only=active_only, kind=kind, search=search)
        return [_to_response(c) for c in comps]
    except Exception as e:
        logger.error(f"Error listing compensation components: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/", response_model=CompensationComponentResponse)
async def create_component(
    component: CompensationComponentCreate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        eff = gated_company_id
        repo = CompensationComponentRepository(db)
        # promote-back dedup: nao duplica se ja existe (nome case-insensitive)
        existing = await repo.get_by_name_ci(eff, component.name)
        if existing is not None:
            logger.info("Comp component dedup hit (promote-back) name=%s company=%s", component.name, eff)
            return _to_response(existing)
        payload = _coerce_dates(component.model_dump())
        new_c = await repo.create(eff, payload)
        await _append_history(db, new_c.id, eff, getattr(current_user, "email", None), "created")
        await _audit(current_user, eff, new_c.id, "post_create", new_c.name)
        await db.commit()
        return _to_response(new_c)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating compensation component: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/{component_id}", response_model=CompensationComponentResponse)
async def get_component(
    component_id: str,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    repo = CompensationComponentRepository(db)
    c = await repo.get_by_id(component_id, gated_company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Compensation component not found")
    return _to_response(c)


@router.put("/{component_id}", response_model=CompensationComponentResponse)
async def update_component(
    component_id: str,
    component: CompensationComponentUpdate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = CompensationComponentRepository(db)
        c = await repo.get_by_id(component_id, gated_company_id)
        if not c:
            raise HTTPException(status_code=404, detail="Compensation component not found")
        payload = _coerce_dates(component.model_dump(exclude_unset=True, exclude_none=True))
        await repo.update(c, payload)
        await _append_history(db, c.id, gated_company_id, getattr(current_user, "email", None), "updated")
        await _audit(current_user, gated_company_id, c.id, "put_update", c.name)
        await db.commit()
        return _to_response(c)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating compensation component: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/{component_id}", response_model=None)
async def delete_component(
    component_id: str,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = CompensationComponentRepository(db)
        c = await repo.get_by_id(component_id, gated_company_id)
        if not c:
            raise HTTPException(status_code=404, detail="Compensation component not found")
        await repo.soft_delete(c)
        await _append_history(db, c.id, gated_company_id, getattr(current_user, "email", None), "deactivated")
        await db.commit()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting compensation component: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/seed-defaults", response_model=None)
async def seed_defaults(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = CompensationComponentRepository(db)
        created = await repo.seed_defaults(gated_company_id)
        await db.commit()
        return {"created": created}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding compensation defaults: {e}")
        raise LIAError(message="Erro interno do servidor")
