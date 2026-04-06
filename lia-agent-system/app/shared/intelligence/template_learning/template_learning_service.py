"""
Template Learning Service — G9.

Tracks email template performance (open/click rates) per company.
Uses MessageQueue + CommunicationLog + EmailTrackingEvent for persistent data:
- MessageQueue stores send events with template_id in extra_data
- CommunicationLog also stores template_id in extra_data (main send path)
- EmailTrackingEvent stores open/click events linked by notification_id
- Queries UNION both sources and join with tracking events for rates
"""
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TemplateLearningService:
    """
    Persistent template performance tracking.

    record_send/open/click are lightweight log-only signals.
    Actual data is derived from MessageQueue (sends) and
    EmailTrackingEvent (opens/clicks) via SQL joins.
    """

    def record_send(
        self,
        company_id: str,
        template_id: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "[TemplateLearning] send company=%s template=%s",
            company_id, template_id,
        )

    def record_open(self, company_id: str, template_id: str) -> None:
        logger.info(
            "[TemplateLearning] open company=%s template=%s",
            company_id, template_id,
        )

    def record_click(self, company_id: str, template_id: str) -> None:
        logger.info(
            "[TemplateLearning] click company=%s template=%s",
            company_id, template_id,
        )

    async def recommend_template(
        self,
        db: AsyncSession,
        company_id: str,
        context: dict[str, Any] | None = None,
        fallback_template_id: str = "default",
        min_sends: int = 5,
    ) -> str:
        """Return best-performing template_id for a company.

        Joins MessageQueue (sends with template_id in extra_data) and
        EmailTrackingEvent (opens) to compute open rates per template.
        """
        try:
            result = await db.execute(text("""
                WITH sends AS (
                    SELECT
                        mq.extra_data->>'template_id' AS template_id,
                        mq.id::text AS notification_id
                    FROM message_queue mq
                    WHERE mq.company_id = :company_id
                      AND mq.extra_data->>'template_id' IS NOT NULL
                    UNION ALL
                    SELECT
                        cl.extra_data->>'template_id' AS template_id,
                        cl.id::text AS notification_id
                    FROM communication_logs cl
                    WHERE cl.company_id = :company_id
                      AND cl.extra_data->>'template_id' IS NOT NULL
                ),
                deduped AS (
                    SELECT DISTINCT template_id, notification_id FROM sends
                ),
                stats AS (
                    SELECT
                        d.template_id,
                        COUNT(DISTINCT d.notification_id) AS send_count,
                        COUNT(DISTINCT CASE WHEN e.event_type = 'open' THEN e.notification_id END) AS open_count
                    FROM deduped d
                    LEFT JOIN email_tracking_events e ON e.notification_id = d.notification_id
                    GROUP BY d.template_id
                    HAVING COUNT(DISTINCT d.notification_id) >= :min_sends
                )
                SELECT template_id, send_count, open_count,
                       ROUND(open_count::numeric / NULLIF(send_count, 0), 4) AS open_rate
                FROM stats
                ORDER BY open_rate DESC NULLS LAST
                LIMIT 1
            """), {"company_id": company_id, "min_sends": min_sends})
            row = result.fetchone()

            if row:
                logger.debug(
                    "[TemplateLearning] recommend company=%s best=%s open_rate=%s",
                    company_id, row.template_id, row.open_rate,
                )
                return row.template_id
            return fallback_template_id
        except Exception as exc:
            logger.debug("[TemplateLearning] recommend fallback: %s", exc)
            return fallback_template_id

    async def get_performance(
        self,
        db: AsyncSession,
        company_id: str,
        template_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get performance metrics per template from persistent data."""
        try:
            params: dict[str, Any] = {"company_id": company_id}
            template_filter = ""
            if template_id:
                template_filter = "AND mq.extra_data->>'template_id' = :template_id"
                params["template_id"] = template_id

            result = await db.execute(text(f"""
                WITH sends AS (
                    SELECT
                        mq.extra_data->>'template_id' AS template_id,
                        mq.id::text AS notification_id
                    FROM message_queue mq
                    WHERE mq.company_id = :company_id
                      AND mq.extra_data->>'template_id' IS NOT NULL
                      {template_filter}
                    UNION ALL
                    SELECT
                        cl.extra_data->>'template_id' AS template_id,
                        cl.id::text AS notification_id
                    FROM communication_logs cl
                    WHERE cl.company_id = :company_id
                      AND cl.extra_data->>'template_id' IS NOT NULL
                      {template_filter.replace('mq.', 'cl.')}
                ),
                deduped AS (
                    SELECT DISTINCT template_id, notification_id FROM sends
                )
                SELECT
                    d.template_id,
                    COUNT(DISTINCT d.notification_id) AS sends,
                    COUNT(DISTINCT CASE WHEN e.event_type = 'open' THEN e.notification_id END) AS opens,
                    COUNT(DISTINCT CASE WHEN e.event_type = 'click' THEN e.notification_id END) AS clicks
                FROM deduped d
                LEFT JOIN email_tracking_events e ON e.notification_id = d.notification_id
                GROUP BY d.template_id
                ORDER BY sends DESC
            """), params)
            rows = result.fetchall()
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
