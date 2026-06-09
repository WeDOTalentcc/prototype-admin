"""Dependency injection for the saas_metrics domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.saas_metrics_repository import (
    SaasMetricsRepository,
)


def get_saas_metrics_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> SaasMetricsRepository:
    return SaasMetricsRepository(db)
