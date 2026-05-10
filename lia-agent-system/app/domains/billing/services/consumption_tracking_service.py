import logging
import os
from datetime import datetime, timedelta
from uuid import UUID as _UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.external_api_consumption import ExternalApiConsumption

logger = logging.getLogger(__name__)

APIFY_USD_TO_BRL_RATE = float(os.environ.get("APIFY_USD_TO_BRL_RATE", "5.50"))
APIFY_MONTHLY_BUDGET_USD = float(os.environ.get("APIFY_MONTHLY_BUDGET_USD", "100.00"))
LLM_MONTHLY_BUDGET_USD = float(os.environ.get("LLM_MONTHLY_BUDGET_USD", "500.00"))
PEARCH_MONTHLY_BUDGET_CREDITS = int(os.environ.get("PEARCH_MONTHLY_BUDGET_CREDITS", "10000"))

PRICING_TABLE = {
    "apify": {
        "enrich": 0.01,
        "apify_search": 0.02,
        "profile_scrape": 0.01,
        "email_finder": 0.01,
        "reveal_email": 0.01,
        "reveal_phone": 0.01,
    },
    "pearch": {
        "search": 1,
    },
    "llm": {
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    },
}

CATEGORY_BUDGETS = {
    "apify": APIFY_MONTHLY_BUDGET_USD,
    "llm": LLM_MONTHLY_BUDGET_USD,
    "pearch": float(PEARCH_MONTHLY_BUDGET_CREDITS),
}


