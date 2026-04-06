"""
FastAPI dependency factories for the Compliance domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.compliance.repositories.compliance_controls_repository import (
    ComplianceControlsRepository,
)


def get_compliance_repo(
    db: AsyncSession = Depends(get_db),
) -> ComplianceControlsRepository:
    return ComplianceControlsRepository(db)
