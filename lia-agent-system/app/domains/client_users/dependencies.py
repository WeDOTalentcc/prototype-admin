"""Dependency injection for the client_users domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.client_user_repository import ClientUserRepository


def get_client_user_repo(db: AsyncSession = Depends(get_tenant_db)) -> ClientUserRepository:
    return ClientUserRepository(db)
