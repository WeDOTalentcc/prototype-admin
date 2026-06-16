"""
Admin External Panel API Endpoints.

Provides endpoints for the external admin panel to manage tenants,
view studio agents, consumption breakdown, and agent quotas.

Authentication: JWT Bearer token validated via ``require_admin`` dependency.
The ``X-Company-ID`` header is used for audit/context only.

Endpoints:
  GET  /api/v1/admin/companies                              — list all tenants
  GET  /api/v1/admin/companies/{company_id}/overview         — consolidated tenant view
  GET  /api/v1/admin/agents/studio/{company_id}              — studio agents for tenant
  GET  /api/v1/admin/agents/studio/{company_id}/consumption  — core vs studio consumption
  GET  /api/v1/admin/agents/quota/{company_id}               — agent quotas by plan
  PUT  /api/v1/admin/agents/quota/{company_id}               — adjust agent quotas
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.core.database import get_db
from app.shared.admin.cross_tenant_session import (
    cross_tenant_session,
    require_superadmin,
)
from app.models.ai_consumption import AiConsumption, AiCreditsBalance
from app.models.billing import Subscription
from app.models.client_account import ClientAccount
from app.models.custom_agent import CustomAgent
from app.models.digital_twin import DigitalTwin
from app.models.recruitment_campaign import RecruitmentCampaign
# Sub-sprint 7B-3a (2026-05-25): SourcingAgent legacy import removed,
# sourcing counts/lists now read CustomAgent.where(category=sourcing).
from app.services.quota_enforcement import (
    DEFAULT_QUOTAS,
    PLAN_AGENT_QUOTAS,
    get_current_count,
    get_effective_quotas,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-external"])


class CompanyListItem(BaseModel):
    id: str
    name: str
    trade_name: str | None = None
    status: str
    plan_id: str | None = None
    industry: str | None = None
    company_size: str | None = None
    primary_email: str | None = None
    created_at: str | None = None
    active_agents: int = 0
    total_tokens_30d: int = 0
    total_cost_30d: int = 0


class CompanyListResponse(BaseModel):
    companies: list[CompanyListItem]
    total: int
    limit: int
    offset: int


class CompanyOverviewResponse(BaseModel):
    company: dict[str, Any]
    subscription: dict[str, Any] | None = None
    ai_consumption: dict[str, Any] = {}
    agents_summary: dict[str, Any] = {}
    token_budget: dict[str, Any] = {}


class StudioAgentItem(BaseModel):
    id: str
    name: str
    agent_type: str
    status: str
    total_executions: int = 0
    created_at: str | None = None
    extra: dict[str, Any] = {}


class CampaignItem(BaseModel):
    id: str
    name: str
    status: str
    total_candidates: int = 0
    candidates_hired: int = 0
    progress_pct: float = 0.0
    created_at: str | None = None


class StudioAgentsResponse(BaseModel):
    company_id: str
    custom_agents: list[StudioAgentItem] = []
    sourcing_agents: list[StudioAgentItem] = []
    digital_twins: list[StudioAgentItem] = []
    campaigns: list[CampaignItem] = []
    totals: dict[str, int] = {}


class ConsumptionBreakdownResponse(BaseModel):
    company_id: str
    period_days: int = 30
    core: dict[str, Any] = {}
    studio: dict[str, Any] = {}
    total_tokens: int = 0
    total_cost_cents: int = 0


class AgentQuotaResponse(BaseModel):
    company_id: str
    plan_code: str | None = None
    quotas: dict[str, int] = {}
    current_usage: dict[str, int] = {}
    quota_enforcement: dict[str, Any] = {}


class AgentQuotaUpdateRequest(WeDoBaseModel):
    custom_agents: int | None = Field(None, ge=-1)
    sourcing_agents: int | None = Field(None, ge=-1)
    digital_twins: int | None = Field(None, ge=-1)
    campaigns: int | None = Field(None, ge=-1)


def _check_quota(limit: int, usage: int) -> dict[str, Any]:
    if limit == -1:
        return {"allowed": True, "remaining": -1, "unlimited": True}
    remaining = max(0, limit - usage)
    return {"allowed": usage < limit, "remaining": remaining, "unlimited": False}


@router.get(
    "/companies",
    response_model=CompanyListResponse,
    summary="List all tenants with summary",
)
async def list_companies(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    plan_filter: str | None = Query(None, alias="plan", description="Filter by plan"),
    search: str | None = Query(None, description="Search by name or email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _admin: Any = Depends(require_admin),
    superadmin: Any = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required.
    # Task #1148: enumerating ALL tenants is inherently cross-tenant, so the
    # whole handler body runs under an audited ``cross_tenant_session``
    # (start+end audit rows, Prometheus counter, RESET ROLE guaranteed).
    async with cross_tenant_session(
        reason="admin_list_companies",
        audit_user_id=str(getattr(superadmin, "id", "") or ""),
    ) as bypass_db:
        db = bypass_db
        conditions = [ClientAccount.is_deleted == False]

        if status_filter:
            conditions.append(ClientAccount.status == status_filter)
        if plan_filter:
            conditions.append(ClientAccount.plan_id == plan_filter)
        if search:
            conditions.append(
                ClientAccount.name.ilike(f"%{search}%")
                | ClientAccount.primary_email.ilike(f"%{search}%")
            )

        count_q = select(func.count(ClientAccount.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        q = (
            select(ClientAccount)
            .where(and_(*conditions))
            .order_by(ClientAccount.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(q)
        clients = result.scalars().all()

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        items = []
        for client in clients:
            cid = client.id

            agent_count_q = select(func.count(CustomAgent.id)).where(
                and_(
                    CustomAgent.company_id == str(cid),
                    CustomAgent.status == "active",
                )
            )
            active_agents = (await db.execute(agent_count_q)).scalar() or 0

            sourcing_count_q = select(func.count(CustomAgent.id)).where(
                and_(
                    CustomAgent.company_id == str(cid),
                    CustomAgent.category == "sourcing",
                    CustomAgent.status != "archived",
                )
            )
            active_sourcing = (await db.execute(sourcing_count_q)).scalar() or 0

            twin_count_q = select(func.count(DigitalTwin.id)).where(
                and_(DigitalTwin.company_id == str(cid), DigitalTwin.is_active == True)
            )
            active_twins = (await db.execute(twin_count_q)).scalar() or 0

            usage_q = select(
                func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
                func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost"),
            ).where(
                and_(
                    AiConsumption.company_id == cid,
                    AiConsumption.created_at >= thirty_days_ago,
                )
            )
            usage_row = (await db.execute(usage_q)).one()

            items.append(
                CompanyListItem(
                    id=str(cid),
                    name=client.name,
                    trade_name=client.trade_name,
                    status=client.status or "",
                    plan_id=client.plan_id,
                    industry=client.industry,
                    company_size=client.company_size,
                    primary_email=client.primary_email,
                    created_at=client.created_at.isoformat() if client.created_at else None,
                    active_agents=active_agents + active_sourcing + active_twins,
                    total_tokens_30d=int(usage_row.tokens),
                    total_cost_30d=int(usage_row.cost),
                )
            )

        return CompanyListResponse(
            companies=items,
            total=total,
            limit=limit,
            offset=offset,
        )


@router.get(
    "/companies/{company_id}/overview",
    response_model=CompanyOverviewResponse,
    summary="Consolidated tenant overview",
)
async def get_company_overview(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    _admin: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")

    result = await db.execute(
        select(ClientAccount).where(ClientAccount.id == company_uuid)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Company not found")

    sub_q = (
        select(Subscription)
        .where(
            and_(
                Subscription.client_id == company_uuid,
                Subscription.status.in_(["active", "trialing"]),
            )
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    sub_result = await db.execute(sub_q)
    subscription = sub_result.scalar_one_or_none()

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    usage_q = select(
        func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
        func.coalesce(func.sum(AiConsumption.input_tokens), 0).label("input_tokens"),
        func.coalesce(func.sum(AiConsumption.output_tokens), 0).label("output_tokens"),
        func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost"),
        func.count(AiConsumption.id).label("operations"),
    ).where(
        and_(
            AiConsumption.company_id == company_uuid,
            AiConsumption.created_at >= thirty_days_ago,
        )
    )
    usage_row = (await db.execute(usage_q)).one()

    cid_str = str(company_uuid)

    custom_count = (
        await db.execute(
            select(func.count(CustomAgent.id)).where(
                CustomAgent.company_id == cid_str
            )
        )
    ).scalar() or 0

    sourcing_count = (
        await db.execute(
            select(func.count(CustomAgent.id)).where(
                and_(
                    CustomAgent.company_id == cid_str,
                    CustomAgent.category == "sourcing",
                    CustomAgent.status != "archived",
                )
            )
        )
    ).scalar() or 0

    twin_count = (
        await db.execute(
            select(func.count(DigitalTwin.id)).where(
                DigitalTwin.company_id == cid_str
            )
        )
    ).scalar() or 0

    campaign_count = (
        await db.execute(
            select(func.count(RecruitmentCampaign.id)).where(
                RecruitmentCampaign.company_id == cid_str
            )
        )
    ).scalar() or 0

    balance_result = await db.execute(
        select(AiCreditsBalance).where(AiCreditsBalance.company_id == company_uuid)
    )
    balance = balance_result.scalar_one_or_none()

    return CompanyOverviewResponse(
        company=client.to_dict(),
        subscription=subscription.to_dict() if subscription else None,
        ai_consumption={
            "total_tokens_30d": int(usage_row.tokens),
            "input_tokens_30d": int(usage_row.input_tokens),
            "output_tokens_30d": int(usage_row.output_tokens),
            "total_cost_cents_30d": int(usage_row.cost),
            "total_operations_30d": int(usage_row.operations),
        },
        agents_summary={
            "custom_agents": custom_count,
            "sourcing_agents": sourcing_count,
            "digital_twins": twin_count,
            "campaigns": campaign_count,
            "total": custom_count + sourcing_count + twin_count + campaign_count,
        },
        token_budget=balance.to_dict() if balance else {},
    )


@router.get(
    "/agents/studio/{company_id}",
    response_model=StudioAgentsResponse,
    summary="List studio agents for a tenant",
)
async def list_studio_agents(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    _admin: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    cid = str(company_id)

    custom_result = await db.execute(
        select(CustomAgent)
        .where(CustomAgent.company_id == cid)
        .order_by(CustomAgent.created_at.desc())
    )
    custom_agents = [
        StudioAgentItem(
            id=str(a.id),
            name=a.name,
            agent_type="custom_agent",
            status=a.status or "draft",
            total_executions=a.total_executions or 0,
            created_at=a.created_at.isoformat() if a.created_at else None,
            extra={
                "role": a.role,
                "domain": a.domain,
                "version": a.version,
                "avg_confidence": a.avg_confidence,
                "is_marketplace_published": a.is_marketplace_published,
            },
        )
        for a in custom_result.scalars().all()
    ]

    # Sub-sprint 7B-3a (2026-05-25): list canonical via CustomAgent category=sourcing.
    # runtime_metrics dict carrega profiles_viewed/approved/rejected/emails_sent/calibration_v
    # (migration 203 moveu legacy cols pra esse JSONB).
    sourcing_result = await db.execute(
        select(CustomAgent)
        .where(
            and_(
                CustomAgent.company_id == cid,
                CustomAgent.category == "sourcing",
            )
        )
        .order_by(CustomAgent.created_at.desc())
    )
    sourcing_agents = []
    for a in sourcing_result.scalars().all():
        m = a.runtime_metrics or {}
        sourcing_agents.append(StudioAgentItem(
            id=str(a.id),
            name=a.name,
            agent_type="sourcing_agent",  # back-compat label
            status=a.status or "active",
            total_executions=int(m.get("profiles_viewed") or 0),
            created_at=a.created_at.isoformat() if a.created_at else None,
            extra={
                "profiles_viewed": m.get("profiles_viewed"),
                "profiles_approved": m.get("profiles_approved"),
                "profiles_rejected": m.get("profiles_rejected"),
                "emails_sent": m.get("emails_sent"),
                "calibration_v": m.get("calibration_v"),
            },
        ))

    twin_result = await db.execute(
        select(DigitalTwin)
        .where(DigitalTwin.company_id == cid)
        .order_by(DigitalTwin.created_at.desc())
    )
    digital_twins = [
        StudioAgentItem(
            id=str(a.id),
            name=a.twin_name,
            agent_type="digital_twin",
            status="active" if a.is_active else "inactive",
            total_executions=a.decision_count or 0,
            created_at=a.created_at.isoformat() if a.created_at else None,
            extra={
                "specialties": a.specialties or [],
                "accuracy_pct": a.accuracy_pct,
            },
        )
        for a in twin_result.scalars().all()
    ]

    campaign_result = await db.execute(
        select(RecruitmentCampaign)
        .where(RecruitmentCampaign.company_id == cid)
        .order_by(RecruitmentCampaign.created_at.desc())
    )
    campaigns = [
        CampaignItem(
            id=str(c.id),
            name=c.name,
            status=c.status or "draft",
            total_candidates=c.total_candidates or 0,
            candidates_hired=c.candidates_hired or 0,
            progress_pct=c.progress_pct,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in campaign_result.scalars().all()
    ]

    return StudioAgentsResponse(
        company_id=cid,
        custom_agents=custom_agents,
        sourcing_agents=sourcing_agents,
        digital_twins=digital_twins,
        campaigns=campaigns,
        totals={
            "custom_agents": len(custom_agents),
            "sourcing_agents": len(sourcing_agents),
            "digital_twins": len(digital_twins),
            "campaigns": len(campaigns),
            "total": len(custom_agents) + len(sourcing_agents) + len(digital_twins) + len(campaigns),
        },
    )


@router.get(
    "/agents/studio/{company_id}/consumption",
    response_model=ConsumptionBreakdownResponse,
    summary="Core vs Studio consumption breakdown",
)
async def get_studio_consumption(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    days: int = Query(30, ge=1, le=365),
    _admin: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")

    start_date = datetime.utcnow() - timedelta(days=days)

    base_conditions = [
        AiConsumption.company_id == company_uuid,
        AiConsumption.created_at >= start_date,
    ]

    core_q = select(
        func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
        func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost"),
        func.count(AiConsumption.id).label("operations"),
    ).where(
        and_(*base_conditions, AiConsumption.agent_category == "core")
    )
    core_row = (await db.execute(core_q)).one()

    studio_q = select(
        func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
        func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost"),
        func.count(AiConsumption.id).label("operations"),
    ).where(
        and_(*base_conditions, AiConsumption.agent_category == "studio")
    )
    studio_row = (await db.execute(studio_q)).one()

    studio_by_type_q = (
        select(
            AiConsumption.agent_type,
            func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
            func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost"),
            func.count(AiConsumption.id).label("operations"),
        )
        .where(and_(*base_conditions, AiConsumption.agent_category == "studio"))
        .group_by(AiConsumption.agent_type)
    )
    studio_breakdown_rows = (await db.execute(studio_by_type_q)).all()

    total_tokens = int(core_row.tokens) + int(studio_row.tokens)
    total_cost = int(core_row.cost) + int(studio_row.cost)

    return ConsumptionBreakdownResponse(
        company_id=company_id,
        period_days=days,
        core={
            "total_tokens": int(core_row.tokens),
            "total_cost_cents": int(core_row.cost),
            "total_operations": int(core_row.operations),
            "percentage": round(int(core_row.tokens) / total_tokens * 100, 2) if total_tokens > 0 else 0,
        },
        studio={
            "total_tokens": int(studio_row.tokens),
            "total_cost_cents": int(studio_row.cost),
            "total_operations": int(studio_row.operations),
            "percentage": round(int(studio_row.tokens) / total_tokens * 100, 2) if total_tokens > 0 else 0,
            "by_agent_type": [
                {
                    "agent_type": row.agent_type,
                    "total_tokens": int(row.tokens),
                    "total_cost_cents": int(row.cost),
                    "total_operations": int(row.operations),
                }
                for row in studio_breakdown_rows
            ],
        },
        total_tokens=total_tokens,
        total_cost_cents=total_cost,
    )


@router.get(
    "/agents/quota/{company_id}",
    response_model=AgentQuotaResponse,
    summary="Get agent quotas for a tenant",
)
async def get_agent_quota(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    _admin: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")

    client_check = await db.execute(
        select(ClientAccount.id).where(ClientAccount.id == company_uuid)
    )
    if not client_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Company not found")

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

    cid = str(company_uuid)
    quotas = await get_effective_quotas(cid, db)

    resource_keys = ["custom_agents", "sourcing_agents", "digital_twins", "campaigns"]
    usage = {}
    for key in resource_keys:
        usage[key] = await get_current_count(key, cid, db)

    enforcement = {
        k: _check_quota(quotas.get(k, 0), usage.get(k, 0))
        for k in resource_keys
    }

    return AgentQuotaResponse(
        company_id=company_id,
        plan_code=plan_code,
        quotas=quotas,
        current_usage=usage,
        quota_enforcement=enforcement,
    )


@router.put(
    "/agents/quota/{company_id}",
    response_model=AgentQuotaResponse,
    summary="Adjust agent quotas for a tenant",
)
async def update_agent_quota(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: AgentQuotaUpdateRequest,
    _admin: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company_id format")

    client_result = await db.execute(
        select(ClientAccount).where(ClientAccount.id == company_uuid)
    )
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Company not found")

    settings = client.settings or {}
    overrides = settings.get("agent_quotas", {})

    if body.custom_agents is not None:
        overrides["custom_agents"] = body.custom_agents
    if body.sourcing_agents is not None:
        overrides["sourcing_agents"] = body.sourcing_agents
    if body.digital_twins is not None:
        overrides["digital_twins"] = body.digital_twins
    if body.campaigns is not None:
        overrides["campaigns"] = body.campaigns

    settings["agent_quotas"] = overrides
    client.settings = settings
    await db.flush()

    return await get_agent_quota(company_id, _admin=_admin, db=db)

reorder_collection_before_item(router)
