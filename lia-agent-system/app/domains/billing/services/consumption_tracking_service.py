import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.external_api_consumption import ExternalApiConsumption

logger = logging.getLogger(__name__)

APIFY_USD_TO_BRL_RATE = float(os.environ.get("APIFY_USD_TO_BRL_RATE", "5.50"))
APIFY_MONTHLY_BUDGET_USD = float(os.environ.get("APIFY_MONTHLY_BUDGET_USD", "100.00"))


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
    ) -> ExternalApiConsumption:
        from uuid import UUID as _UUID
        rate = APIFY_USD_TO_BRL_RATE
        record = ExternalApiConsumption(
            company_id=company_id,
            user_id=user_id,
            candidate_id=_UUID(str(candidate_id)) if candidate_id else None,
            linkedin_url=linkedin_url,
            provider="apify",
            operation=operation,
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

        await ConsumptionTrackingService._check_budget_alert(db, company_id)

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
    ) -> ExternalApiConsumption:
        record = ExternalApiConsumption(
            company_id=company_id,
            user_id=user_id,
            provider="pearch",
            operation=operation,
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
        return record

    _budget_alerts_sent: dict[str, str] = {}

    @staticmethod
    async def _check_budget_alert(db: AsyncSession, company_id: str) -> None:
        now = datetime.utcnow()
        month_key = f"{company_id}:{now.year}-{now.month:02d}"

        if month_key in ConsumptionTrackingService._budget_alerts_sent:
            return

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
        total_usd = result.scalar() or 0.0

        if total_usd >= APIFY_MONTHLY_BUDGET_USD:
            ConsumptionTrackingService._budget_alerts_sent[month_key] = now.isoformat()
            logger.warning(
                "[ConsumptionTracking] BUDGET ALERT: company=%s monthly Apify spend $%.2f >= budget $%.2f",
                company_id, total_usd, APIFY_MONTHLY_BUDGET_USD,
            )
            try:
                from app.domains.analytics.services.activity_service import ActivityService
                activity_svc = ActivityService()
                await activity_svc.create_activity(
                    activity_type="budget_alert",
                    title="Alerta de Orçamento Apify",
                    description=f"Consumo Apify mensal atingiu ${total_usd:.2f} (limite: ${APIFY_MONTHLY_BUDGET_USD:.2f})",
                    summary=f"Consumo: ${total_usd:.2f} / ${APIFY_MONTHLY_BUDGET_USD:.2f}",
                    actor_id="system",
                    actor_name="Sistema",
                    actor_type="system",
                    target_id=company_id,
                    target_name=company_id,
                    target_type="company",
                    extra_data={
                        "total_usd": round(total_usd, 2),
                        "budget_usd": APIFY_MONTHLY_BUDGET_USD,
                        "usage_percentage": round((total_usd / APIFY_MONTHLY_BUDGET_USD) * 100, 1),
                    },
                    priority="urgent",
                    category="billing",
                )
            except Exception as e:
                logger.error("[ConsumptionTracking] Failed to create budget alert activity: %s", e)

            try:
                from app.services.notification_service import NotificationService, NotificationType
                notif_svc = NotificationService()
                usage_pct = round((total_usd / APIFY_MONTHLY_BUDGET_USD) * 100, 1)
                await notif_svc.create_notification(
                    user_id="system",
                    title="Alerta de Orçamento Apify",
                    message=(
                        f"O consumo mensal de Apify atingiu ${total_usd:.2f} USD "
                        f"({usage_pct}% do limite de ${APIFY_MONTHLY_BUDGET_USD:.2f} USD)."
                    ),
                    notification_type=NotificationType.URGENT,
                    category="billing",
                    source_agent="consumption_tracking",
                    source_trigger="budget_threshold",
                    metadata={
                        "company_id": company_id,
                        "total_usd": round(total_usd, 2),
                        "budget_usd": APIFY_MONTHLY_BUDGET_USD,
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
