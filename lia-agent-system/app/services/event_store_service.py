"""Backwards-compatibility shim — canonical implementation in domain layer."""
from app.shared.services.event_store_service import *  # noqa: F401, F403
from app.domains.analytics.services.event_store_service import _DomainEvent  # noqa: F401
