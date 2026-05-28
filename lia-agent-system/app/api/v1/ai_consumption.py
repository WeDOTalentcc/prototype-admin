"""
AI Consumption API Endpoints.

Provides endpoints for:
- Recording AI usage (internal)
- Viewing usage summaries and history
- Managing credit limits (admin)
- Analytics by agent, model, and day
"""
# SISTEMA: Tokens LLM (consumption tracking) — ADR-030
# Ver: docs/adr/ADR-030-ai-credits-two-systems.md
# NAO confundir com billing.py (creditos de plano) — sistemas distintos intencionalmente.
# Este arquivo trata de metering tecnico: tokens por modelo, rate limiting, overage.
# Para verificar limite de plano ou emitir fatura, usar billing.py.
import logging
from datetime import date, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import Date, and_, cast, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.ai.repositories.ai_consumption_repository import AiConsumptionRepository
from app.models.ai_consumption import AiConsumption, AiCreditsBalance
from app.schemas.ai_consumption import (
    AgentDailyTrendListResponse,
    AgentDailyTrendResponse,
    AiConsumptionRecord,
    AiConsumptionResponse,
    BalanceResponse,
    UpdateLimitsRequest,
    UsageByAgentListResponse,
    UsageByAgentResponse,
    UsageByDayListResponse,
    UsageByDayResponse,
    UsageHistoryResponse,
    UsageSummaryResponse,
)
from app.shared.services.token_tracking_service import (
    DEFAULT_LIMITS,
    TOKEN_PRICES,
    get_token_tracking_service,
)
from app.domains.credits.services.token_budget_service import get_plan_limit
from app.shared.tenant_guard import get_verified_company_id
from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-consumption", tags=["ai-consumption"])


def get_ai_consumption_repo(db: AsyncSession = Depends(get_db)) -> AiConsumptionRepository:
    return AiConsumptionRepository(db)


async def get_or_create_balance(db: AsyncSession, company_uuid: UUID) -> AiCreditsBalance:
    result = await db.execute(
        select(AiCreditsBalance).where(AiCreditsBalance.company_id == company_uuid)
    )
    balance = result.scalar_one_or_none()
    if balance is None:
        from datetime import date as date_type
        today = date_type.today()
        period_start = today.replace(day=1)
        if today.month == 12:
            period_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            period_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        balance = AiCreditsBalance(
            company_id=company_uuid,
            monthly_limit=100000,
            current_usage=0,
            period_start=period_start,
            period_end=period_end,
        )
        db.add(balance)
        await db.flush()
        await db.refresh(balance)
    return balance


