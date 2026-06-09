"""
Dependency injection for opinions domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.opinions_repository import OpinionsRepository


def get_opinions_repo(db: AsyncSession = Depends(get_tenant_db)) -> OpinionsRepository:
    return OpinionsRepository(db)
