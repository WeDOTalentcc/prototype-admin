"""Dependency injection functions for journey_mapping domain repositories."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.journey_mapping_repository import JourneyMappingRepository


def get_journey_mapping_repo(db: AsyncSession = Depends(get_tenant_db)) -> JourneyMappingRepository:
    return JourneyMappingRepository(db)
