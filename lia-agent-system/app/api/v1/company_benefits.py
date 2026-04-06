"""
Company Benefits API endpoints.
CRUD operations for company-specific benefits management.
"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.models.company_benefit import DEFAULT_BRAZILIAN_BENEFITS, CompanyBenefit

router = APIRouter(prefix="/company/benefits", tags=["company-benefits"])
logger = logging.getLogger(__name__)


class CompanyBenefitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str | None = None
    description: str | None = None
    icon: str | None = None
    value: float | None = None
    value_type: str | None = "informative"
    is_highlighted: bool = False
    order: int = 0


class CompanyBenefitUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    icon: str | None = None
    value: float | None = None
    value_type: str | None = None
    is_active: bool | None = None
    is_highlighted: bool | None = None
    order: int | None = None


class CompanyBenefitResponse(BaseModel):
    id: str
    company_id: str
    name: str
    category: str | None = None
    description: str | None = None
    icon: str | None = None
    value: float | None = None
    value_type: str | None = None
    is_active: bool = True
    is_highlighted: bool = False
    order: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=list[CompanyBenefitResponse])
async def list_company_benefits(
    company_id: str | None = Query(None, description="Filter by company ID"),
    category: str | None = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Return only active benefits"),
    search: str | None = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    List company benefits.
    Returns benefits for the specified company or the current user's company.
    """
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        
        query = select(CompanyBenefit).where(CompanyBenefit.company_id == effective_company_id)
        
        if active_only:
            query = query.where(CompanyBenefit.is_active)
        
        if category:
            query = query.where(CompanyBenefit.category == category)
        
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(CompanyBenefit.name).like(search_term),
                    func.lower(CompanyBenefit.description).like(search_term)
                )
            )
        
        query = query.order_by(CompanyBenefit.order, CompanyBenefit.name)
        
        result = await db.execute(query)
        benefits = result.scalars().all()
        
        return [
            CompanyBenefitResponse(
                id=str(b.id),
                company_id=b.company_id,
                name=b.name,
                category=b.category,
                description=b.description,
                icon=b.icon,
                value=b.value,
                value_type=b.value_type,
                is_active=b.is_active,
                is_highlighted=b.is_highlighted,
                order=b.order,
                created_at=b.created_at.isoformat() if b.created_at else None,
                updated_at=b.updated_at.isoformat() if b.updated_at else None
            )
            for b in benefits
        ]
        
    except Exception as e:
        logger.error(f"Error listing company benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CompanyBenefitResponse)
async def create_company_benefit(
    benefit: CompanyBenefitCreate,
    company_id: str | None = Query(None, description="Company ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Create a new company benefit.
    """
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        
        new_benefit = CompanyBenefit(
            company_id=effective_company_id,
            name=benefit.name,
            category=benefit.category,
            description=benefit.description,
            icon=benefit.icon,
            value=benefit.value,
            value_type=benefit.value_type,
            is_highlighted=benefit.is_highlighted,
            order=benefit.order
        )
        
        db.add(new_benefit)
        await db.commit()
        await db.refresh(new_benefit)
        
        logger.info(f"✅ Created company benefit: {new_benefit.name} for company: {effective_company_id}")
        
        return CompanyBenefitResponse(
            id=str(new_benefit.id),
            company_id=new_benefit.company_id,
            name=new_benefit.name,
            category=new_benefit.category,
            description=new_benefit.description,
            icon=new_benefit.icon,
            value=new_benefit.value,
            value_type=new_benefit.value_type,
            is_active=new_benefit.is_active,
            is_highlighted=new_benefit.is_highlighted,
            order=new_benefit.order,
            created_at=new_benefit.created_at.isoformat() if new_benefit.created_at else None,
            updated_at=new_benefit.updated_at.isoformat() if new_benefit.updated_at else None
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{benefit_id}", response_model=CompanyBenefitResponse)
async def get_company_benefit(
    benefit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get a specific company benefit by ID.
    """
    try:
        result = await db.execute(
            select(CompanyBenefit).where(CompanyBenefit.id == benefit_id)
        )
        benefit = result.scalar_one_or_none()
        
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        
        return CompanyBenefitResponse(
            id=str(benefit.id),
            company_id=benefit.company_id,
            name=benefit.name,
            category=benefit.category,
            description=benefit.description,
            icon=benefit.icon,
            value=benefit.value,
            value_type=benefit.value_type,
            is_active=benefit.is_active,
            is_highlighted=benefit.is_highlighted,
            order=benefit.order,
            created_at=benefit.created_at.isoformat() if benefit.created_at else None,
            updated_at=benefit.updated_at.isoformat() if benefit.updated_at else None
        )
        
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
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Update a company benefit.
    """
    try:
        result = await db.execute(
            select(CompanyBenefit).where(CompanyBenefit.id == benefit_id)
        )
        benefit = result.scalar_one_or_none()
        
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        
        update_data = updates.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        for key, value in update_data.items():
            setattr(benefit, key, value)
        
        await db.commit()
        await db.refresh(benefit)
        
        logger.info(f"✅ Updated company benefit: {benefit.name}")
        
        return CompanyBenefitResponse(
            id=str(benefit.id),
            company_id=benefit.company_id,
            name=benefit.name,
            category=benefit.category,
            description=benefit.description,
            icon=benefit.icon,
            value=benefit.value,
            value_type=benefit.value_type,
            is_active=benefit.is_active,
            is_highlighted=benefit.is_highlighted,
            order=benefit.order,
            created_at=benefit.created_at.isoformat() if benefit.created_at else None,
            updated_at=benefit.updated_at.isoformat() if benefit.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{benefit_id}", response_model=None)
async def delete_company_benefit(
    benefit_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Delete a company benefit (soft delete by default).
    """
    try:
        result = await db.execute(
            select(CompanyBenefit).where(CompanyBenefit.id == benefit_id)
        )
        benefit = result.scalar_one_or_none()
        
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        
        if hard_delete:
            await db.delete(benefit)
            message = f"Benefit '{benefit.name}' permanently deleted"
        else:
            benefit.is_active = False
            benefit.updated_at = datetime.utcnow()
            message = f"Benefit '{benefit.name}' deactivated"
        
        await db.commit()
        
        logger.info(f"✅ {message}")
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-defaults", response_model=None)
async def seed_default_benefits(
    company_id: str | None = Query(None, description="Company ID to seed benefits for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Seed default Brazilian benefits for a company.
    Only adds benefits that don't already exist (by name).
    """
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        
        result = await db.execute(
            select(func.count(CompanyBenefit.id)).where(
                CompanyBenefit.company_id == effective_company_id
            )
        )
        existing_count = result.scalar() or 0
        
        if existing_count > 0:
            return {
                "success": True,
                "message": f"Benefits already exist for company ({existing_count} benefits)",
                "created": 0,
                "total": existing_count
            }
        
        created_count = 0
        for benefit_data in DEFAULT_BRAZILIAN_BENEFITS:
            existing = await db.execute(
                select(CompanyBenefit).where(
                    CompanyBenefit.company_id == effective_company_id,
                    CompanyBenefit.name == benefit_data["name"]
                )
            )
            if not existing.scalar_one_or_none():
                benefit = CompanyBenefit(
                    company_id=effective_company_id,
                    **benefit_data
                )
                db.add(benefit)
                created_count += 1
        
        await db.commit()
        
        logger.info(f"✅ Seeded {created_count} default benefits for company: {effective_company_id}")
        
        return {
            "success": True,
            "message": f"Successfully seeded {created_count} default benefits",
            "created": created_count,
            "total": len(DEFAULT_BRAZILIAN_BENEFITS)
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding default benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list", response_model=None)
async def list_benefit_categories():
    """
    List available benefit categories.
    """
    categories = [
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
    return categories
