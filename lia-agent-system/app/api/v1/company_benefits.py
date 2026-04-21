"""
Company Benefits API endpoints.
CRUD operations for company-specific benefits management.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.domains.company.repositories.company_benefit_repository import (
    CompanyBenefitRepository,
)

router = APIRouter(prefix="/company/benefits", tags=["company-benefits"])
logger = logging.getLogger(__name__)


class CompanyBenefitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str | None = None
    description: str | None = None
    icon: str | None = None
    provider: str | None = None
    value: float | None = None
    value_type: str | None = "informative"
    percentage_value: float | None = None
    value_details: str | None = None
    seniority_levels: list[str] | None = None
    waiting_period_days: int = 0
    is_highlighted: bool = False
    is_mandatory: bool = False
    is_discount: bool = False
    is_active: bool = True
    order: int = 0


class CompanyBenefitUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    icon: str | None = None
    provider: str | None = None
    value: float | None = None
    value_type: str | None = None
    percentage_value: float | None = None
    value_details: str | None = None
    seniority_levels: list[str] | None = None
    waiting_period_days: int | None = None
    is_active: bool | None = None
    is_highlighted: bool | None = None
    is_mandatory: bool | None = None
    is_discount: bool | None = None
    order: int | None = None


class CompanyBenefitResponse(BaseModel):
    id: str
    company_id: str
    name: str
    category: str | None = None
    description: str | None = None
    icon: str | None = None
    provider: str | None = None
    value: float | None = None
    value_type: str | None = None
    percentage_value: float | None = None
    value_details: str | None = None
    seniority_levels: list[str] = Field(default_factory=lambda: ["all"])
    waiting_period_days: int = 0
    is_active: bool = True
    is_highlighted: bool = False
    is_mandatory: bool = False
    is_discount: bool = False
    order: int = 0
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


def _to_response(b) -> CompanyBenefitResponse:
    seniority = b.seniority_levels if b.seniority_levels else ["all"]
    if not isinstance(seniority, list):
        seniority = ["all"]
    return CompanyBenefitResponse(
        id=str(b.id),
        company_id=b.company_id,
        name=b.name,
        category=b.category,
        description=b.description,
        icon=b.icon,
        provider=b.provider,
        value=b.value,
        value_type=b.value_type,
        percentage_value=b.percentage_value,
        value_details=b.value_details,
        seniority_levels=seniority,
        waiting_period_days=b.waiting_period_days or 0,
        is_active=b.is_active,
        is_highlighted=b.is_highlighted,
        is_mandatory=bool(getattr(b, "is_mandatory", False)),
        is_discount=bool(getattr(b, "is_discount", False)),
        order=b.order,
        created_at=b.created_at.isoformat() if b.created_at else None,
        updated_at=b.updated_at.isoformat() if b.updated_at else None,
    )


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


@router.get("/active", response_model=list[CompanyBenefitResponse])
async def list_active_company_benefits(
    company_id: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """List only active company benefits (convenience endpoint used by FE hook)."""
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        repo = CompanyBenefitRepository(db)
        benefits = await repo.list_for_company(
            effective_company_id,
            active_only=True,
            category=category,
            search=search,
        )
        return [_to_response(b) for b in benefits]
    except Exception as e:
        logger.error(f"Error listing active company benefits: {e}")
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
    """List available benefit categories (canonical enum shared with FE).

    Keep this list in sync with `plataforma-lia/src/types/benefits.ts`
    (`BenefitCategory`) and the `BENEFIT_CATEGORIES` constants in the
    settings components.
    """
    return [
        {"id": "health", "name": "Saúde & Bem-estar", "icon": "🏥"},
        {"id": "food", "name": "Alimentação", "icon": "🍽️"},
        {"id": "transport", "name": "Transporte", "icon": "🚌"},
        {"id": "education", "name": "Educação & Desenvolvimento", "icon": "📚"},
        {"id": "wellness", "name": "Bem-estar", "icon": "💪"},
        {"id": "financial", "name": "Financeiro", "icon": "💰"},
        {"id": "quality_life", "name": "Qualidade de Vida", "icon": "🏡"},
        {"id": "family", "name": "Família", "icon": "👨\u200d👩\u200d👧"},
        {"id": "flexibility", "name": "Flexibilidade", "icon": "⏰"},
        {"id": "security", "name": "Segurança", "icon": "🛡️"},
        {"id": "other", "name": "Outros", "icon": "📦"},
    ]