async def _get_usage_summary_data(company_id: str, db: AsyncSession) -> UsageSummaryResponse:
    company_uuid = UUID(company_id)
    balance = await get_or_create_balance(db, company_uuid)

    conditions = [
        AiConsumption.company_id == company_uuid,
        AiConsumption.created_at >= datetime.combine(balance.period_start, datetime.min.time()),
        AiConsumption.created_at <= datetime.combine(balance.period_end, datetime.max.time()),
    ]

    stats_query = select(
        func.sum(AiConsumption.total_tokens).label("total_tokens"),
        func.sum(AiConsumption.input_tokens).label("input_tokens"),
        func.sum(AiConsumption.output_tokens).label("output_tokens"),
        func.sum(AiConsumption.cost_cents).label("total_cost"),
        func.count(AiConsumption.id).label("total_ops"),
    ).where(and_(*conditions))

    result = await db.execute(stats_query)
    stats = result.one()
    total_tokens = int(stats.total_tokens or 0)

    seven_days_ago = datetime.now() - timedelta(days=7)
    last7_query = select(
        func.sum(AiConsumption.total_tokens).label("tokens_7d"),
        func.sum(AiConsumption.cost_cents).label("cost_7d"),
    ).where(and_(
        AiConsumption.company_id == company_uuid,
        AiConsumption.created_at >= seven_days_ago,
    ))
    last7_result = await db.execute(last7_query)
    last7 = last7_result.one()

    tokens_7d = int(last7.tokens_7d or 0)
    cost_7d = int(last7.cost_7d or 0)

    avg_daily_tokens = round(tokens_7d / 7)
    avg_daily_cost = round(cost_7d / 7)
    projected_monthly_tokens = avg_daily_tokens * 30
    projected_monthly_cost = avg_daily_cost * 30

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = select(
        func.sum(AiConsumption.total_tokens).label("today_tokens"),
    ).where(and_(
        AiConsumption.company_id == company_uuid,
        AiConsumption.created_at >= today_start,
    ))
    today_result = await db.execute(today_query)
    daily_usage_today = int((today_result.scalar() or 0))

    plan_code = None
    try:
        from app.domains.credits.services.token_budget_service import get_plan_for_company
        plan_code = await get_plan_for_company(company_id)
    except Exception as exc:
        logger.debug("Could not resolve plan_code for company %s, using default limit: %s", company_id, exc)
    daily_limit = get_plan_limit(plan_code)
    if daily_limit == -1:
        daily_limit = 0
    daily_usage_pct = round((daily_usage_today / daily_limit) * 100, 2) if daily_limit > 0 else 0

    return UsageSummaryResponse(
        company_id=company_id,
        period_start=balance.period_start.isoformat(),
        period_end=balance.period_end.isoformat(),
        total_tokens=total_tokens,
        total_input_tokens=int(stats.input_tokens or 0),
        total_output_tokens=int(stats.output_tokens or 0),
        total_cost_cents=int(stats.total_cost or 0),
        total_operations=int(stats.total_ops or 0),
        monthly_limit=balance.monthly_limit,
        usage_percentage=round((total_tokens / balance.monthly_limit) * 100, 2) if balance.monthly_limit > 0 else 0,
        remaining_tokens=max(0, balance.monthly_limit - total_tokens),
        overage_allowed=balance.overage_allowed,
        projected_monthly_tokens=projected_monthly_tokens,
        projected_monthly_cost_cents=projected_monthly_cost,
        avg_daily_tokens_7d=avg_daily_tokens,
        avg_daily_cost_7d=avg_daily_cost,
        daily_limit=daily_limit,
        daily_usage_today=daily_usage_today,
        daily_usage_percentage=daily_usage_pct,
    )


