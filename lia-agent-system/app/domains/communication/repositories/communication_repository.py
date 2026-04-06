"""
Communication domain repository — handles DB operations for CommunicationLog.
"""
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.services.communication_service import CommunicationLog


class CommunicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_log_by_provider_message_id(
        self, message_id: str, values: dict
    ) -> int:
        """Update CommunicationLog record(s) matching provider_message_id.

        Returns the number of rows updated.
        """
        result = await self.db.execute(
            update(CommunicationLog)
            .where(CommunicationLog.provider_message_id == message_id)
            .values(**values)
        )
        await self.db.commit()
        return result.rowcount  # type: ignore[union-attr]
