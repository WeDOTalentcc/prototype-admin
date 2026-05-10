"""
Company Benefits API endpoints (Benefit domain — read/write via BenefitRepository).

Handles listing, creating, updating, deleting, and summarising benefits attached
to a company profile.  These routes use the `Benefit` model / `BenefitRepository`
and are separate from the `CompanyBenefit`-based CRUD in company_benefits.py.
"""
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.domains.company.dependencies import get_benefit_repo
from app.domains.company.repositories.benefit_repository import BenefitRepository
from app.schemas.company import (
    BenefitCreate,
    BenefitResponse,
    BenefitUpdate,
    BenefitsSummaryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


@router.get("/benefits", response_model=list[BenefitResponse])
async def list_benefits(
    company_id: str | None = Query(None),
    category: str | None = Query(None),
    include_inactive: bool = Query(False),
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
):
    """List all benefits for a company."""
    try:
        if not company_id or company_id in ("default", "unknown"):
            logger.warning("list_benefits called without valid company_id — returning empty list to prevent cross-tenant data leak")
            return []

        try:
            company_uuid = uuid.UUID(company_id)
        except ValueError:
            logger.warning(f"list_benefits: invalid company_id format '{company_id}' — returning empty list")
            return []

        benefits = await benefit_repo.list_for_company(company_uuid)
        if category:
            benefits = [b for b in benefits if b.category == category]
        if not include_inactive:
            benefits = [b for b in benefits if b.is_active]
        benefits.sort(key=lambda b: (b.category or "", b.order or 0))
        return benefits
    except Exception as e:
        logger.error(f"Error listing benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benefits", response_model=BenefitResponse)
async def create_benefit(
    company_id: str,
    data: BenefitCreate,
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
):
    """Create a new benefit."""
    try:
        if not company_id or company_id in ("default", "unknown"):
            raise HTTPException(status_code=400, detail="Valid company_id is required to create a benefit")

        try:
            resolved_company_id = uuid.UUID(company_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid company_id format: {company_id}")

        benefit = await benefit_repo.create({"company_id": resolved_company_id, **data.model_dump()})
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created benefit: {benefit.name}")
        return benefit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/benefits/{benefit_id}", response_model=BenefitResponse)
async def update_benefit(
    benefit_id: uuid.UUID,
    data: BenefitUpdate,
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
):
    """Update a benefit."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        benefit = await benefit_repo.update(benefit_id, update_data)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        return benefit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/benefits/{benefit_id}", response_model=None)
async def delete_benefit(
    benefit_id: uuid.UUID,
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
):
    """Soft delete a benefit."""
    try:
        deleted = await benefit_repo.delete(benefit_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Benefit not found")
        return {"success": True, "message": "Benefit deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benefits/active", response_model=list[BenefitResponse])
async def list_active_benefits(
    company_id: str | None = Query(None),
    seniority_level: str | None = Query(None),
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
):
    """List only active benefits for a company."""
    try:
        if not company_id or company_id in ("default", "unknown"):
            return []

        try:
            company_uuid = uuid.UUID(company_id)
        except ValueError:
            return []

        benefits = await benefit_repo.list_for_company(company_uuid)
        benefits = [b for b in benefits if b.is_active]

        if seniority_level:
            benefits = [
                b for b in benefits
                if not b.seniority_levels
                or "all" in (b.seniority_levels or [])
                or seniority_level in (b.seniority_levels or [])
            ]

        return benefits
    except Exception as e:
        logger.error(f"Error listing active benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benefits/highlighted", response_model=list[BenefitResponse])
async def list_highlighted_benefits(
    company_id: str | None = Query(None),
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
):
    """List highlighted benefits for a company."""
    try:
        if not company_id or company_id in ("default", "unknown"):
            return []

        try:
            company_uuid = uuid.UUID(company_id)
        except ValueError:
            return []

        benefits = await benefit_repo.list_for_company(company_uuid)
        return [b for b in benefits if b.is_active and b.is_highlighted]
    except Exception as e:
        logger.error(f"Error listing highlighted benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benefits/summary", response_model=BenefitsSummaryResponse)
async def get_benefits_summary(
    company_id: str | None = Query(None),
    benefit_repo: BenefitRepository = Depends(get_benefit_repo),
):
    """Get a summary of company benefits for AI agents."""
    try:
        if not company_id or company_id in ("default", "unknown"):
            logger.warning("get_benefits_summary called without valid company_id — returning empty summary")
            return {"total_count": 0, "active_count": 0, "highlighted_count": 0, "categories": {}, "formatted_text": "", "benefits": []}

        try:
            company_uuid = uuid.UUID(company_id)
        except ValueError:
            logger.warning(f"get_benefits_summary: invalid company_id format '{company_id}'")
            return {"total_count": 0, "active_count": 0, "highlighted_count": 0, "categories": {}, "formatted_text": "", "benefits": []}

        all_benefits = await benefit_repo.list_for_company(company_uuid)
        active_benefits = [b for b in all_benefits if b.is_active]
        highlighted_benefits = [b for b in active_benefits if b.is_highlighted]

        CATEGORY_NAMES = {
            "health": "Saúde & Bem-estar",
            "food": "Alimentação",
            "transport": "Transporte",
            "education": "Educação & Desenvolvimento",
            "financial": "Financeiro",
            "quality_life": "Qualidade de Vida",
            "family": "Família",
            "security": "Segurança",
        }

        categories = {}
        for benefit in active_benefits:
            cat = benefit.category or "other"
            if cat not in categories:
                categories[cat] = {"name": CATEGORY_NAMES.get(cat, cat), "count": 0, "benefits": []}
            categories[cat]["count"] += 1
            categories[cat]["benefits"].append({
                "name": benefit.name,
                "description": benefit.description,
                "value_type": benefit.value_type,
                "value": benefit.value,
                "percentage_value": benefit.percentage_value,
                "is_highlighted": benefit.is_highlighted,
            })

        formatted_lines = ["**Benefícios da Empresa:**"]
        for cat_id, cat_data in categories.items():
            cat_benefits = []
            for b in cat_data["benefits"]:
                if b["value_type"] == "monetary" and b["value"]:
                    cat_benefits.append(f'{b["name"]} (R$ {b["value"]:,.2f})')
                elif b["value_type"] == "percentage" and b["percentage_value"]:
                    cat_benefits.append(f'{b["name"]} ({b["percentage_value"]}%)')
                else:
                    cat_benefits.append(b["name"])
            if cat_benefits:
                formatted_lines.append(f"- {cat_data['name']}: {', '.join(cat_benefits)}")

        formatted_text = "\n".join(formatted_lines) if len(formatted_lines) > 1 else "Nenhum benefício cadastrado."

        benefits_list = [
            {
                "id": str(b.id),
                "name": b.name,
                "description": b.description,
                "category": b.category,
                "value_type": b.value_type,
                "value": b.value,
                "percentage_value": b.percentage_value,
                "is_highlighted": b.is_highlighted,
            }
            for b in active_benefits
        ]

        return BenefitsSummaryResponse(
            total_count=len(all_benefits),
            active_count=len(active_benefits),
            highlighted_count=len(highlighted_benefits),
            categories=categories,
            formatted_text=formatted_text,
            benefits=benefits_list,
        )
    except Exception as e:
        logger.error(f"Error getting benefits summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
