"""
Dependency injection for admin domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.admin_repository import AdminRepository


def get_admin_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> AdminRepository:
    return AdminRepository(db)
