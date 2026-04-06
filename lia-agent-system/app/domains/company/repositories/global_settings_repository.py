"""GlobalSettingsRepository - session-in-constructor pattern."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import GlobalSearchSettings

logger = logging.getLogger(__name__)


class GlobalSettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_company(self, company_id: str) -> GlobalSearchSettings | None:
        result = await self.db.execute(
            select(GlobalSearchSettings).where(
                GlobalSearchSettings.company_id == company_id
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self, company_id: str, data: dict
    ) -> GlobalSearchSettings:
        settings = await self.get_for_company(company_id)
        if settings:
            for key, value in data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        else:
            settings = GlobalSearchSettings(company_id=company_id, **data)
            self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
