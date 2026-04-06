"""
Dependency injection for admin_settings domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.admin_settings.repositories.admin_settings_repository import (
    AdminSettingsRepository,
)


def get_admin_settings_repo(
    db: AsyncSession = Depends(get_db),
) -> AdminSettingsRepository:
    return AdminSettingsRepository(db)