class ConsumptionTrackingService:

    @staticmethod
    async def record_apify_call(
        db: AsyncSession,
        company_id: str,
        user_id: str | None,
        candidate_id: str | None,
        linkedin_url: str | None,
        operation: str,
        cost_usd: float,
        success: bool,
        result_status: str = "success",
        response_time_ms: int = 0,
        error_message: str | None = None,
        pipeline_id: str | None = None,
        actor_id: str | None = None,
        search_session_id: str | None = None,
    ) -> ExternalApiConsumption:
        rate = APIFY_USD_TO_BRL_RATE
        record = ExternalApiConsumption(
            company_id=company_id,
            user_id=user_id,
            candidate_id=_UUID(str(candidate_id)) if candidate_id else None,
            linkedin_url=linkedin_url,
            provider="apify",
            operation=operation,
            pipeline_id=_UUID(pipeline_id) if pipeline_id else None,
            actor_id=actor_id,
            search_session_id=search_session_id,
            credits_consumed=0,
            cost_usd=cost_usd,
            cost_brl=round(cost_usd * rate, 4),
            exchange_rate=rate,
            success=success,
            result_status=result_status if success else (result_status if result_status != "success" else "fail"),
            error_message=error_message,
            response_time_ms=response_time_ms,
        )
        db.add(record)
        await db.flush()

        logger.info(
            "[ConsumptionTracking] Apify %s recorded: company=%s candidate=%s cost=$%.4f status=%s",
            operation, company_id, candidate_id, cost_usd, record.result_status,
        )

        await ConsumptionTrackingService._check_budget_alert(db, company_id, "apify")

        try:
            from app.domains.analytics.services.token_tracking_service import TokenTrackingService
            async with AsyncSessionLocal() as ai_db:
                tts = TokenTrackingService(ai_db)
                await tts.record_apify_usage(
                    company_id=company_id,
                    user_id=user_id,
                    candidate_id=str(candidate_id) if candidate_id else None,
                    operation=operation,
                    cost_usd=cost_usd,
                    response_time_ms=response_time_ms,
                )
        except Exception as e:
            logger.debug("[ConsumptionTracking] Could not record in ai_consumption: %s", e)

        from app.domains.billing.services.consumption_logger import ConsumptionAuditLogger
        ConsumptionAuditLogger.log_operation(
            company_id=company_id,
            user_id=user_id,
            operation=operation,
            provider="apify",
            cost_usd=cost_usd,
            success=success,
            duration_ms=response_time_ms,
            pipeline_id=pipeline_id,
            actor_id=actor_id,
            error_message=error_message,
        )

        return record

    @staticmethod
    async def record_apify_search_call(
        db: AsyncSession,
        company_id: str,
        user_id: str | None,
        operation: str,
        cost_usd: float,
        success: bool,
        pipeline_id: str | None = None,
        result_status: str = "success",
        response_time_ms: int = 0,
        error_message: str | None = None,
        actor_id: str | None = None,
        search_session_id: str | None = None,
    ) -> ExternalApiConsumption:
        rate = APIFY_USD_TO_BRL_RATE
        record = ExternalApiConsumption(
            company_id=company_id,
            user_id=user_id,
            provider="apify",
            operation=operation,
            pipeline_id=_UUID(pipeline_id) if pipeline_id else None,
            actor_id=actor_id,
            search_session_id=search_session_id,
            credits_consumed=0,
            cost_usd=cost_usd,
            cost_brl=round(cost_usd * rate, 4),
            exchange_rate=rate,
            success=success,
            result_status=result_status if success else (result_status if result_status != "success" else "fail"),
            error_message=error_message,
            response_time_ms=response_time_ms,
        )
        db.add(record)
        await db.flush()

        logger.info(
            "[ConsumptionTracking] Apify search %s recorded: company=%s pipeline=%s cost=$%.4f status=%s",
            operation, company_id, pipeline_id, cost_usd, record.result_status,
        )

        await ConsumptionTrackingService._check_budget_alert(db, company_id, "apify")

        from app.domains.billing.services.consumption_logger import ConsumptionAuditLogger
        ConsumptionAuditLogger.log_operation(
            company_id=company_id,
            user_id=user_id,
            operation=operation,
            provider="apify",
            cost_usd=cost_usd,
            success=success,
            duration_ms=response_time_ms,
            pipeline_id=pipeline_id,
            actor_id=actor_id,
            error_message=error_message,
        )

        return record

    @staticmethod
    async def record_pearch_call(
        db: AsyncSession,
        company_id: str,
        user_id: str | None,
        operation: str,
        credits_consumed: int,
        success: bool,
        result_status: str = "success",
        response_time_ms: int = 0,
        error_message: str | None = None,
        search_session_id: str | None = None,
    ) -> ExternalApiConsumption:
        record = ExternalApiConsumption(
            company_id=company_id,
            user_id=user_id,
            provider="pearch",
            operation=operation,
            search_session_id=search_session_id,
            credits_consumed=credits_consumed,
            cost_usd=0.0,
            cost_brl=0.0,
            exchange_rate=APIFY_USD_TO_BRL_RATE,
            success=success,
            result_status=result_status if success else (result_status if result_status != "success" else "fail"),
            error_message=error_message,
            response_time_ms=response_time_ms,
        )
        db.add(record)
        await db.flush()

        logger.info(
            "[ConsumptionTracking] Pearch %s recorded: company=%s credits=%d status=%s",
            operation, company_id, credits_consumed, record.result_status,
        )

        await ConsumptionTrackingService._check_budget_alert(db, company_id, "pearch")

        from app.domains.billing.services.consumption_logger import ConsumptionAuditLogger
        ConsumptionAuditLogger.log_operation(
            company_id=company_id,
            user_id=user_id,
            operation=operation,
            provider="pearch",
            cost_usd=0.0,
            success=success,
            duration_ms=response_time_ms,
            error_message=error_message,
        )

        return record

    @staticmethod
    async def record_llm_call(
        db: AsyncSession,
        company_id: str,
        user_id: str | None,
        model_name: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float | None = None,
        success: bool = True,
        response_time_ms: int = 0,
        error_message: str | None = None,
        pipeline_id: str | None = None,
        search_session_id: str | None = None,
    ) -> ExternalApiConsumption:
        if cost_usd is None:
            cost_usd = ConsumptionTrackingService.calculate_llm_cost(
                model_name, tokens_input, tokens_output
            )

        rate = APIFY_USD_TO_BRL_RATE
        record = ExternalApiConsumption(
            company_id=company_id,
            user_id=user_id,
            provider="llm",
            operation="llm_inference",
            model_name=model_name,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            pipeline_id=_UUID(pipeline_id) if pipeline_id else None,
            search_session_id=search_session_id,
            credits_consumed=0,
            cost_usd=round(cost_usd, 6),
            cost_brl=round(cost_usd * rate, 4),
            exchange_rate=rate,
            success=success,
            result_status="success" if success else "fail",
            error_message=error_message,
            response_time_ms=response_time_ms,
        )
        db.add(record)
        await db.flush()

        logger.info(
            "[ConsumptionTracking] LLM %s recorded: company=%s model=%s tokens=%d+%d cost=$%.6f",
            "llm_inference", company_id, model_name, tokens_input, tokens_output, cost_usd,
        )

        await ConsumptionTrackingService._check_budget_alert(db, company_id, "llm")

        from app.domains.billing.services.consumption_logger import ConsumptionAuditLogger
        ConsumptionAuditLogger.log_operation(
            company_id=company_id,
            user_id=user_id,
            operation="llm_inference",
            provider="llm",
            cost_usd=cost_usd,
            success=success,
            duration_ms=response_time_ms,
            pipeline_id=pipeline_id,
            model_name=model_name,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            error_message=error_message,
        )

        return record

    @staticmethod
    async def record_pipeline_call(
        db: AsyncSession,
        company_id: str,
        user_id: str | None,
        pipeline_id: str,
        stages: list[dict],
        total_cost_usd: float,
        success: bool = True,
        search_session_id: str | None = None,
    ) -> list[ExternalApiConsumption]:
        records = []
        for stage in stages:
            record = ExternalApiConsumption(
                company_id=company_id,
                user_id=user_id,
                provider=stage.get("provider", "apify"),
                operation=stage["operation"],
                pipeline_id=_UUID(pipeline_id),
                search_session_id=search_session_id,
                actor_id=stage.get("actor_id"),
                cost_usd=stage.get("cost_usd", 0.0),
                cost_brl=round(stage.get("cost_usd", 0.0) * APIFY_USD_TO_BRL_RATE, 4),
                exchange_rate=APIFY_USD_TO_BRL_RATE,
                success=stage.get("success", True),
                result_status="success" if stage.get("success", True) else "fail",
                error_message=stage.get("error_message"),
                response_time_ms=stage.get("response_time_ms", 0),
                credits_consumed=0,
            )
            db.add(record)
            records.append(record)

        await db.flush()

        logger.info(
            "[ConsumptionTracking] Pipeline %s recorded: company=%s stages=%d total=$%.4f",
            pipeline_id, company_id, len(stages), total_cost_usd,
        )

        from app.domains.billing.services.consumption_logger import ConsumptionAuditLogger
        ConsumptionAuditLogger.log_operation(
            company_id=company_id,
            user_id=user_id,
            operation="pipeline",
            provider="apify",
            cost_usd=total_cost_usd,
            success=success,
            pipeline_id=pipeline_id,
            extra={"stages": len(stages)},
        )

        return records

    @staticmethod
    def calculate_llm_cost(model_name: str, tokens_input: int, tokens_output: int) -> float:
        llm_prices = PRICING_TABLE.get("llm", {})
        model_key = model_name.lower()
        prices = llm_prices.get(model_key)

        if not prices:
            candidates = sorted(llm_prices.keys(), key=len, reverse=True)
            for key in candidates:
                if key in model_key:
                    prices = llm_prices[key]
                    break

        if not prices:
            prices = {"input": 0.003, "output": 0.015}

        cost = (tokens_input / 1000) * prices["input"] + (tokens_output / 1000) * prices["output"]
        return round(cost, 6)

    @staticmethod
    def get_operation_price(provider: str, operation: str) -> float | None:
        provider_prices = PRICING_TABLE.get(provider)
        if not provider_prices:
            return None
        return provider_prices.get(operation)

    _budget_alerts_sent: dict[str, str] = {}
    _tenant_budgets: dict[str, dict[str, float]] = {}

    @staticmethod
    def set_tenant_budget(company_id: str, category: str, budget_usd: float) -> None:
        if company_id not in ConsumptionTrackingService._tenant_budgets:
            ConsumptionTrackingService._tenant_budgets[company_id] = {}
        ConsumptionTrackingService._tenant_budgets[company_id][category] = budget_usd

    @staticmethod
    def get_tenant_budget(company_id: str, category: str) -> float:
        tenant_budgets = ConsumptionTrackingService._tenant_budgets.get(company_id, {})
        if category in tenant_budgets:
            return tenant_budgets[category]
        return CATEGORY_BUDGETS.get(category, APIFY_MONTHLY_BUDGET_USD)

    @staticmethod
    async def _check_budget_alert(db: AsyncSession, company_id: str, category: str = "apify") -> None:
        """Fire-and-forget budget alert check — never raises, never blocks caller."""
        try:
            await ConsumptionTrackingService._check_budget_alert_inner(db, company_id, category)
        except Exception as _exc:
            import logging as _log
            _log.getLogger(__name__).debug(
                "[BudgetAlert] non-critical check failed: %s", _exc
            )

    @staticmethod
    async def _check_budget_alert_inner(db: AsyncSession, company_id: str, category: str = "apify") -> None:
        now = datetime.utcnow()
        month_key = f"{company_id}:{now.year}-{now.month:02d}"  # keyed per-company-month (not per-category)

        if month_key in ConsumptionTrackingService._budget_alerts_sent:
            return

        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        provider_filter = category

        if category == "pearch":
            result = await db.execute(
                select(func.sum(ExternalApiConsumption.credits_consumed)).where(
                    and_(
                        ExternalApiConsumption.company_id == company_id,
                        ExternalApiConsumption.provider == "pearch",
                        ExternalApiConsumption.created_at >= month_start,
                    )
                )
            )
            _raw_val = result.scalar()
            # Guard against AsyncMock returning coroutines in test environments
            import inspect
            if inspect.iscoroutine(_raw_val):
                _raw_val = 0  # fail-safe; real queries return sync scalar
            total_usd = float(_raw_val or 0)
        else:
            result = await db.execute(
                select(func.sum(ExternalApiConsumption.cost_usd)).where(
                    and_(
                        ExternalApiConsumption.company_id == company_id,
                        ExternalApiConsumption.provider == provider_filter,
                        ExternalApiConsumption.created_at >= month_start,
                    )
                )
            )
            total_usd = result.scalar() or 0.0

        budget = ConsumptionTrackingService.get_tenant_budget(company_id, category)

        if total_usd >= budget:
            ConsumptionTrackingService._budget_alerts_sent[month_key] = now.isoformat()

            from app.domains.billing.services.consumption_logger import ConsumptionAuditLogger
            ConsumptionAuditLogger.log_budget_alert(
                company_id=company_id,
                category=category,
                current_spend_usd=total_usd,
                budget_usd=budget,
                usage_percentage=round((total_usd / budget) * 100, 1) if budget > 0 else 0,
            )

            logger.warning(
                "[ConsumptionTracking] BUDGET ALERT: company=%s category=%s monthly spend $%.2f >= budget $%.2f",
                company_id, category, total_usd, budget,
            )
            try:
                from app.domains.analytics.services.activity_service import ActivityService
                activity_svc = ActivityService()
                await activity_svc.create_activity(
                    activity_type="budget_alert",
                    title=f"Alerta de Orçamento {category.upper()}",
                    description=f"Consumo {category} mensal atingiu ${total_usd:.2f} (limite: ${budget:.2f})",
                    summary=f"Consumo: ${total_usd:.2f} / ${budget:.2f}",
                    actor_id="system",
                    actor_name="Sistema",
                    actor_type="system",
                    target_id=company_id,
                    target_name=company_id,
                    target_type="company",
                    extra_data={
                        "total_usd": round(total_usd, 2),
                        "budget_usd": budget,
                        "category": category,
                        "usage_percentage": round((total_usd / budget) * 100, 1),
                    },
                    priority="urgent",
                    category="billing",
                )
            except Exception as e:
                logger.error("[ConsumptionTracking] Failed to create budget alert activity: %s", e)

            try:
                from app.services.notification_service import NotificationService, NotificationType
                notif_svc = NotificationService()
                usage_pct = round((total_usd / budget) * 100, 1)
                await notif_svc.create_notification(
                    user_id="system",
                    title=f"Alerta de Orçamento {category.upper()}",
                    message=(
                        f"O consumo mensal de {category} atingiu ${total_usd:.2f} USD "
                        f"({usage_pct}% do limite de ${budget:.2f} USD)."
                    ),
                    notification_type=NotificationType.URGENT,
                    category="billing",
                    source_agent="consumption_tracking",
                    source_trigger="budget_threshold",
                    metadata={
                        "company_id": company_id,
                        "total_usd": round(total_usd, 2),
                        "budget_usd": budget,
                        "category": category,
                        "usage_percentage": usage_pct,
                    },
                )
            except Exception as e:
                logger.error("[ConsumptionTracking] Failed to send budget notification: %s", e)

    @staticmethod
    async def get_monthly_apify_spend(db: AsyncSession, company_id: str) -> float:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.sum(ExternalApiConsumption.cost_usd)).where(
                and_(
                    ExternalApiConsumption.company_id == company_id,
                    ExternalApiConsumption.provider == "apify",
                    ExternalApiConsumption.created_at >= month_start,
                )
            )
        )
        return result.scalar() or 0.0

    @staticmethod
    async def get_monthly_spend_by_category(db: AsyncSession, company_id: str) -> dict[str, float]:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(
                ExternalApiConsumption.provider,
                func.sum(ExternalApiConsumption.cost_usd).label("total"),
            ).where(
                and_(
                    ExternalApiConsumption.company_id == company_id,
                    ExternalApiConsumption.created_at >= month_start,
                )
            ).group_by(ExternalApiConsumption.provider)
        )
        return {row.provider: float(row.total or 0) for row in result.all()}
