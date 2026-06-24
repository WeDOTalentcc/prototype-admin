"""
Offer Rules Settings — GET/PUT /company/offer-rules

Configurações N2/N3: dias de início permitidos, aviso prévio, negociação.
company_id sempre do JWT via Depends(require_company_id). NUNCA do payload.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.compliance.audit_service import AuditService
from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository
from app.domains.company.repositories.salary_band_repository import SalaryBandRepository
from app.domains.company.repositories.benefit_repository import BenefitRepository
from libs.models.lia_models.company_hiring_policy import OFFER_RULES_DEFAULTS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company", tags=["company"])

_MAX_NOTICE_DAYS = 365
_MAX_FLEX_PCT = 50
_MAX_ROUNDS = 10
_VALID_START_DAYS = set(range(1, 29))


class OfferRulesUpdate(WeDoBaseModel):
    allowed_start_day_of_month: list[int] | None = None
    onboarding_blackout_periods: list[dict] | None = None
    min_notice_days: int | None = None
    negotiation_enabled: bool | None = None
    salary_flex_pct_max: int | None = None
    benefits_flex_items: list[str] | None = None
    negotiation_hitl_threshold_pct: int | None = None
    counter_proposal_max_rounds: int | None = None

    @field_validator("allowed_start_day_of_month")
    @classmethod
    def valid_start_days(cls, v):
        if v is None:
            return v
        invalid = [d for d in v if d not in _VALID_START_DAYS]
        if invalid:
            raise ValueError(
                f"Dias de início inválidos: {invalid}. Use 1-28 para cobrir todos os meses."
            )
        return list(sorted(set(v)))

    @field_validator("min_notice_days")
    @classmethod
    def valid_notice_days(cls, v):
        if v is not None and (v < 0 or v > _MAX_NOTICE_DAYS):
            raise ValueError(f"min_notice_days deve estar entre 0 e {_MAX_NOTICE_DAYS}.")
        return v

    @field_validator("salary_flex_pct_max")
    @classmethod
    def valid_flex_pct(cls, v):
        if v is not None and (v < 0 or v > _MAX_FLEX_PCT):
            raise ValueError(f"salary_flex_pct_max deve estar entre 0 e {_MAX_FLEX_PCT}.")
        return v

    @field_validator("counter_proposal_max_rounds")
    @classmethod
    def valid_rounds(cls, v):
        if v is not None and (v < 0 or v > _MAX_ROUNDS):
            raise ValueError(f"counter_proposal_max_rounds deve estar entre 0 e {_MAX_ROUNDS}.")
        return v


class OfferRulesResponse(WeDoBaseModel):
    company_id: str
    offer_rules: dict


@router.get("/offer-rules", response_model=OfferRulesResponse)
async def get_offer_rules(
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    policy = await HiringPolicyRepository(db).get_by_company(company_id)
    rules = (policy.offer_rules if policy else None) or OFFER_RULES_DEFAULTS
    return {"company_id": company_id, "offer_rules": rules}


@router.put("/offer-rules", response_model=OfferRulesResponse)
async def update_offer_rules(
    payload: OfferRulesUpdate,
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    repo = HiringPolicyRepository(db)
    policy = await repo.get_by_company(company_id)

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Política de contratação não encontrada para esta empresa.",
        )

    current_rules = dict(policy.offer_rules or OFFER_RULES_DEFAULTS)
    updates = payload.model_dump(exclude_unset=True)
    current_rules.update(updates)

    await repo.update_offer_rules(company_id, current_rules)

    await AuditService.log_decision(
        db=db,
        company_id=company_id,
        action="offer_rules_update",
        entity_type="company_hiring_policy",
        entity_id=company_id,
        reasoning=[{"updated_keys": list(updates.keys())}],
    )

    await db.commit()
    logger.info("[offer_rules] updated company=%s keys=%s", company_id, list(updates.keys()))
    return {"company_id": company_id, "offer_rules": current_rules}


class OfferAgentReadinessItem(WeDoBaseModel):
    key: str
    label: str
    ok: bool
    settings_path: str


class OfferAgentReadinessResponse(WeDoBaseModel):
    score: int
    total: int
    ready: bool
    items: list[OfferAgentReadinessItem]


@router.get("/offer-agent/readiness", response_model=OfferAgentReadinessResponse)
async def get_offer_agent_readiness(
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Verifica se dados necessarios para o offer_concierge estao configurados.
    Retorna score + deep-links para config. Usado pelo Agent Studio pos-ativacao."""
    from uuid import UUID as _UUID

    policy = await HiringPolicyRepository(db).get_by_company(company_id)
    offer_rules = (policy.offer_rules if policy else None) or {}

    salary_count = await SalaryBandRepository(db).count_for_company(company_id)
    has_salary_bands = salary_count > 0

    has_negotiation_config = (
        offer_rules.get("negotiation_enabled", False) is True
        or offer_rules.get("salary_flex_pct_max", 0) > 0
    )

    try:
        benefits = await BenefitRepository(db).list_active_for_company(_UUID(company_id))
        has_benefits = len(benefits) > 0
    except Exception:
        has_benefits = False

    has_notice_days = offer_rules.get("min_notice_days", 0) >= 1

    items = [
        OfferAgentReadinessItem(
            key="salary_bands",
            label="Faixas salariais por nível",
            ok=has_salary_bands,
            settings_path="/configuracoes?hub=remuneracao",
        ),
        OfferAgentReadinessItem(
            key="negotiation_rules",
            label="Políticas de negociação de oferta",
            ok=has_negotiation_config,
            settings_path="/configuracoes?hub=contratacao",
        ),
        OfferAgentReadinessItem(
            key="benefits",
            label="Benefícios da empresa",
            ok=has_benefits,
            settings_path="/configuracoes?hub=beneficios",
        ),
        OfferAgentReadinessItem(
            key="notice_days",
            label="Prazo mínimo de aviso para início",
            ok=has_notice_days,
            settings_path="/configuracoes?hub=contratacao",
        ),
    ]

    score = sum(1 for i in items if i.ok)
    total = len(items)
    return OfferAgentReadinessResponse(score=score, total=total, ready=score == total, items=items)

