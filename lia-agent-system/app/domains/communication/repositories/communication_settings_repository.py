"""
CommunicationSettingsRepository — data access for per-company communication settings.
Extracted from app/api/v1/communication_settings.py as part of Phase 2 refactor.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CommunicationSettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_company_id(self, company_id: str):
        """Return CommunicationSettings for company, or None."""
        from app.models.communication_settings import CommunicationSettings

        result = await self.db.execute(
            select(CommunicationSettings).where(
                CommunicationSettings.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, company_id: str, update_data: dict):
        """Create or update CommunicationSettings; flush and refresh; return instance."""
        from app.models.communication_settings import (
            DEFAULT_COMMUNICATION_SETTINGS,
            CommunicationSettings,
        )

        settings = await self.get_by_company_id(company_id)
        if settings:
            for field, value in update_data.items():
                setattr(settings, field, value)
            settings.updated_at = datetime.utcnow()
        else:
            settings_data = {**DEFAULT_COMMUNICATION_SETTINGS}
            settings_data.update(update_data)
            settings_data["company_id"] = company_id
            settings = CommunicationSettings(**settings_data)
            self.db.add(settings)

        await self.db.flush()
        await self.db.refresh(settings)
        return settings
