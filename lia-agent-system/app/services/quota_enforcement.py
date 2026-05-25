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
    quotas = PLAN_AGENT_QUOTAS.get(plan_key, DEFAULT_QUOTAS).copy()

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
