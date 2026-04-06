"""
SerializableMixin - Standardized serialization for SQLAlchemy models.

Adds to_dict() and from_dict() to any SQLAlchemy model, making data
portable across frameworks (SQLAlchemy → ActiveRecord, Prisma, etc).
"""
import logging
from datetime import date, datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class SerializableMixin:
    """Mixin that adds serialization/deserialization to SQLAlchemy models.
    
    Usage:
        class MyModel(Base, SerializableMixin):
            __tablename__ = "my_table"
            ...
        
        # Serialize
        data = instance.to_dict()
        data = instance.to_dict(exclude={"password_hash"})
        data = instance.to_dict(include={"id", "name", "email"})
        
        # Deserialize
        instance = MyModel.from_dict(data)
    """
    
    _serialize_exclude: set[str] = set()
    
    _serialize_include: set[str] | None = None
    
    def to_dict(
        self,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        include_relationships: bool = False
    ) -> dict[str, Any]:
        """Convert model instance to dictionary.
        
        Args:
            include: Only include these fields (overrides class default)
            exclude: Exclude these fields (merged with class default)
            include_relationships: Include loaded relationships
            
        Returns:
            Dictionary representation of the model
        """
        result = {}
        
        fields_include = include or self._serialize_include
        fields_exclude = (exclude or set()) | self._serialize_exclude
        
        mapper = self.__class__.__mapper__ if hasattr(self.__class__, '__mapper__') else None
        if not mapper:
            return result
        
        for column in mapper.columns:
            key = column.key
            
            if fields_include and key not in fields_include:
                continue
            if key in fields_exclude:
                continue
            
            value = getattr(self, key, None)
            result[key] = self._serialize_value(value)
        
        if include_relationships and mapper.relationships:
            for rel in mapper.relationships:
                key = rel.key
                if fields_exclude and key in fields_exclude:
                    continue
                value = getattr(self, key, None)
                if value is None:
                    result[key] = None
                elif isinstance(value, list):
                    result[key] = [
                        item.to_dict() if hasattr(item, 'to_dict') else str(item)
                        for item in value
                    ]
                elif hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any], **kwargs) -> "SerializableMixin":
        """Create model instance from dictionary.
        
        Args:
            data: Dictionary with model data
            **kwargs: Additional fields to set
            
        Returns:
            New model instance (not yet added to session)
        """
        mapper = cls.__mapper__ if hasattr(cls, '__mapper__') else None
        if not mapper:
            return cls(**data, **kwargs)
        
        column_keys = {col.key for col in mapper.columns}
        filtered_data = {k: v for k, v in data.items() if k in column_keys}
        filtered_data.update(kwargs)
        
        return cls(**filtered_data)
    
    def update_from_dict(self, data: dict[str, Any], exclude: set[str] | None = None) -> "SerializableMixin":
        """Update model instance from dictionary.
        
        Args:
            data: Dictionary with updated fields
            exclude: Fields to skip
            
        Returns:
            Self for chaining
        """
        exclude = exclude or {"id", "created_at"}
        mapper = self.__class__.__mapper__ if hasattr(self.__class__, '__mapper__') else None
        column_keys = {col.key for col in mapper.columns} if mapper else set()
        
        for key, value in data.items():
            if key in exclude:
                continue
            if key in column_keys and hasattr(self, key):
                setattr(self, key, value)
        
        return self
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Convert a value to a JSON-serializable format."""
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, (list, tuple)):
            return [SerializableMixin._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: SerializableMixin._serialize_value(v) for k, v in value.items()}
        if hasattr(value, 'value'):  # Enum
            return value.value
        return value
