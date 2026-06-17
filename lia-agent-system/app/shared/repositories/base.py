"""
Base Repository - Generic CRUD operations.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common CRUD operations.
    
    Subclass this for each model. Override methods to customize behavior.
    When migrating to Rails, implement this interface with ActiveRecord.
    """
    
    @abstractmethod
    async def get_by_id(self, id: UUID, db) -> T | None:
        """Find entity by primary key."""
        ...
    
    @abstractmethod
    async def list(self, db, filters: dict[str, Any] | None = None, 
                   limit: int = 50, offset: int = 0,
                   order_by: str | None = None) -> list[T]:
        """List entities with optional filtering and pagination."""
        ...
    
    @abstractmethod
    async def create(self, db, data: dict[str, Any]) -> T:
        """Create a new entity."""
        ...
    
    @abstractmethod
    async def update(self, db, id: UUID, data: dict[str, Any]) -> T | None:
        """Update an existing entity."""
        ...
    
    @abstractmethod
    async def delete(self, db, id: UUID) -> bool:
        """Delete an entity by ID."""
        ...
    
    @abstractmethod
    async def count(self, db, filters: dict[str, Any] | None = None) -> int:
        """Count entities matching filters."""
        ...
    
    @abstractmethod
    async def exists(self, db, id: UUID) -> bool:
        """Check if entity exists."""
        ...
