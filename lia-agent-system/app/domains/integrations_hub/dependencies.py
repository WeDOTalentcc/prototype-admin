"""
Dependency injection for integrations_hub domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.integrations_hub.repositories.integrations_hub_repository import (
    IntegrationsHubRepository,
)


def get_integrations_hub_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> IntegrationsHubRepository:
    return IntegrationsHubRepository(db)
