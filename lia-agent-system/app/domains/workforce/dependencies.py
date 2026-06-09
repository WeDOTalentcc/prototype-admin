"""
FastAPI dependency injection factories for the workforce domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.workforce_repository import WorkforceRepository


def get_workforce_repo(db: AsyncSession = Depends(get_tenant_db)) -> WorkforceRepository:
    return WorkforceRepository(db)
