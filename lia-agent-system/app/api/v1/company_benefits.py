"""
Company Benefits API endpoints.
CRUD operations for company-specific benefits management.

Schema-alvo: 1:1 com Rails canonical (`ats-api-copia/db/migrate/20250715000005_create_benefits.rb`).
Cobre 24 colunas (22 do Rails + icon e timestamps).

Multi-tenancy: scoping por company_id em toda query (RLS no DB tambem aplicada).

LGPD: provider_contact e PII. Camadas downstream (logs, JD publicada) devem
mascarar — ver // TODO(LGPD:001) em jd_template_service.

Mudancas Fase 1 (2026-04-30):
  - Pydantic Create/Update/Response cobrem 22 campos editaveis (antes: 8).
  - Validacao condicional por value_type (monetary|percentage|informative).
  - Helper _to_response retorna 24 colunas.
"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id, validate_company_access
from app.auth.models import User
from app.core.database import get_db
from app.domains.company.repositories.company_benefit_repository import (
    CompanyBenefitRepository,
)

router = APIRouter(prefix="/company/benefits", tags=["company-benefits"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CompanyBenefitBase(BaseModel):
    """Campos editaveis (mesmos para Create e Update)."""

    name: str | None = Field(None, max_length=255)
    category: str | None = None
    description: str | None = None
    icon: str | None = None

    # Valor (3 modos)
    value: float | None = None
    percentage_value: float | None = None
    value_type: str | None = "informative"  # monetary | percentage | informative
    value_details: str | None = None

    # Elegibilidade
    applicable_to: list[str] | None = Field(default_factory=list)
    seniority_levels: list[str] | None = Field(default_factory=list)
    contract_types: list[str] | None = Field(default_factory=list)
    departments: dict[str, Any] | None = Field(default_factory=dict)

    # Regras operacionais
    waiting_period_days: int | None = None
    is_mandatory: bool | None = False
    is_active: bool | None = True
    is_highlighted: bool | None = False
    is_discount: bool | None = False

    # Apresentacao
    order: int | None = 0

    # Provider (PII em provider_contact — // TODO(LGPD:001) em jd_template_service)
    provider: str | None = None
    provider_contact: str | None = None


class CompanyBenefitCreate(CompanyBenefitBase):
    """Create exige `name` (override).

    Validacao condicional por value_type:
      - monetary    -> value e obrigatorio
      - percentage  -> percentage_value e obrigatorio
      - informative -> value_details e obrigatorio (ou description como fallback)
    """
    name: str = Field(..., min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_value_by_type(self) -> "CompanyBenefitCreate":
        vt = (self.value_type or "informative").lower()
        if vt == "monetary" and self.value is None:
            raise ValueError("value e obrigatorio quando value_type='monetary'")
        if vt == "percentage" and self.percentage_value is None:
            raise ValueError("percentage_value e obrigatorio quando value_type='percentage'")
        if vt == "informative" and not self.value_details and not self.description:
            raise ValueError(
                "value_details (ou description) e obrigatorio quando value_type='informative'"
            )
        return self


class CompanyBenefitUpdate(CompanyBenefitBase):
    """Update aceita campos parciais. Sem validacao condicional pois pode
    estar atualizando so um pedaco; UI deve garantir consistencia."""
    pass


class CompanyBenefitResponse(BaseModel):
    """Response com 24 colunas (22 Rails + icon + timestamps)."""
    id: str
    company_id: str

    name: str
    category: str | None = None
    description: str | None = None
    icon: str | None = None

    value: float | None = None
    percentage_value: float | None = None
    value_type: str | None = None
    value_details: str | None = None

    applicable_to: list[str] = Field(default_factory=list)
    seniority_levels: list[str] = Field(default_factory=list)
    contract_types: list[str] = Field(default_factory=list)
    departments: dict[str, Any] = Field(default_factory=dict)

    waiting_period_days: int | None = None
    is_mandatory: bool = False
    is_active: bool = True
    is_highlighted: bool = False
    is_discount: bool = False

    order: int = 0

    provider: str | None = None
    provider_contact: str | None = None

    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


def _to_response(b) -> CompanyBenefitResponse:
    return CompanyBenefitResponse(
        id=str(b.id),
        company_id=b.company_id,
        name=b.name,
        category=b.category,
        description=b.description,
        icon=b.icon,
        value=b.value,
        percentage_value=getattr(b, "percentage_value", None),
        value_type=b.value_type,
        value_details=getattr(b, "value_details", None),
        applicable_to=getattr(b, "applicable_to", None) or [],
        seniority_levels=getattr(b, "seniority_levels", None) or [],
        contract_types=getattr(b, "contract_types", None) or [],
        departments=getattr(b, "departments", None) or {},
        waiting_period_days=getattr(b, "waiting_period_days", None),
        is_mandatory=getattr(b, "is_mandatory", False) or False,
        is_active=b.is_active,
        is_highlighted=b.is_highlighted,
        is_discount=getattr(b, "is_discount", False) or False,
        order=b.order or 0,
        provider=getattr(b, "provider", None),
        provider_contact=getattr(b, "provider_contact", None),
        created_at=b.created_at.isoformat() if b.created_at else None,
        updated_at=b.updated_at.isoformat() if b.updated_at else None,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[CompanyBenefitResponse])
async def list_company_benefits(
    company_id: str | None = Query(None),
    category: str | None = Query(None),
    active_only: bool = Query(True),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """List company benefits."""
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        validate_company_access(current_user, effective_company_id)
        repo = CompanyBenefitRepository(db)
        benefits = await repo.list_for_company(
            effective_company_id,
            active_only=active_only,
            category=category,
            search=search,
        )
        return [_to_response(b) for b in benefits]
    except Exception as e:
        logger.error(f"Error listing company benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CompanyBenefitResponse)
async def create_company_benefit(
    benefit: CompanyBenefitCreate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Create a new company benefit."""
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        validate_company_access(current_user, effective_company_id)
        repo = CompanyBenefitRepository(db)
        new_benefit = await repo.create(effective_company_id, benefit.model_dump())
        logger.info(f"Created company benefit: {new_benefit.name} for company: {effective_company_id}")
        return _to_response(new_benefit)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{benefit_id}", response_model=CompanyBenefitResponse)
