"""
SQLAlchemy implementation of BaseRepository.

Designed for async SQLAlchemy sessions (AsyncSession).
For sync sessions, subclass and override methods without async/await.

Portability note for Rails migration:
  - Replace SQLAlchemy queries with ActiveRecord equivalents
  - The BaseRepository ABC defines the interface contract
  - Each method maps to a standard ActiveRecord operation
"""
import logging
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SQLAlchemyRepository(BaseRepository[T]):
    """SQLAlchemy async implementation of the repository pattern.
    
    Requires AsyncSession. All methods are async.
    For sync usage, create a SyncSQLAlchemyRepository subclass.
    """
    
    model_class: type = None

    def __init__(self):
        if not self.model_class:
            raise ValueError(f"{self.__class__.__name__} must define model_class")

    async def get_by_id(self, id: UUID, db: AsyncSession) -> T | None:
        result = await db.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self, db: AsyncSession, filters=None, limit=50, offset=0, order_by=None
    ) -> list[T]:
        query = select(self.model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
        if order_by and hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by).desc())
        elif hasattr(self.model_class, 'created_at'):
            query = query.order_by(self.model_class.created_at.desc())
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, data: dict[str, Any]) -> T:
        instance = self.model_class(**data)
        db.add(instance)
        await db.flush()
        return instance

    async def update(self, db: AsyncSession, id: UUID, data: dict[str, Any]) -> T | None:
        instance = await self.get_by_id(id, db)
        if not instance:
            return None
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await db.flush()
        return instance

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        instance = await self.get_by_id(id, db)
        if not instance:
            return False
        await db.delete(instance)
        await db.flush()
        return True

    async def count(self, db: AsyncSession, filters=None) -> int:
        query = select(func.count()).select_from(self.model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
        result = await db.execute(query)
        return result.scalar() or 0

    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        return await self.get_by_id(id, db) is not None
