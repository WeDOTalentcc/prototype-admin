import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_account import ClientAccount
from app.models.billing import Subscription
from app.models.custom_agent import CustomAgent
from app.models.digital_twin import DigitalTwin
from app.models.recruitment_campaign import RecruitmentCampaign
# Sub-sprint 7B-3a (2026-05-25): SourcingAgent legacy import removed,
# sourcing count now reads CustomAgent.where(category=sourcing).

logger = logging.getLogger(__name__)

PLAN_AGENT_QUOTAS: dict[str, dict[str, int]] = {
    "starter": {
        "custom_agents": 2,
        "sourcing_agents": 1,
        "digital_twins": 0,
        "campaigns": 1,
    },
    "pro": {
        "custom_agents": 10,
        "sourcing_agents": 5,
        "digital_twins": 3,
        "campaigns": 5,
    },
    "business": {
        "custom_agents": 50,
        "sourcing_agents": 20,
        "digital_twins": 10,
        "campaigns": 20,
    },
    "enterprise": {
        "custom_agents": -1,
        "sourcing_agents": -1,
        "digital_twins": -1,
        "campaigns": -1,
    },
}

DEFAULT_QUOTAS = PLAN_AGENT_QUOTAS["starter"]


def _safe_uuid(value: str) -> UUID | None:
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        return None


async def _get_quotas_from_plan_config(plan_code: str, db: AsyncSession) -> dict[str, int] | None:
    """Fetch agent quotas from company_plan_configs table."""
    try:
        from lia_models.plan_config import CompanyPlanConfig

        result = await db.execute(
            select(
                CompanyPlanConfig.max_custom_agents,
                CompanyPlanConfig.max_sourcing_agents,
                CompanyPlanConfig.max_digital_twins,
                CompanyPlanConfig.max_campaigns,
            ).where(CompanyPlanConfig.plan_code == plan_code.lower().strip()).limit(1)
        )
        row = result.one_or_none()
        if row:
            return {
                "custom_agents": row[0],
                "sourcing_agents": row[1],
                "digital_twins": row[2],
                "campaigns": row[3],
            }
    except Exception as exc:
        logger.debug("[QUOTA] DB plan_config lookup failed for plan=%s: %s", plan_code, exc)
    return None


async def get_effective_quotas(company_id: str, db: AsyncSession) -> dict[str, int]:
    company_uuid = _safe_uuid(company_id)

    if company_uuid is None:
        return DEFAULT_QUOTAS.copy()

    sub_q = (
        select(Subscription.plan_code)
        .where(
            and_(
                Subscription.client_id == company_uuid,
                Subscription.status.in_(["active", "trialing"]),
            )
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    plan_code = (await db.execute(sub_q)).scalar_one_or_none()
    plan_key = (plan_code or "starter").lower().strip()

    # Fase 1.3: try DB (company_plan_configs) before hardcoded fallback
    db_quotas = await _get_quotas_from_plan_config(plan_key, db)
    quotas = db_quotas if db_quotas is not None else PLAN_AGENT_QUOTAS.get(plan_key, DEFAULT_QUOTAS).copy()
    if db_quotas is None:
        quotas = quotas.copy()

    # Per-company override from ClientAccount.settings (highest priority)
    client_result = await db.execute(
        select(ClientAccount).where(ClientAccount.id == company_uuid)
    )
    client = client_result.scalar_one_or_none()
    if client and client.settings and isinstance(client.settings, dict):
        overrides = client.settings.get("agent_quotas", {})
        if overrides:
            quotas.update(overrides)

    return quotas


async def get_current_count(
    resource_key: str, company_id: str, db: AsyncSession
) -> int:
    cid_str = str(company_id)

    if resource_key == "custom_agents":
        q = select(func.count(CustomAgent.id)).where(
            and_(
                CustomAgent.company_id == cid_str,
                CustomAgent.status != "archived",
            )
        )
    elif resource_key == "sourcing_agents":
        # 7B-3a canonical: count from CustomAgent filter category=sourcing.
        # Resource key string mantida pra back-compat pricing (decisão 7B-3b).
        q = select(func.count(CustomAgent.id)).where(
            and_(
                CustomAgent.company_id == cid_str,
                CustomAgent.category == "sourcing",
                CustomAgent.status != "archived",
            )
        )
    elif resource_key == "digital_twins":
        q = select(func.count(DigitalTwin.id)).where(
            DigitalTwin.company_id == cid_str
        )
    elif resource_key == "campaigns":
        q = select(func.count(RecruitmentCampaign.id)).where(
            and_(
                RecruitmentCampaign.company_id == cid_str,
                RecruitmentCampaign.status.in_(["draft", "active", "paused"]),
            )
        )
    else:
        return 0

    return (await db.execute(q)).scalar() or 0


async def enforce_quota(
    resource_key: str, company_id: str, db: AsyncSession
) -> None:
    quotas = await get_effective_quotas(company_id, db)
    limit = quotas.get(resource_key, 0)

    if limit == -1:
        return

    current = await get_current_count(resource_key, company_id, db)

    if current >= limit:
        label = resource_key.replace("_", " ")
        logger.warning(
            "[QUOTA] Denied creation of %s for company=%s (current=%d, limit=%d)",
            resource_key, company_id, current, limit,
        )
        raise HTTPException(
            status_code=403,
            detail=(
                f"Quota exceeded for {label}: "
                f"current usage {current}/{limit}. "
                f"Upgrade your plan or contact admin to increase quota."
            ),
        )


# === Sprint 7C / 7B-3b backlog (2026-05-26): max_agents_total alias canonical ===
# Decisão Paulo: soma transparente como ALIAS, não refactor breaking.
# PRESERVA PLAN_AGENT_QUOTAS 4 categorias + admin_external contract.
# Apenas adiciona views computed pra UI sidebar consumir "X/Y agentes" unified.

_AGENT_CATEGORY_KEYS = (
    "sourcing_agents",
    "custom_agents",
    "digital_twins",
    "campaigns",
)


def get_max_agents_total(plan: str) -> int:
    """Soma 4 categorias agent (sourcing + custom + digital_twins + campaigns).

    -1 (ilimitado) em qualquer categoria -> -1 result (propaga ilimitado).
    Plano desconhecido -> 0.

    Sprint 7C / 7B-3b backlog: alias unified pra UI sidebar/badges.
    NÃO substitui PLAN_AGENT_QUOTAS dict (admin_external + per-category
    enforce_quota continuam canonical).
    """
    quota = PLAN_AGENT_QUOTAS.get((plan or "").lower().strip())
    if not quota:
        return 0
    values = [quota.get(field, 0) for field in _AGENT_CATEGORY_KEYS]
    if -1 in values:
        return -1
    return sum(values)


async def get_current_agents_total(company_id: str, db: AsyncSession) -> int:
    """Soma current count das 4 categorias agent canonical.

    Reusa get_current_count per resource pra single source of truth
    (filtros de status: status != archived, campaigns ativas, etc).
    """
    total = 0
    for resource_key in _AGENT_CATEGORY_KEYS:
        total += await get_current_count(resource_key, company_id, db)
    return total
