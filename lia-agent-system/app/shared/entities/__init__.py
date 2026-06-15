"""Entity type definitions for the WeDOTalent entity resolver.

Exported symbols:
    ENTITY_REGISTRY - dict[str, EntityTypeDefinition] with all supported types
    EntityTypeDefinition - dataclass with entity metadata
    get_entity_type - validates and returns EntityTypeDefinition by name
"""
from app.shared.entities.registry import ENTITY_REGISTRY, EntityTypeDefinition, get_entity_type

__all__ = ["ENTITY_REGISTRY", "EntityTypeDefinition", "get_entity_type"]
