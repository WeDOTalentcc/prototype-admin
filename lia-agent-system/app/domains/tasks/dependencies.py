"""
Dependency injection factories for the tasks domain.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.repositories.tasks_repository import TasksRepository


def get_tasks_repo(db: AsyncSession = Depends(get_tenant_db)) -> TasksRepository:
    return TasksRepository(db)
