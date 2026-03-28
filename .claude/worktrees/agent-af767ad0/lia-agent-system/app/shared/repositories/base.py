"""
Base Repository - Generic CRUD operations.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any, Type
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository with common CRUD operations.
    
    Subclass this for each model. Override methods to customize behavior.
    When migrating to Rails, implement this interface with ActiveRecord.
    """
    
    @abstractmethod
    async def get_by_id(self, id: UUID, db) -> Optional[T]:
        """Find entity by primary key."""
        ...
    
    @abstractmethod
    async def list(self, db, filters: Optional[Dict[str, Any]] = None, 
                   limit: int = 50, offset: int = 0,
                   order_by: Optional[str] = None) -> List[T]:
        """List entities with optional filtering and pagination."""
        ...
    
    @abstractmethod
    async def create(self, db, data: Dict[str, Any]) -> T:
        """Create a new entity."""
        ...
    
    @abstractmethod
    async def update(self, db, id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing entity."""
        ...
    
    @abstractmethod
    async def delete(self, db, id: UUID) -> bool:
        """Delete an entity by ID."""
        ...
    
    @abstractmethod
    async def count(self, db, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        ...
    
    @abstractmethod
    async def exists(self, db, id: UUID) -> bool:
        """Check if entity exists."""
        ...
