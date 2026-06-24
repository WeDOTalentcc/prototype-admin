"""Entity type definitions — single source of truth for EntityResolver.

Each EntityTypeDefinition carries the metadata needed to:
  - locate the unique identifier field in a DB row
  - know which fields to search against user input
  - know what to display in a disambiguation list

Multi-tenancy: company_id is always enforced by the caller / repository layer,
NOT here. This module is purely structural metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EntityTypeDefinition:
    name: str                     # Display name, e.g. "Candidate"
    unique_id_field: str          # Primary key field name in DB row, e.g. "candidate_id"
    searchable_fields: list[str]  # Fields fuzzy-matched against user input
    display_fields: list[str]     # Fields included in disambiguation display name
    table_name: str               # DB table (informational — queries handled by callers)


ENTITY_REGISTRY: dict[str, EntityTypeDefinition] = {
    "candidate": EntityTypeDefinition(
        name="Candidate",
        unique_id_field="candidate_id",
        searchable_fields=["name", "first_name", "last_name", "email"],
        display_fields=["name", "email"],
        table_name="candidates",
    ),
    "job": EntityTypeDefinition(
        name="Job",
        unique_id_field="job_id",
        searchable_fields=["title", "department"],
        display_fields=["title", "department"],
        table_name="job_vacancies",
    ),
    "company": EntityTypeDefinition(
        name="Company",
        unique_id_field="company_id",
        searchable_fields=["name", "trade_name"],
        display_fields=["name"],
        table_name="companies",
    ),
    "user": EntityTypeDefinition(
        name="User",
        unique_id_field="user_id",
        searchable_fields=["name", "first_name", "last_name", "email"],
        display_fields=["name", "email"],
        table_name="users",
    ),
}


def get_entity_type(entity_type: str) -> EntityTypeDefinition:
    """Return EntityTypeDefinition for entity_type, raise ValueError for unknown."""
    key = entity_type.lower()
    if key not in ENTITY_REGISTRY:
        valid = ", ".join(sorted(ENTITY_REGISTRY.keys()))
        raise ValueError(
            f"Unknown entity type {entity_type}. Valid types: {valid}"
        )
    return ENTITY_REGISTRY[key]
