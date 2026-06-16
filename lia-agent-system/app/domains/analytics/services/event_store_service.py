"""
EventStoreService — append-only event store for SOX audit replay.

Rules:
  - ONLY append() — never update or delete events
  - get_history() — replay events for an aggregate in order
  - reconstruct_state() — apply event fold to reconstruct entity state
  - All operations fail-open
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

try:
    from lia_models.event_store import DomainEvent as _DomainEvent  # type: ignore[union-attr]
except Exception:
    _DomainEvent = None  # type: ignore[union-attr]


class EventStoreService:
    """Append-only event store. No UPDATE or DELETE."""

    async def append(
        self,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        data: dict[str, Any],
        company_id: str,
        db: AsyncSession,
        created_by: str | None = None,
    ) -> bool:
        """Append event to store. Fail-open: returns False on error."""
        try:
            DomainEvent = _DomainEvent or __import__("app.models.event_store", fromlist=["DomainEvent"]).DomainEvent
            # Get next sequence number
            result = await db.execute(
                select(func.coalesce(func.max(DomainEvent.sequence_number), 0)).where(
                    DomainEvent.aggregate_type == aggregate_type,
                    DomainEvent.aggregate_id == aggregate_id,
                )
            )
            next_seq = (result.scalar() or 0) + 1

            event = DomainEvent(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                event_data=data,
                company_id=company_id,
                created_by=created_by,
                created_at=datetime.utcnow(),
                sequence_number=next_seq,
            )
            db.add(event)
            await db.commit()
            logger.info(
                "[EventStore] appended %s/%s event_type=%s seq=%d",
                aggregate_type, aggregate_id, event_type, next_seq,
            )
            return True
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.warning("[EventStore] append failed (fail-open): %s", exc)
            return False

    async def get_history(
        self,
        aggregate_type: str,
        aggregate_id: str,
        db: AsyncSession,
        from_sequence: int = 0,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Get ordered event history for an aggregate. Fail-open: returns []."""
        try:
            DomainEvent = _DomainEvent or __import__("app.models.event_store", fromlist=["DomainEvent"]).DomainEvent
            # ADR-001-EXEMPT: DomainEvent is a system-level event log without a dedicated repo; promote in Sprint 6 cleanup
            result = await db.execute(
                select(DomainEvent).where(
                    DomainEvent.aggregate_type == aggregate_type,
                    DomainEvent.aggregate_id == aggregate_id,
                    DomainEvent.sequence_number > from_sequence,
                ).order_by(DomainEvent.sequence_number).limit(limit)
            )
            events = result.scalars().all()
            return [
                {
                    "id": str(ev.id),
                    "aggregate_type": ev.aggregate_type,
                    "aggregate_id": ev.aggregate_id,
                    "event_type": ev.event_type,
                    "event_data": ev.event_data,
                    "company_id": ev.company_id,
                    "created_by": ev.created_by,
                    "created_at": ev.created_at.isoformat() if ev.created_at else None,
                    "sequence_number": ev.sequence_number,
                }
                for ev in events
            ]
        except Exception as exc:
            logger.warning("[EventStore] get_history failed (fail-open): %s", exc)
            return []

    async def reconstruct_state(
        self,
        aggregate_type: str,
        aggregate_id: str,
        db: AsyncSession,
        folder: Callable[[dict, dict], dict] | None = None,
    ) -> dict[str, Any]:
        """Reconstruct aggregate state by folding events. Fail-open: returns {}."""
        try:
            events = await self.get_history(aggregate_type, aggregate_id, db)
            if not events:
                return {}

            if folder is None:
                # Default folder: merge event_data into state
                def default_folder(state: dict, event: dict) -> dict:
                    updated = {**state}
                    updated.update(event.get("event_data", {}))
                    updated["_last_event_type"] = event["event_type"]
                    updated["_sequence"] = event["sequence_number"]
                    return updated
                folder = default_folder

            state: dict[str, Any] = {}
            for event in events:
                state = folder(state, event)
            return state
        except Exception as exc:
            logger.warning("[EventStore] reconstruct_state failed: %s", exc)
            return {}


event_store_service = EventStoreService()
