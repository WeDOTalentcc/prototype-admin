"""Endpoints da faixa salarial canonica GRANULAR (salary_bands) — catalogo.

FONTE UNICA: Configuracoes -> Faixas Salariais por Nivel. Mesmo padrao de
company_compensation_components: CRUD item-centric + escopo granular (contrato,
departamento, area, filial/CNPJ) + vigencia. company_id SEMPRE do JWT.
GET /map devolve {nivel: faixa-base} p/ o preview de R$ da verba.
"""
import logging
import uuid as _uuid_module
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.company.repositories.salary_band_repository import SalaryBandRepository
from app.shared.security.require_company_id import require_company_id_strict_match
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company/salary-bands", tags=["salary-bands"])

_DATE_FIELDS = ("valid_from", "valid_until")


class SalaryBandCreate(WeDoBaseModel):
    level: str
    label: str | None = None
    min: float | None = None
    mid: float | None = None
    max: float | None = None
    currency: str = "BRL"
    contract_types: list[str] = Field(default_factory=list)
    departments: dict | None = None
    area: list[str] = Field(default_factory=list)
    subsidiaries: list | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool = True
    order: int | None = None


class SalaryBandUpdate(WeDoBaseModel):
    level: str | None = None
    label: str | None = None
    min: float | None = None
    mid: float | None = None
    max: float | None = None
    currency: str | None = None
    contract_types: list[str] | None = None
    departments: dict | None = None
    area: list[str] | None = None
    subsidiaries: list | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool | None = None
    order: int | None = None


class SalaryBandResponse(BaseModel):
    id: str
    company_id: str
    level: str
    label: str | None = None
    min: float | None = None
    mid: float | None = None
    max: float | None = None
    currency: str | None = None
    contract_types: list | None = None
    departments: dict | None = None
    area: list | None = None
    subsidiaries: list | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool = True
    order: int = 0
    created_at: str | None = None
    updated_at: str | None = None

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


def _to_response(b) -> SalaryBandResponse:
    deps = getattr(b, "departments", None)
    return SalaryBandResponse(
        id=str(b.id),
        company_id=b.company_id,
        level=b.level,
        label=b.label,
        min=b.min, mid=b.mid, max=b.max,
        currency=b.currency,
        contract_types=b.contract_types if isinstance(b.contract_types, list) else None,
        departments=deps if isinstance(deps, dict) else None,
        area=b.area if isinstance(b.area, list) else None,
        subsidiaries=b.subsidiaries if isinstance(b.subsidiaries, list) else None,
        valid_from=b.valid_from.isoformat() if getattr(b, "valid_from", None) else None,
        valid_until=b.valid_until.isoformat() if getattr(b, "valid_until", None) else None,
        is_active=b.is_active,
        order=b.order or 0,
        created_at=b.created_at.isoformat() if b.created_at else None,
        updated_at=b.updated_at.isoformat() if b.updated_at else None,
    )


async def _audit(current_user, company_id, target_id, operation):
    try:
        from app.shared.compliance.audit_service import AuditService as _AS
        await _AS().log_action(
            trace_id=str(_uuid_module.uuid4()),
            company_id=str(company_id),
            action_type="salary_bands_update",
            actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
            target_id=str(target_id),
            target_type="salary_band",
            metadata={"source": f"rest_{operation}", "operation": operation},
        )
    except Exception as e:
        logger.error("Audit log failed salary_bands (%s): %s", operation, e)


@router.get("/map")
async def get_band_map(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    """{nivel: {min,mid,max,currency}} — faixa-base por nivel p/ preview de R$ da verba."""
    try:
        eff = gated_company_id
        if not eff or eff in ("default", "unknown"):
            return {}
        repo = SalaryBandRepository(db)
        return await repo.get_band_map(eff)
    except Exception as e:
        logger.error(f"Error building salary band map: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[SalaryBandResponse])
async def list_salary_bands(
    company_id: str | None = Query(None),
    level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        eff = gated_company_id
        if not eff or eff in ("default", "unknown"):
            return []
        repo = SalaryBandRepository(db)
        bands = await repo.list_for_company(eff, active_only=True, level=level)
        return [_to_response(b) for b in bands]
    except Exception as e:
        logger.error(f"Error listing salary bands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=SalaryBandResponse)
async def create_salary_band(
    band: SalaryBandCreate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = SalaryBandRepository(db)
        payload = _coerce_dates(band.model_dump())
        new_b = await repo.create(gated_company_id, payload)
        await _audit(current_user, gated_company_id, new_b.id, "post_create")
        await db.commit()
        return _to_response(new_b)
    except ValueError as ve:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating salary band: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{band_id}", response_model=SalaryBandResponse)
async def update_salary_band(
    band_id: str,
    band: SalaryBandUpdate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = SalaryBandRepository(db)
        b = await repo.get_by_id(band_id, gated_company_id)
        if not b:
            raise HTTPException(status_code=404, detail="Salary band not found")
        payload = _coerce_dates(band.model_dump(exclude_unset=True, exclude_none=True))
        await repo.update(b, payload)
        await _audit(current_user, gated_company_id, b.id, "put_update")
        await db.commit()
        return _to_response(b)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating salary band: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{band_id}", response_model=None)
async def delete_salary_band(
    band_id: str,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = SalaryBandRepository(db)
        b = await repo.get_by_id(band_id, gated_company_id)
        if not b:
            raise HTTPException(status_code=404, detail="Salary band not found")
        await repo.soft_delete(b)
        await db.commit()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting salary band: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-defaults", response_model=list[SalaryBandResponse])
async def seed_defaults(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = SalaryBandRepository(db)
        await repo.seed_defaults(gated_company_id)
        await _audit(current_user, gated_company_id, gated_company_id, "seed_defaults")
        await db.commit()
        bands = await repo.list_for_company(gated_company_id, active_only=True)
        return [_to_response(b) for b in bands]
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding salary bands: {e}")
        raise HTTPException(status_code=500, detail=str(e))
