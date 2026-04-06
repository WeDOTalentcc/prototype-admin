"""
FastAPI dependency factories for the Trust Center domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.trust_center.repositories.trust_center_repository import (
    TrustCenterRepository,
)


def get_trust_center_repo(
    db: AsyncSession = Depends(get_db),
) -> TrustCenterRepository:
    return TrustCenterRepository(db)
