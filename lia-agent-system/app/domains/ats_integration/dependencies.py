"""
FastAPI dependency injection for the ATS Integration domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.ats_integration.repositories.ats_repository import ATSRepository


def get_ats_repo(db: AsyncSession = Depends(get_tenant_db)) -> ATSRepository:
    return ATSRepository(db)
