from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.credits.repositories.credits_repository import CreditsRepository


def get_credits_repo(db: AsyncSession = Depends(get_tenant_db)) -> CreditsRepository:
    return CreditsRepository(db)