@router.get("/summary", response_model=UsageSummaryResponse, summary="Get usage summary")
async def get_summary(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get AI usage summary for the current billing period (alias for /usage)."""
    try:
        return await _get_usage_summary_data(company_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage", response_model=UsageSummaryResponse, summary="Get current period usage")
async def get_usage_summary(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get AI usage summary for the current billing period."""
    try:
        return await _get_usage_summary_data(company_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/{client_id}", response_model=UsageSummaryResponse, summary="Get client usage (admin)")
async def get_client_usage(
    client_id: str,
    company_id: str = Depends(get_verified_company_id),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: ownership check added (P0-W3-04 fix 2026-05-24)
    """Get AI usage summary for a specific client.

    Regular users can only view their own company's usage.
    WeDOTalent admins and tenant admins can view any company.
    """
    try:
        # P0-W3-04: enforce ownership — user must be accessing own tenant OR be admin
        if (str(current_user.company_id) != str(client_id)
                and current_user.role not in (UserRole.admin, UserRole.wedotalent_admin)):
            raise HTTPException(status_code=403, detail="Access denied")
        client_uuid = UUID(client_id)
        balance = await get_or_create_balance(db, client_uuid)
        
        conditions = [
            AiConsumption.company_id == client_uuid,
            AiConsumption.created_at >= datetime.combine(balance.period_start, datetime.min.time()),
            AiConsumption.created_at <= datetime.combine(balance.period_end, datetime.max.time())
        ]
        
        # TODO(phase2): complex transaction with balance model — AiConsumption stats query left as direct DB
        stats_query = select(
            func.sum(AiConsumption.total_tokens).label('total_tokens'),
            func.sum(AiConsumption.input_tokens).label('input_tokens'),
            func.sum(AiConsumption.output_tokens).label('output_tokens'),
            func.sum(AiConsumption.cost_cents).label('total_cost'),
            func.count(AiConsumption.id).label('total_ops')
        ).where(and_(*conditions))
        
        result = await db.execute(stats_query)
        stats = result.one()
        
        total_tokens = int(stats.total_tokens or 0)
        
        return UsageSummaryResponse(
            company_id=client_id,
            period_start=balance.period_start.isoformat(),
            period_end=balance.period_end.isoformat(),
            total_tokens=total_tokens,
            total_input_tokens=int(stats.input_tokens or 0),
            total_output_tokens=int(stats.output_tokens or 0),
            total_cost_cents=int(stats.total_cost or 0),
            total_operations=int(stats.total_ops or 0),
            monthly_limit=balance.monthly_limit,
            usage_percentage=round((total_tokens / balance.monthly_limit) * 100, 2) if balance.monthly_limit > 0 else 0,
            remaining_tokens=max(0, balance.monthly_limit - total_tokens),
            overage_allowed=balance.overage_allowed
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=UsageHistoryResponse, summary="Get usage history")
async def get_usage_history(
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    agent_type: str | None = Query(None, description="Filter by agent type"),
    model: str | None = Query(None, description="Filter by model"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get historical AI consumption records with filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [AiConsumption.company_id == company_uuid]
        
        if start_date:
            conditions.append(AiConsumption.created_at >= start_date)
        if end_date:
            conditions.append(AiConsumption.created_at <= end_date)
        if agent_type:
            conditions.append(AiConsumption.agent_type == agent_type)
        if model:
            conditions.append(AiConsumption.model == model)
        
        repo = AiConsumptionRepository(db)
        records, total = await repo.list_history(
            company_id,
            start_date=start_date,
            end_date=end_date,
            agent_type=agent_type,
            model=model,
            limit=limit,
            offset=offset,
        )
        
        return UsageHistoryResponse(
            records=[AiConsumptionResponse(**r.to_dict()) for r in records],
            total=total,
            limit=limit,
            offset=offset,
            period_start=start_date.isoformat() if start_date else None,
            period_end=end_date.isoformat() if end_date else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-agent", response_model=UsageByAgentListResponse, summary="Get usage by agent type")
async def get_usage_by_agent(
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    studio_agent_id: str | None = Query(
        None,
        description=(
            "Filtra consumo de um agente Studio individual (canonical). "
            "Quando omitido, agrega todos os agentes da tenant. "
            "Wave 0 Fix 5 (2026-05-27)."
        ),
    ),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get AI usage grouped by agent type. Optionally filter by studio_agent_id."""
    try:
        company_uuid = UUID(company_id)
        conditions = [AiConsumption.company_id == company_uuid]
        
        if start_date:
            conditions.append(AiConsumption.created_at >= start_date)
        if end_date:
            conditions.append(AiConsumption.created_at <= end_date)
        
        repo = AiConsumptionRepository(db)
        rows = await repo.get_usage_by_agent(
            company_id,
            start_date=start_date,
            end_date=end_date,
            studio_agent_id=studio_agent_id,
        )
        
        grand_total_tokens = sum(row.total_tokens or 0 for row in rows)
        grand_total_ops = sum(row.total_ops or 0 for row in rows)
        
        data = []
        for row in rows:
            tokens = int(row.total_tokens or 0)
            data.append(UsageByAgentResponse(
                agent_type=row.agent_type,
                total_tokens=tokens,
                total_operations=int(row.total_ops or 0),
                total_cost_cents=int(row.total_cost or 0),
                percentage_of_total=round((tokens / grand_total_tokens) * 100, 2) if grand_total_tokens > 0 else 0
            ))
        
        data.sort(key=lambda x: x.total_tokens, reverse=True)
        
        return UsageByAgentListResponse(
            data=data,
            total_tokens=grand_total_tokens,
            total_operations=grand_total_ops
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage by agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-trend", response_model=AgentDailyTrendListResponse, summary="Get daily trend per agent")
async def get_agent_daily_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get AI usage grouped by day and agent type for trend charts."""
    try:
        repo = AiConsumptionRepository(db)
        rows = await repo.get_usage_by_agent_and_day(company_id, days=days)

        data = []
        dates_seen: set[str] = set()
        for row in rows:
            date_str = row.date.isoformat() if row.date else ""
            dates_seen.add(date_str)
            data.append(AgentDailyTrendResponse(
                date=date_str,
                agent_type=row.agent_type,
                total_tokens=int(row.total_tokens or 0),
                total_cost_cents=int(row.total_cost or 0),
                total_operations=int(row.total_ops or 0),
            ))

        return AgentDailyTrendListResponse(
            data=data,
            total_days=len(dates_seen),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent daily trend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _get_daily_usage_data(days: int, company_id: str, db: AsyncSession) -> UsageByDayListResponse:
    """Internal helper to get daily usage data."""
    company_uuid = UUID(company_id)
    start_date = datetime.now() - timedelta(days=days)
    
    conditions = [
        AiConsumption.company_id == company_uuid,
        AiConsumption.created_at >= start_date
    ]
    
    repo = AiConsumptionRepository(db)
    rows = await repo.get_usage_by_day(company_id, days=days)
    
    data = []
    total_tokens = 0
    for row in rows:
        tokens = int(row.total_tokens or 0)
        total_tokens += tokens
        data.append(UsageByDayResponse(
            date=row.date.isoformat() if row.date else "",
            total_tokens=tokens,
            total_operations=int(row.total_ops or 0),
            total_cost_cents=int(row.total_cost or 0)
        ))
    
    return UsageByDayListResponse(
        data=data,
        total_tokens=total_tokens,
        total_days=len(data)
    )


@router.get("/daily", response_model=UsageByDayListResponse, summary="Get daily usage")
async def get_daily_usage(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get AI usage grouped by day (alias for /by-day)."""
    try:
        return await _get_daily_usage_data(days, company_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-day", response_model=UsageByDayListResponse, summary="Get daily usage")
async def get_usage_by_day(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get AI usage grouped by day for charts."""
    try:
        return await _get_daily_usage_data(days, company_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage by day: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance", response_model=BalanceResponse, summary="Get credits balance")
async def get_balance(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get current AI credits balance and limits."""
    try:
        company_uuid = UUID(company_id)
        balance = await get_or_create_balance(db, company_uuid)
        
        # TODO(phase2): complex transaction with balance model — usage sum query left as direct DB
        usage_query = select(
            func.sum(AiConsumption.total_tokens).label('total')
        ).where(and_(
            AiConsumption.company_id == company_uuid,
            AiConsumption.created_at >= datetime.combine(balance.period_start, datetime.min.time()),
            AiConsumption.created_at <= datetime.combine(balance.period_end, datetime.max.time())
        ))
        
        result = await db.execute(usage_query)
        current_usage = int(result.scalar() or 0)
        
        balance.current_usage = current_usage
        
        return BalanceResponse(**balance.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting balance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record", response_model=AiConsumptionResponse, summary="Record AI consumption")
async def record_consumption(
    record: AiConsumptionRecord,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Record a new AI consumption entry (internal use)."""
    try:
        company_uuid = UUID(company_id)
        
        total_tokens = record.total_tokens
        if total_tokens is None:
            total_tokens = record.input_tokens + record.output_tokens

        # P1-W3-08: Overage enforcement — block when limit exceeded + overage_allowed=False
        _balance = await get_or_create_balance(db, company_uuid)
        if _balance.monthly_limit and _balance.monthly_limit > 0 and not _balance.overage_allowed:
            _period_usage_result = await db.execute(
                select(func.sum(AiConsumption.total_tokens)).where(
                    and_(
                        AiConsumption.company_id == company_uuid,
                        AiConsumption.created_at >= datetime.combine(_balance.period_start, datetime.min.time()),
                        AiConsumption.created_at <= datetime.combine(_balance.period_end, datetime.max.time()),
                    )
                )
            )
            _current = int(_period_usage_result.scalar() or 0)
            if _current >= _balance.monthly_limit:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": "monthly_limit_exceeded",
                        "current_usage": _current,
                        "monthly_limit": _balance.monthly_limit,
                        "message": "Limite mensal de tokens atingido. Contate o administrador para aumentar o limite.",
                    },
                )

        repo = AiConsumptionRepository(db)
        consumption = await repo.create({
            "company_id": company_uuid,
            "user_id": UUID(record.user_id) if record.user_id else None,
            "agent_type": record.agent_type,
            "operation": record.operation,
            "model": record.model,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "total_tokens": total_tokens,
            "cost_cents": record.cost_cents or 0,
            "candidate_id": UUID(record.candidate_id) if record.candidate_id else None,
            "vacancy_id": UUID(record.vacancy_id) if record.vacancy_id else None,
            "extra_data": record.metadata or {},
        })
        
        # P1-W3-07+W3-09: balance.current_usage update removed.
        # Updating was (a) un-committed — no db.commit() after assignment, and
        # (b) race-prone — get_or_create_balance has no WITH FOR UPDATE.
        # GET /balance recalculates current_usage via SELECT SUM(total_tokens)
        # on every call so the displayed value is always correct without this field.
        logger.info(f"Recorded AI consumption: {consumption.agent_type}/{consumption.operation} - {total_tokens} tokens")
        
        return AiConsumptionResponse(**consumption.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording consumption: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/limits/{client_id}", response_model=BalanceResponse, summary="Update client limits (admin)")
async def update_limits(
    client_id: str,
    request: UpdateLimitsRequest,
    company_id: str = Depends(get_verified_company_id),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: role + ownership check added (P0-W3-04 fix 2026-05-24)
    """Update AI limits for a client.

    Requires: admin or wedotalent_admin role AND (own company OR wedotalent_admin).
    Regular users and non-admin tenant users cannot modify limits for any company.
    """
    try:
        # P0-W3-04: only admins can update limits; wedotalent_admin can update any tenant
        if current_user.role not in (UserRole.admin, UserRole.wedotalent_admin):
            raise HTTPException(status_code=403, detail="Admin access required to update limits")
        if (current_user.role == UserRole.admin
                and str(current_user.company_id) != str(client_id)):
            raise HTTPException(status_code=403, detail="Access denied: can only update own company limits")
        client_uuid = UUID(client_id)
        balance = await get_or_create_balance(db, client_uuid)
        
        if request.monthly_limit is not None:
            balance.monthly_limit = request.monthly_limit
        if request.overage_allowed is not None:
            balance.overage_allowed = request.overage_allowed
        if request.overage_rate_cents is not None:
            balance.overage_rate_cents = request.overage_rate_cents
        if request.period_start is not None:
            balance.period_start = request.period_start
        if request.period_end is not None:
            balance.period_end = request.period_end
        if request.reset_usage:
            balance.current_usage = 0
        
        # TODO(phase2): balance model update — left as direct DB (balance is separate model)
        await db.flush()
        await db.refresh(balance)
        
        logger.info(f"Updated AI limits for client {client_id}")
        
        return BalanceResponse(**balance.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating limits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def get_user_id_from_header(
    x_user_id: str | None = Header(None, alias="X-User-ID")
) -> str | None:
    """Extract user ID from header (optional)."""
    if x_user_id:
        try:
            UUID(x_user_id)
            return x_user_id
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-User-ID format"
            )
    return None


ai_usage_router = APIRouter(prefix="/ai/usage", tags=["ai-usage"])


@ai_usage_router.get("/me", summary="Get current user's AI usage")
async def get_my_usage(
    period: str = Query("day", description="Period: hour, day, week, month"),
    user_id: str | None = Depends(get_user_id_from_header),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Get AI token usage for the current user.
    
    Returns usage statistics including:
    - Total tokens used (input + output)
    - Cost estimate in USD
    - Operations count
    - Usage breakdown by agent type
    - Limit status and remaining quota
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header required"
        )
    
    try:
        tracking_service = get_token_tracking_service(db)
        usage = await tracking_service.get_usage_by_user(
            user_id=user_id, 
            period=period, 
            company_id=company_id
        )
        
        is_within_limits, limit_message = await tracking_service.check_limits(
            user_id=user_id,
            company_id=company_id
        )
        
        usage["limits_status"] = {
            "is_within_limits": is_within_limits,
            "message": limit_message
        }
        
        return usage
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@ai_usage_router.get("/company", summary="Get company AI usage")
async def get_company_usage(
    period: str = Query("day", description="Period: hour, day, week, month"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Get AI token usage for the company.
    
    Returns company-wide usage statistics including:
    - Total tokens used across all users
    - Cost estimate in USD
    - Unique user count
    - Usage breakdown by agent type and model
    - Monthly limits and remaining quota
    """
    try:
        tracking_service = get_token_tracking_service(db)
        usage = await tracking_service.get_usage_by_company(
            company_id=company_id,
            period=period
        )
        
        real_time = await tracking_service.get_real_time_stats(
            company_id=company_id,
            window_minutes=5
        )
        usage["real_time"] = real_time
        
        return usage
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@ai_usage_router.get("/agents", summary="Get AI usage by agent type (admin)")
async def get_agents_usage(
    period: str = Query("day", description="Period: hour, day, week, month"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Get AI token usage grouped by agent type (admin endpoint).
    
    Returns usage statistics per agent including:
    - Token usage per agent type
    - Cost breakdown by agent
    - Operation counts
    - Average latency per agent
    - Percentage of total usage
    """
    try:
        tracking_service = get_token_tracking_service(db)
        usage = await tracking_service.get_usage_by_agent(
            period=period,
            company_id=company_id
        )
        
        usage["token_prices"] = TOKEN_PRICES
        usage["default_limits"] = DEFAULT_LIMITS
        
        return usage
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agents usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@ai_usage_router.get("/limits", summary="Get configured usage limits")
async def get_usage_limits(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Get the configured usage limits for the company.
    
    Returns:
    - Default limits (daily tokens per user, company, monthly cost)
    - Token pricing information for cost estimation
    """
    try:
        tracking_service = get_token_tracking_service(db)
        limits = tracking_service.get_limits(company_id)
        
        return {
            "company_id": company_id,
            "limits": limits,
            "token_prices": TOKEN_PRICES
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting limits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@ai_usage_router.post("/check-limits", summary="Check if within usage limits")
async def check_usage_limits(
    user_id: str | None = Depends(get_user_id_from_header),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Check if the user/company is within configured usage limits.
    
    Returns:
    - is_within_limits: Boolean indicating if usage is allowed
    - message: Human-readable status message
    - details: Breakdown of current usage vs limits
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header required"
        )
    
    try:
        tracking_service = get_token_tracking_service(db)
        
        is_within_limits, message = await tracking_service.check_limits(
            user_id=user_id,
            company_id=company_id
        )
        
        user_usage = await tracking_service.get_usage_by_user(
            user_id=user_id,
            period="day",
            company_id=company_id
        )
        
        company_usage = await tracking_service.get_usage_by_company(
            company_id=company_id,
            period="day"
        )
        
        limits = tracking_service.get_limits(company_id)
        
        return {
            "is_within_limits": is_within_limits,
            "message": message,
            "details": {
                "user_daily_tokens": user_usage["total_tokens"],
                "user_daily_limit": limits["daily_tokens_per_user"],
                "user_usage_percentage": user_usage.get("usage_percentage", 0),
                "company_daily_tokens": company_usage["total_tokens"],
                "company_daily_limit": limits["daily_tokens_per_company"],
                "company_usage_percentage": company_usage.get("usage_percentage", 0)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking limits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@ai_usage_router.get("/real-time", summary="Get real-time usage statistics")
async def get_real_time_usage(
    window_minutes: int = Query(5, ge=1, le=60, description="Time window in minutes"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Get real-time AI usage statistics for the last N minutes.
    
    Returns:
    - Total tokens in window
    - Operations count
    - Tokens per minute rate
    - Average latency
    """
    try:
        tracking_service = get_token_tracking_service(db)
        return await tracking_service.get_real_time_stats(
            company_id=company_id,
            window_minutes=window_minutes
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting real-time usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Onda 4 B2/B3 — Drilldown + Budget Alerts (2026-05-28)
# ============================================================================
# B2: lista execuções individuais (rows ai_consumption) com filtros + paginação.
# B3: alertas de orçamento global + per-agent com severity info/warning/critical.
#
# Multi-tenancy: get_verified_company_id obrigatório.
# ADR-001: queries SQL fail-closed via WHERE company_id; agregação on-demand
# (sem tabela snapshot — esperar evidência de carga antes de pré-computar).
# ============================================================================

from typing import Literal as _Literal

from app.shared.types import WeDoBaseModel as _WeDoBaseModel


class ConsumptionExecutionItem(_WeDoBaseModel):
    """Onda 4 B2 — uma linha de drilldown de consumo."""

    consumption_id: str
    agent_type: str
    studio_agent_id: str | None = None
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_cents: int
    candidate_id: str | None = None
    vacancy_id: str | None = None
    created_at: datetime


class ConsumptionDrilldownResponse(_WeDoBaseModel):
    """Onda 4 B2 — payload completo do drilldown."""

    items: list[ConsumptionExecutionItem]
    total_count: int
    total_cost_cents: int
    total_tokens: int


@router.get(
    "/by-agent/drilldown",
    response_model=ConsumptionDrilldownResponse,
    summary="Onda 4 B2 — drilldown de execuções de consumo",
)
async def get_consumption_drilldown(
    agent_type: str | None = Query(default=None, description="Filtra por agent_type (ex: 'digital_twin')"),
    studio_agent_id: str | None = Query(default=None, description="Filtra por studio_agent_id (agente individual)"),
    since_days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
) -> ConsumptionDrilldownResponse:
    """Lista execuções individuais (ai_consumption) com filtros + paginação.

    Multi-tenancy: filter company_id no SQL.
    Performance: usa index idx_ai_consumption_company_type_date quando existir;
    fallback aceitável em volumes < 100k rows/tenant/period.
    """
    from datetime import date as _date_type

    company_uuid = UUID(company_id)
    since_cutoff = datetime.now() - timedelta(days=since_days)

    conditions = [
        AiConsumption.company_id == company_uuid,
        AiConsumption.created_at >= since_cutoff,
    ]
    if agent_type:
        conditions.append(AiConsumption.agent_type == agent_type)
    if studio_agent_id:
        conditions.append(AiConsumption.studio_agent_id == studio_agent_id)

    totals_stmt = select(
        func.count(AiConsumption.id).label("total_count"),
        func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("total_cost_cents"),
        func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("total_tokens"),
    ).where(and_(*conditions))
    totals_result = await db.execute(totals_stmt)
    totals = totals_result.one()

    items_stmt = (
        select(AiConsumption)
        .where(and_(*conditions))
        .order_by(desc(AiConsumption.created_at))
        .limit(limit)
        .offset(offset)
    )
    items_result = await db.execute(items_stmt)
    rows = list(items_result.scalars().all())

    items: list[ConsumptionExecutionItem] = []
    for row in rows:
        items.append(
            ConsumptionExecutionItem(
                consumption_id=str(row.id),
                agent_type=row.agent_type,
                studio_agent_id=row.studio_agent_id,
                operation=row.operation,
                model=row.model,
                input_tokens=int(row.input_tokens or 0),
                output_tokens=int(row.output_tokens or 0),
                total_tokens=int(row.total_tokens or 0),
                cost_cents=int(row.cost_cents or 0),
                candidate_id=str(row.candidate_id) if row.candidate_id else None,
                vacancy_id=str(row.vacancy_id) if row.vacancy_id else None,
                created_at=row.created_at,
            )
        )

    return ConsumptionDrilldownResponse(
        items=items,
        total_count=int(totals.total_count or 0),
        total_cost_cents=int(totals.total_cost_cents or 0),
        total_tokens=int(totals.total_tokens or 0),
    )
