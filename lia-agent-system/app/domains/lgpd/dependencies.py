"""Dependency injection factories for the LGPD domain."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.lgpd.repositories.lgpd_repository import LGPDRepository


def get_lgpd_repo(db: AsyncSession = Depends(get_tenant_db)) -> LGPDRepository:
    return LGPDRepository(db)
