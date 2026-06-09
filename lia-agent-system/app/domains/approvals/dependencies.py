from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_tenant_db
from app.repositories.approvals_repository import ApprovalsRepository


def get_approvals_repo(db: AsyncSession = Depends(get_tenant_db)) -> ApprovalsRepository:
    return ApprovalsRepository(db)
