"""
Alert Repository — data access layer for alert configs and preferences.
Extracted from app/api/v1/alerts.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertConfig, AlertPreference

logger = logging.getLogger(__name__)


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_configs_for_company(self, company_id: str) -> list[AlertConfig]:
        result = await self.db.execute(
            select(AlertConfig).where(AlertConfig.company_id == company_id)
            .order_by(AlertConfig.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_config_by_id(self, config_id: UUID) -> AlertConfig | None:
        result = await self.db.execute(
            select(AlertConfig).where(AlertConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def create_config(self, data: dict) -> AlertConfig:
        cfg = AlertConfig(**data)
        self.db.add(cfg)
        await self.db.flush()
        await self.db.refresh(cfg)
        return cfg

    async def update_config(self, config: AlertConfig, data: dict) -> AlertConfig:
        for key, value in data.items():
            setattr(config, key, value)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete_config(self, config: AlertConfig) -> None:
        await self.db.delete(config)
        await self.db.flush()

    async def get_preference(self, user_id: str) -> AlertPreference | None:
        result = await self.db.execute(
            select(AlertPreference).where(AlertPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_preference(self, user_id: str, data: dict) -> AlertPreference:
        pref = await self.get_preference(user_id)
        if pref:
            for key, value in data.items():
                setattr(pref, key, value)
        else:
            pref = AlertPreference(user_id=user_id, **data)
            self.db.add(pref)
        await self.db.flush()
        await self.db.refresh(pref)
        return pref
