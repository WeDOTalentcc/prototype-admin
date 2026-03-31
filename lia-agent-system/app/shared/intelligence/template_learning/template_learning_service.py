"""
Template Learning Service — G9.

Tracks email template performance (open/click rates) per company using
persistent EmailTrackingEvent records. Recommends the best-performing
template variant for a given context.

Data is derived from EmailTrackingEvent table — no in-memory state.
Each webhook open/click records a tracking event that references the
template via resolve_company_template(). This service queries those
events for aggregated performance metrics.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TemplateLearningService:
    """
    Persistent template performance tracking via EmailTrackingEvent.

    Provides record_* methods (fire-and-forget counters via tracking events)
    and async query methods for recommendation and reporting.
    """

    def record_send(
        self,
        company_id: str,
        template_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        logger.debug(
            "[TemplateLearning] send recorded company=%s template=%s",
            company_id, template_id,
        )

    def record_open(self, company_id: str, template_id: str) -> None:
        logger.debug(
            "[TemplateLearning] open recorded company=%s template=%s",
            company_id, template_id,
        )

    def record_click(self, company_id: str, template_id: str) -> None:
        logger.debug(
            "[TemplateLearning] click recorded company=%s template=%s",
            company_id, template_id,
        )

    async def recommend_template(
        self,
        db: AsyncSession,
        company_id: str,
        context: Optional[Dict[str, Any]] = None,
        fallback_template_id: str = "default",
        min_sends: int = 5,
    ) -> str:
        """Return best-performing template_id for a company.

        Queries EmailTrackingEvent for aggregated open rates per template.
        Picks highest open_rate among templates with >= min_sends sends.
        """
        try:
            from app.models.email_tracking import EmailTrackingEvent

            stmt = (
                select(
                    func.split_part(EmailTrackingEvent.token, ":", 2).label("template_id"),
                    func.count().filter(
                        EmailTrackingEvent.event_type == "token"
                    ).label("sends"),
                    func.count().filter(
                        EmailTrackingEvent.event_type == "open"
                    ).label("opens"),
                )
                .where(
                    EmailTrackingEvent.company_id == company_id,
                    EmailTrackingEvent.event_type.in_(["token", "open"]),
                )
                .group_by("template_id")
                .having(func.count().filter(EmailTrackingEvent.event_type == "token") >= min_sends)
            )
            result = await db.execute(stmt)
            rows = result.all()

            if not rows:
                return fallback_template_id

            best = max(rows, key=lambda r: (r.opens / r.sends if r.sends > 0 else 0))
            logger.debug(
                "[TemplateLearning] recommend company=%s best=%s open_rate=%.2f",
                company_id, best.template_id, best.opens / best.sends if best.sends > 0 else 0,
            )
            return best.template_id
        except Exception as exc:
            logger.debug("[TemplateLearning] recommend fallback: %s", exc)
            return fallback_template_id

    async def get_performance(
        self,
        db: AsyncSession,
        company_id: str,
        template_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get performance metrics from persistent tracking events."""
        try:
            from app.models.email_tracking import EmailTrackingEvent

            conditions = [EmailTrackingEvent.company_id == company_id]
            if template_id:
                conditions.append(
                    func.split_part(EmailTrackingEvent.token, ":", 2) == template_id
                )

            stmt = (
                select(
                    func.split_part(EmailTrackingEvent.token, ":", 2).label("template_id"),
                    func.count().filter(EmailTrackingEvent.event_type == "token").label("sends"),
                    func.count().filter(EmailTrackingEvent.event_type == "open").label("opens"),
                    func.count().filter(EmailTrackingEvent.event_type == "click").label("clicks"),
                )
                .where(and_(*conditions))
                .group_by("template_id")
            )
            result = await db.execute(stmt)
            rows = result.all()
            return [
                {
                    "template_id": r.template_id,
                    "sends": r.sends,
                    "opens": r.opens,
                    "clicks": r.clicks,
                    "open_rate": round(r.opens / r.sends, 4) if r.sends > 0 else 0.0,
                    "click_rate": round(r.clicks / r.sends, 4) if r.sends > 0 else 0.0,
                }
                for r in rows
            ]
        except Exception as exc:
            logger.debug("[TemplateLearning] get_performance error: %s", exc)
            return []


template_learning_service = TemplateLearningService()
