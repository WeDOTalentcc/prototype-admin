"""
Dependency injection functions for goals domain repositories.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from .repositories.goals_repository import GoalsRepository


def get_goals_repo(db: AsyncSession = Depends(get_db)) -> GoalsRepository:
    return GoalsRepository(db)
