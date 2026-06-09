"""
Dependency injection for admin_settings domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.admin_settings_repository import (
    AdminSettingsRepository,
)


def get_admin_settings_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> AdminSettingsRepository:
    return AdminSettingsRepository(db)
