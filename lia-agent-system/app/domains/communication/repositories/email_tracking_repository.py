"""EmailTrackingRepository — DB access for EmailTrackingEvent records.

Extracted from app/domains/communication/services/email_tracking_service.py per ADR-001.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.email_tracking import EmailTrackingEvent


class EmailTrackingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_base_event_by_token(self, token: str) -> EmailTrackingEvent | None:
        """Get base EmailTrackingEvent by token.

        Token is a globally-unique cryptographically random identifier embedded
        in tracking pixel URLs (open events) and tracked link URLs (click events).
        Query happens BEFORE the tenant is known (anonymous pixel/click handler).
        """
        # TENANT-EXEMPT: token is a globally-unique cryptographically random
        # identifier (UNIQUE column). The handler is anonymous (no auth/JWT) —
        # the tenant is derived FROM the row via EmailTrackingEvent.company_id.
        result = await self.db.execute(
            select(EmailTrackingEvent).where(
                EmailTrackingEvent.token == token,
                EmailTrackingEvent.event_type == "token",
            )
        )
        return result.scalar_one_or_none()

    async def count_by_event_type(
        self,
        *,
        notification_id: str,
        company_id: str,
    ) -> dict[str, int]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        stmt = (
            select(EmailTrackingEvent.event_type, func.count().label("count"))
            .where(
                EmailTrackingEvent.notification_id == notification_id,
                EmailTrackingEvent.company_id == company_id,
                EmailTrackingEvent.event_type.in_(["open", "click"]),
            )
            .group_by(EmailTrackingEvent.event_type)
        )
        result = await self.db.execute(stmt)
        return {row.event_type: row.count for row in result}

    async def count_unique_opens(
        self,
        *,
        notification_id: str,
        company_id: str,
    ) -> int:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        stmt = (
            select(func.count(EmailTrackingEvent.recipient_hash.distinct()).label("unique_opens"))
            .where(
                EmailTrackingEvent.notification_id == notification_id,
                EmailTrackingEvent.company_id == company_id,
                EmailTrackingEvent.event_type == "open",
                EmailTrackingEvent.recipient_hash.isnot(None),
            )
        )
        result = await self.db.execute(stmt)
        return int(result.scalar() or 0)

    async def find_message_queue_by_sg_id(self, sg_message_id: str):
        """Resolve MessageQueue row from sg_message_id via JSONB extra_data lookup."""
        from lia_models.message_queue import MessageQueue

        stmt = select(
            MessageQueue.id,
            MessageQueue.company_id,
            MessageQueue.extra_data,
        ).where(
            MessageQueue.extra_data["sg_message_id"].astext == sg_message_id,
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.first()

    async def find_communication_log_by_provider_message_id(self, sg_message_id: str):
        from app.domains.communication.services.communication_models import CommunicationLog

        stmt = select(
            CommunicationLog.company_id,
            CommunicationLog.extra_data,
        ).where(
            CommunicationLog.provider_message_id == sg_message_id,
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.first()
