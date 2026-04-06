"""
Dependency injection functions for the clients domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.clients.repositories.client_account_repository import ClientAccountRepository


def get_client_repo(db: AsyncSession = Depends(get_db)) -> ClientAccountRepository:
    return ClientAccountRepository(db)
