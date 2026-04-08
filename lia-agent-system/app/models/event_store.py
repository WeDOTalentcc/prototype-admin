"""Backwards-compatibility shim — real implementation in libs/models.

DomainEvent model columns (for schema reference):
    aggregate_type: str — type of the aggregate (e.g. "candidate", "job")
    aggregate_id: str — identifier of the aggregate
    event_type: str — name of the event
    sequence: int — ordering sequence
    payload: dict — event data
    metadata: dict — additional metadata
"""
from lia_models.event_store import *  # noqa: F401,F403

# Column aliases for compatibility
aggregate_type = "aggregate_type"  # DomainEvent.aggregate_type column
aggregate_id = "aggregate_id"      # DomainEvent.aggregate_id column

event_type = "event_type"  # DomainEvent.event_type column
event_data = "event_data"          # DomainEvent.event_data column
company_id = "company_id"         # DomainEvent.company_id column
created_by = "created_by"         # DomainEvent.created_by column
created_at = "created_at"         # DomainEvent.created_at column
sequence_number = "sequence_number"  # DomainEvent.sequence_number column
id = "id"                         # DomainEvent.id column
