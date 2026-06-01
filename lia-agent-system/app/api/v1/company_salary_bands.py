"""Endpoints da faixa salarial canonica por nivel (salary_bands).

FONTE UNICA: Configuracoes -> Faixas Salariais por Nivel. company_id SEMPRE do
JWT (require_company_id_strict_match). PUT / substitui a tabela inteira (a UI
edita o conjunto de bandas de uma vez). Espelha company_compensation_components.
"""
import logging
import uuid as _uuid_module

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.company.repositories.salary_band_repository import SalaryBandRepository
from app.shared.security.require_company_id import require_company_id_strict_match
from app.shared.seniority_levels import label_for, order_for
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company/salary-bands", tags=["salary-bands"])


class SalaryBandItem(WeDoBaseModel):
    level: str
    label: str | None = None
    min: float | None = None
    mid: float | None = None
    max: float | None = None
    currency: str = "BRL"
    order: int | None = None


class SalaryBandsReplaceRequest(WeDoBaseModel):
    bands: list[SalaryBandItem] = Field(default_factory=list)


class SalaryBandResponse(BaseModel):
    id: str
    company_id: str
    level: str
    label: str | None = None
    min: float | None = None
    mid: float | None = None
    max: float | None = None
    currency: str | None = None
    is_active: bool = True
    order: int = 0
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


# Defaults BR p/ seed (mesmos valores do defaultPolicy do frontend)
_DEFAULT_BANDS = [
    {"level": "junior", "min": 4000, "mid": 6000, "max": 8000},
    {"level": "pleno", "min": 7000, "mid": 9500, "max": 12000},
    {"level": "senior", "min": 11000, "mid": 14000, "max": 17000},
]


def _to_response(b) -> SalaryBandResponse:
    return SalaryBandResponse(
        id=str(b.id),
        company_id=b.company_id,
        level=b.level,
        label=b.label,
        min=b.min,
        mid=b.mid,
        max=b.max,
        currency=b.currency,
        is_active=b.is_active,
        order=b.order,
        created_at=b.created_at.isoformat() if b.created_at else None,
        updated_at=b.updated_at.isoformat() if b.updated_at else None,
    )


async def _audit(current_user, company_id, operation, count):
    try:
        from app.shared.compliance.audit_service import AuditService as _AS
        await _AS().log_action(
            trace_id=str(_uuid_module.uuid4()),
            company_id=str(company_id),
            action_type="salary_bands_update",
            actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
            target_id=str(company_id),
            target_type="salary_bands",
            metadata={"source": f"rest_{operation}", "operation": operation, "count": count},
        )
    except Exception as e:
        logger.error("Audit log failed salary_bands (%s): %s", operation, e)


@router.get("/", response_model=list[SalaryBandResponse])
async def list_salary_bands(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        eff = gated_company_id
        if not eff or eff in ("default", "unknown"):
            return []
        repo = SalaryBandRepository(db)
        bands = await repo.list_for_company(eff, active_only=True)
        return [_to_response(b) for b in bands]
    except Exception as e:
        logger.error(f"Error listing salary bands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", response_model=list[SalaryBandResponse])
async def replace_salary_bands(
    payload: SalaryBandsReplaceRequest,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    gated_company_id: str = Depends(require_company_id_strict_match("query.company_id")),
):
    try:
        repo = SalaryBandRepository(db)
        bands = await repo.replace_all(
            gated_company_id, [b.model_dump() for b in payload.bands]
        )
        await _audit(current_user, gated_company_id, "put_replace", len(bands))
        await db.commit()
        return [_to_response(b) for b in bands]
    except ValueError as ve:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error replacing salary bands: {e}")
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
        existing = await repo.list_for_company(gated_company_id, active_only=True)
        if existing:
            return [_to_response(b) for b in existing]
        seed = [
            {**d, "label": label_for(d["level"]), "order": order_for(d["level"]), "currency": "BRL"}
            for d in _DEFAULT_BANDS
        ]
        bands = await repo.replace_all(gated_company_id, seed)
        await _audit(current_user, gated_company_id, "seed_defaults", len(bands))
        await db.commit()
        return [_to_response(b) for b in bands]
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding salary bands: {e}")
        raise HTTPException(status_code=500, detail=str(e))
