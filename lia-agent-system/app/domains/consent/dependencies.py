"""
FastAPI dependency factories for the Consent domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.consent_repository import ConsentRepository


def get_consent_repo(
    db: AsyncSession = Depends(get_tenant_db),
) -> ConsentRepository:
    return ConsentRepository(db)
