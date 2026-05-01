import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

STUDIO_AGENT_TYPES = {"sourcing_agent", "custom_agent", "digital_twin", "recruitment_campaign", "marketplace_agent"}


class StudioMeteringService:

    OPERATION_TOKEN_ESTIMATES = {
        "create_sourcing_agent": (200, 100),
        "calibrate_agent": (2000, 1500),
        "run_multi_strategy": (3000, 2000),
        "create_custom_agent": (150, 80),
        "test_custom_agent": (1000, 800),
        "execute_custom_agent": (2000, 1500),
        "create_twin": (500, 300),
        "evaluate_with_twin": (3000, 2000),
        "index_twin_audio": (5000, 500),
        "create_campaign": (100, 50),
        "advance_campaign": (500, 300),
        "install_from_marketplace": (50, 20),
    }

    TOKEN_COST_PER_1K = 0.15

    async def record_studio_usage(
        self,
        db: AsyncSession,
        company_id: str,
        agent_type: str,
        operation: str,
        studio_agent_id: str | None = None,
        model: str = "gemini-1.5-flash",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_cents: int = 0,
        user_id: str | None = None,
        extra_data: dict | None = None,
        profiles_processed: int = 0,
    ) -> None:
        from lia_models.ai_consumption import AiConsumption

        if input_tokens == 0 and output_tokens == 0:
            est_in, est_out = self.OPERATION_TOKEN_ESTIMATES.get(operation, (100, 50))
            input_tokens = est_in
            output_tokens = est_out

        total_tokens = input_tokens + output_tokens

        if cost_cents == 0 and total_tokens > 0:
            cost_cents = max(1, int((total_tokens / 1000) * self.TOKEN_COST_PER_1K * 100))

        merged_extra = extra_data or {}
        if profiles_processed > 0:
            merged_extra["profiles_processed"] = profiles_processed

        record = AiConsumption(
            id=uuid.uuid4(),
            company_id=company_id,
            user_id=user_id,
            agent_type=agent_type,
            agent_category="studio",
            operation=operation,
            model=model,
            studio_agent_id=studio_agent_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_cents=cost_cents,
            extra_data=merged_extra,
        )
        db.add(record)
        await db.flush()

        if total_tokens > 0:
            try:
                from app.domains.credits.services.token_budget_service import increment_usage
                await increment_usage(company_id, total_tokens)
            except Exception as e:
                logger.warning("[StudioMetering] TokenBudget increment failed: %s", e)

    async def get_studio_consumption(
        self,
        db: AsyncSession,
        company_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        from lia_models.ai_consumption import AiConsumption

        since = datetime.utcnow() - timedelta(days=days)
        base_filter = and_(
            AiConsumption.company_id == company_id,
            AiConsumption.agent_category == "studio",
            AiConsumption.created_at >= since,
        )

        from sqlalchemy import cast, Integer as SAInteger
        from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB

        total_q = select(
            func.count(AiConsumption.id).label("executions"),
            func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
            func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost_cents"),
        ).where(base_filter)
        totals = (await db.execute(total_q)).one()

        total_credits = round(int(totals.cost_cents) / 100, 2)

        profiles_q = select(
            func.coalesce(
                func.sum(
                    cast(AiConsumption.extra_data["profiles_processed"].as_string(), SAInteger)
                ), 0
            ).label("profiles"),
        ).where(
            and_(base_filter, AiConsumption.extra_data["profiles_processed"] != None)
        )
        try:
            profiles_row = (await db.execute(profiles_q)).one()
            total_profiles = int(profiles_row.profiles)
        except Exception:
            total_profiles = 0

        by_type_q = (
            select(
                AiConsumption.agent_type,
                func.count(AiConsumption.id).label("executions"),
                func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
                func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost_cents"),
            )
            .where(base_filter)
            .group_by(AiConsumption.agent_type)
        )
        type_rows = (await db.execute(by_type_q)).all()

        breakdown = {}
        for row in type_rows:
            breakdown[row.agent_type] = {
                "executions": row.executions,
                "tokens": row.tokens,
                "cost_cents": row.cost_cents,
                "credits": round(int(row.cost_cents) / 100, 2),
            }

        return {
            "company_id": str(company_id),
            "period_days": days,
            "total_executions": totals.executions,
            "total_tokens": totals.tokens,
            "total_cost_cents": totals.cost_cents,
            "total_credits": total_credits,
            "total_profiles_processed": total_profiles,
            "breakdown_by_type": breakdown,
        }

    async def get_agent_consumption(
        self,
        db: AsyncSession,
        company_id: str,
        studio_agent_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        from lia_models.ai_consumption import AiConsumption

        since = datetime.utcnow() - timedelta(days=days)
        q = select(
            func.count(AiConsumption.id).label("executions"),
            func.coalesce(func.sum(AiConsumption.total_tokens), 0).label("tokens"),
            func.coalesce(func.sum(AiConsumption.cost_cents), 0).label("cost_cents"),
        ).where(
            and_(
                AiConsumption.company_id == company_id,
                AiConsumption.studio_agent_id == studio_agent_id,
                AiConsumption.created_at >= since,
            )
        )
        row = (await db.execute(q)).one()

        return {
            "studio_agent_id": studio_agent_id,
            "period_days": days,
            "executions": row.executions,
            "tokens": row.tokens,
            "cost_cents": row.cost_cents,
        }

    async def check_quota(
        self,
        db: AsyncSession,
        company_id: str,
        agent_type: str,
    ) -> tuple[bool, str]:
        from lia_models.agent_quota import AgentQuota, get_limits_for_plan

        result = await db.execute(
            select(AgentQuota).where(AgentQuota.company_id == company_id).with_for_update()
        )
        quota = result.scalar_one_or_none()

        if not quota:
            try:
                from app.domains.credits.services.token_budget_service import get_plan_for_company
                plan_code = await get_plan_for_company(company_id)
            except Exception:
                plan_code = "starter"
            limits = get_limits_for_plan(plan_code)
            quota = AgentQuota(
                company_id=company_id,
                plan_code=plan_code or "starter",
                **limits,
            )
            db.add(quota)
            await db.flush()

        field_map = {
            "sourcing_agent": ("active_sourcing_agents", "max_sourcing_agents"),
            "custom_agent": ("active_custom_agents", "max_custom_agents"),
            "digital_twin": ("active_digital_twins", "max_digital_twins"),
            "recruitment_campaign": ("active_campaigns", "max_campaigns"),
        }

        if agent_type not in field_map:
            return True, ""

        active_field, max_field = field_map[agent_type]
        active_count = getattr(quota, active_field, 0) or 0
        max_count = getattr(quota, max_field, -1)

        if max_count == -1:
            return True, ""

        if active_count >= max_count:
            return False, (
                f"Limite de {max_count} agente(s) do tipo '{agent_type}' atingido "
                f"para o plano '{quota.plan_code}'. Faça upgrade para criar mais."
            )
        return True, ""

    async def check_and_increment_quota(
        self,
        db: AsyncSession,
        company_id: str,
        agent_type: str,
    ) -> tuple[bool, str]:
        allowed, msg = await self.check_quota(db, company_id, agent_type)
        if not allowed:
            return False, msg
        await self.increment_active_count(db, company_id, agent_type)
        return True, ""

    async def increment_active_count(
        self,
        db: AsyncSession,
        company_id: str,
        agent_type: str,
    ) -> None:
        from lia_models.agent_quota import AgentQuota

        result = await db.execute(
            select(AgentQuota).where(AgentQuota.company_id == company_id)
        )
        quota = result.scalar_one_or_none()
        if not quota:
            return

        field_map = {
            "sourcing_agent": "active_sourcing_agents",
            "custom_agent": "active_custom_agents",
            "digital_twin": "active_digital_twins",
            "recruitment_campaign": "active_campaigns",
        }
        field = field_map.get(agent_type)
        if field:
            current = getattr(quota, field, 0) or 0
            setattr(quota, field, current + 1)
            await db.flush()

    async def decrement_active_count(
        self,
        db: AsyncSession,
        company_id: str,
        agent_type: str,
    ) -> None:
        from lia_models.agent_quota import AgentQuota

        result = await db.execute(
            select(AgentQuota).where(AgentQuota.company_id == company_id)
        )
        quota = result.scalar_one_or_none()
        if not quota:
            return

        field_map = {
            "sourcing_agent": "active_sourcing_agents",
            "custom_agent": "active_custom_agents",
            "digital_twin": "active_digital_twins",
            "recruitment_campaign": "active_campaigns",
        }
        field = field_map.get(agent_type)
        if field:
            current = getattr(quota, field, 0) or 0
            setattr(quota, field, max(0, current - 1))
            await db.flush()


studio_metering_service = StudioMeteringService()