async def get_company_benefit(
    benefit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Get a specific company benefit by ID."""
    try:
        repo = CompanyBenefitRepository(db)
        benefit = await repo.get_by_id(benefit_id)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        validate_company_access(current_user, benefit.company_id)
        return _to_response(benefit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{benefit_id}", response_model=CompanyBenefitResponse)
async def update_company_benefit(
    benefit_id: UUID,
    updates: CompanyBenefitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Update a company benefit."""
    try:
        repo = CompanyBenefitRepository(db)
        benefit = await repo.get_by_id(benefit_id)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        validate_company_access(current_user, benefit.company_id)
        benefit = await repo.update(benefit, updates.model_dump(exclude_unset=True))
        logger.info(f"Updated company benefit: {benefit.name}")
        return _to_response(benefit)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{benefit_id}", response_model=None)
async def delete_company_benefit(
    benefit_id: UUID,
    hard_delete: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Delete a company benefit (soft delete by default)."""
    try:
        repo = CompanyBenefitRepository(db)
        benefit = await repo.get_by_id(benefit_id)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        validate_company_access(current_user, benefit.company_id)
        if hard_delete:
            await repo.hard_delete(benefit)
            message = f"Benefit '{benefit.name}' permanently deleted"
        else:
            await repo.soft_delete(benefit)
            message = f"Benefit '{benefit.name}' deactivated"
        logger.info(f"  {message}")
        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-defaults", response_model=None)
async def seed_default_benefits(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Seed default Brazilian benefits for a company."""
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        validate_company_access(current_user, effective_company_id)
        repo = CompanyBenefitRepository(db)
        existing_count = await repo.count_for_company(effective_company_id)
        if existing_count > 0:
            return {
                "success": True,
                "message": f"Benefits already exist for company ({existing_count} benefits)",
                "created": 0,
                "total": existing_count,
            }
        created_count = await repo.seed_defaults(effective_company_id)
        logger.info(f"Seeded {created_count} default benefits for company: {effective_company_id}")
        return {
            "success": True,
            "message": f"Successfully seeded {created_count} default benefits",
            "created": created_count,
            "total": created_count,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding default benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list", response_model=None)
async def list_benefit_categories():
    """List available benefit categories."""
    return [
        {"id": "health", "name": "Saúde", "icon": "🏥"},
        {"id": "food", "name": "Alimentação", "icon": "🍽️"},
        {"id": "transport", "name": "Transporte", "icon": "🚌"},
        {"id": "education", "name": "Educação", "icon": "📚"},
        {"id": "wellness", "name": "Bem-estar", "icon": "💪"},
        {"id": "financial", "name": "Financeiro", "icon": "💰"},
        {"id": "family", "name": "Família", "icon": "👨‍👩‍👧"},
        {"id": "flexibility", "name": "Flexibilidade", "icon": "⏰"},
        {"id": "other", "name": "Outros", "icon": "📦"},
    ]
