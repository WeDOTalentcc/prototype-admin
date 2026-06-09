"""
Dependency injection for notifications domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.notifications_repository import NotificationsRepository


def get_notifications_repo(db: AsyncSession = Depends(get_tenant_db)) -> NotificationsRepository:
    return NotificationsRepository(db)
