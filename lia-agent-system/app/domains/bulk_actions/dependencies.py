"""
Dependency injection for bulk_actions domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.bulk_actions_repository import BulkActionsRepository


def get_bulk_actions_repo(db: AsyncSession = Depends(get_tenant_db)) -> BulkActionsRepository:
    return BulkActionsRepository(db)
