"""
Dependency injection for shared_searches domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.shared_search_repository import (
    SharedSearchRepository,
)


def get_shared_search_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> SharedSearchRepository:
    return SharedSearchRepository(db)
