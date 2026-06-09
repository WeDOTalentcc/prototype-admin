"""Dependency injection functions for observability domain repositories."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.observability_repository import ObservabilityRepository


def get_observability_repo(db: AsyncSession = Depends(get_tenant_db)) -> ObservabilityRepository:
    return ObservabilityRepository(db)
