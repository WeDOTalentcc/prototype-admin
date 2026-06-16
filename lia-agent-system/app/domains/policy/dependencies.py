"""
Dependency injection functions for the policy domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.policy.repositories.policy_repository import PolicyRepository


def get_policy_repo(db: AsyncSession = Depends(get_tenant_db)) -> PolicyRepository:
    return PolicyRepository(db)
