"""
FastAPI dependency factories for the Health Check domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.health_check.repositories.health_check_repository import (
    HealthCheckRepository,
)


def get_health_check_repo(
    db: AsyncSession = Depends(get_db),
) -> HealthCheckRepository:
    return HealthCheckRepository(db)
