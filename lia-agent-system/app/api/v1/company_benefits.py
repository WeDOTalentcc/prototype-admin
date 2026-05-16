"""
Company Benefits API endpoints.
CRUD operations for company-specific benefits management.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.domains.company.repositories.company_benefit_repository import (
    CompanyBenefitRepository,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

router = APIRouter(prefix="/company/benefits", tags=["company-benefits"])
logger = logging.getLogger(__name__)


# Protected eligibility terms (LGPD + CLAUDE.md Fairness non-negotiable rule)
PROHIBITED_ELIGIBILITY_TERMS: frozenset[str] = frozenset({
    # PT-BR
    "genero", "gênero", "sexo", "feminino", "masculino", "homem", "mulher",
    "raca", "raça", "etnia", "cor", "negro", "branco", "pardo",
    "idade", "jovem", "idoso", "velho", "anos",
    "religiao", "religião", "catolico", "evangelico", "judeu", "muçulmano",
    "estado_civil", "casado", "solteiro", "divorciado",
    "saude", "saúde", "deficiencia", "deficiência", "gestante", "gravida",
    "grávida",
    # EN
    "gender", "sex", "male", "female",
    "race", "ethnicity", "color",
    "age", "young", "old", "senior_citizen",
    "religion", "religious",
    "marital", "married", "single",
    "health", "disability", "pregnancy", "pregnant",
})


def _check_fairness_eligibility(field_name: str, value) -> None:
    """Raise ValueError when a protected term appears in an eligibility field.

    Error messages are LLM-optimised: they name the problem and remediation.
    """
    if value is None:
        return
    if isinstance(value, (list, tuple, set)):
        terms = {str(v).lower() for v in value}
    elif isinstance(value, dict):
        terms = {str(k).lower() for k in value}
    else:
        terms = {str(value).lower()}
    hits = terms & PROHIBITED_ELIGIBILITY_TERMS
    if hits:
        raise ValueError(
            f"FAIRNESS VIOLATION: campo '{field_name}' contém termos discriminatórios "
            f"{sorted(hits)}. Benefícios não podem ter elegibilidade por atributo protegido "
            f"(LGPD Art. 11, CLAUDE.md #2/#3). Remova os termos e use critérios neutros "
            f"como cargo, nível seniority canonical, ou tipo de contrato."
        )


class CompanyBenefitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str | None = None
    description: str | None = None
    icon: str | None = None

    # Monetary / value fields
    value: float | None = None
    percentage_value: float | None = None
    value_type: str | None = "informative"
    value_details: str | None = None

    # Eligibility scoping
    applicable_to: list | None = None
    seniority_levels: list | None = None
    contract_types: list | None = None
    departments: dict | list | None = None

    # Provider
    provider: str | None = None
    provider_contact: str | None = None

    # Scheduling
    waiting_period_days: int | None = None

    # Flags
    is_mandatory: bool = False
    is_discount: bool = False
    is_active: bool = True
    is_highlighted: bool = False
    order: int = 0

    from pydantic import model_validator

    @model_validator(mode="after")
    def validate_value_by_type(self) -> "CompanyBenefitCreate":
        """Conditional value validation by value_type (harness sensor)."""
        vt = self.value_type or "informative"
        if vt == "monetary" and self.value is None:
            raise ValueError(
                "INVALID: value_type='monetary' exige o campo 'value' (valor numérico). "
                "Defina value=<float> ou mude value_type para 'informative'."
            )
        if vt == "percentage" and self.percentage_value is None:
            raise ValueError(
                "INVALID: value_type='percentage' exige o campo 'percentage_value'. "
                "Defina percentage_value=<float> ou mude value_type."
            )
        if vt == "informative" and self.value_details is None and self.description is None:
            raise ValueError(
                "INVALID: value_type='informative' exige 'value_details' ou 'description'. "
                "Adicione uma descrição textual do benefício."
            )
        return self

    @model_validator(mode="after")
    def validate_fairness_eligibility(self) -> "CompanyBenefitCreate":
        """LGPD + Fairness non-negotiable (CLAUDE.md #2/#3): no protected terms."""
        _check_fairness_eligibility("applicable_to", self.applicable_to)
        _check_fairness_eligibility("seniority_levels", self.seniority_levels)
        _check_fairness_eligibility("contract_types", self.contract_types)
        _check_fairness_eligibility("departments", self.departments)
        return self


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
    percentage_value: float | None = None
    value_type: str | None = None
    value_details: str | None = None
    applicable_to: str | None = None
    seniority_levels: str | None = None
    contract_types: str | None = None
    departments: str | None = None
    is_active: bool = True
    is_highlighted: bool = False
    order: int = 0
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
        applicable_to=getattr(b, "applicable_to", None),
        seniority_levels=getattr(b, "seniority_levels", None),
        contract_types=getattr(b, "contract_types", None),
        departments=getattr(b, "departments", None),
        is_active=b.is_active,
        is_highlighted=b.is_highlighted,
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
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
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


@router.post("/", response_model=CompanyBenefitResponse)
async def create_company_benefit(
    benefit: CompanyBenefitCreate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    """Create a new company benefit."""
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        repo = CompanyBenefitRepository(db)
        new_benefit = await repo.create(effective_company_id, benefit.model_dump())
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created company benefit: {new_benefit.name} for company: {effective_company_id}")
        return _to_response(new_benefit)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating company benefit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=list[CompanyBenefitResponse])
async def list_active_company_benefits(
    company_id: str | None = Query(None),
    seniority_level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    """List only active benefits for a company.

    Canonical replacement for the legacy `/company/benefits/active` endpoint
    that lived in `company_benefits_api.py` (deleted in T2 / task #989).
    Must stay registered BEFORE `/{benefit_id}` to avoid the path being
    matched as a UUID lookup (regression bug B11).
    """
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        if not effective_company_id or effective_company_id in ("default", "unknown"):
            return []
        repo = CompanyBenefitRepository(db)
        benefits = await repo.list_for_company(effective_company_id, active_only=True)
        if seniority_level and seniority_level != "all":
            benefits = [
                b for b in benefits
                if not b.seniority_levels
                or "all" in (b.seniority_levels or "")
                or seniority_level in (b.seniority_levels or "")
            ]
        return [_to_response(b) for b in benefits]
    except Exception as e:
        logger.error(f"Error listing active company benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/highlighted", response_model=list[CompanyBenefitResponse])
async def list_highlighted_company_benefits(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    """List highlighted (and active) benefits for a company.

    Canonical replacement for legacy `/company/benefits/highlighted`. Must
    stay declared BEFORE `/{benefit_id}` (route order).
    """
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        if not effective_company_id or effective_company_id in ("default", "unknown"):
            return []
        repo = CompanyBenefitRepository(db)
        benefits = await repo.list_for_company(effective_company_id, active_only=True)
        return [_to_response(b) for b in benefits if b.is_highlighted]
    except Exception as e:
        logger.error(f"Error listing highlighted company benefits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=None)
async def get_company_benefits_summary(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    """Get an AI-agent-friendly summary of company benefits.

    Canonical replacement for legacy `/company/benefits/summary` from
    `company_benefits_api.py`. Returns counts, categories, formatted_text
    and a flat benefits list (untyped dict — same shape as the legacy
    `BenefitsSummaryResponse`). Must stay declared BEFORE `/{benefit_id}`.
    """
    empty = {
        "total_count": 0,
        "active_count": 0,
        "highlighted_count": 0,
        "categories": {},
        "formatted_text": "",
        "benefits": [],
    }
    try:
        effective_company_id = company_id or get_user_company_id(current_user)
        if not effective_company_id or effective_company_id in ("default", "unknown"):
            logger.warning(
                "get_company_benefits_summary called without valid company_id "
                "— returning empty summary"
            )
            return empty
        repo = CompanyBenefitRepository(db)
        all_benefits = await repo.list_for_company(effective_company_id, active_only=False)
        active_benefits = [b for b in all_benefits if b.is_active]
        highlighted_benefits = [b for b in active_benefits if b.is_highlighted]

        category_names = {
            "health": "Saúde & Bem-estar",
            "food": "Alimentação",
            "transport": "Transporte",
            "education": "Educação & Desenvolvimento",
            "financial": "Financeiro",
            "wellness": "Bem-estar",
            "family": "Família",
            "flexibility": "Flexibilidade",
            "other": "Outros",
        }
        categories: dict = {}
        for b in active_benefits:
            cat = b.category or "other"
            if cat not in categories:
                categories[cat] = {"name": category_names.get(cat, cat), "count": 0, "benefits": []}
            categories[cat]["count"] += 1
            categories[cat]["benefits"].append({
                "name": b.name,
                "description": b.description,
                "value_type": b.value_type,
                "value": b.value,
                "percentage_value": b.percentage_value,
                "is_highlighted": b.is_highlighted,
            })

        formatted_lines = ["**Benefícios da Empresa:**"]
        for cat_data in categories.values():
            items = []
            for b in cat_data["benefits"]:
                if b["value_type"] == "monetary" and b["value"]:
                    items.append(f'{b["name"]} (R$ {b["value"]:,.2f})')
                elif b["value_type"] == "percentage" and b["percentage_value"]:
                    items.append(f'{b["name"]} ({b["percentage_value"]}%)')
                else:
                    items.append(b["name"])
            if items:
                formatted_lines.append(f"- {cat_data['name']}: {', '.join(items)}")
        formatted_text = (
            "\n".join(formatted_lines) if len(formatted_lines) > 1 else "Nenhum benefício cadastrado."
        )
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
        return {
            "total_count": len(all_benefits),
            "active_count": len(active_benefits),
            "highlighted_count": len(highlighted_benefits),
            "categories": categories,
            "formatted_text": formatted_text,
            "benefits": benefits_list,
        }
    except Exception as e:
        logger.error(f"Error getting company benefits summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{benefit_id}", response_model=CompanyBenefitResponse)
async def get_company_benefit(
    benefit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update a company benefit."""
    try:
        repo = CompanyBenefitRepository(db)
        benefit = await repo.get_by_id(benefit_id)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        benefit = await repo.update(benefit, updates.model_dump(exclude_unset=True))
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
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
async def list_benefit_categories(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
