"""Conversation memory repository (ADR-001 canonical example for Sprint 5.4).

Extracts the single `select(ConversationMemory)` query from
`recruiter_assistant/services/memory_service.py:get_recent_messages`
into a canonical repository per ADR-001.

Smallest service migration in Sprint 5.4 (1 SQL hit) — sets the pattern
for Boy Scout follow-up of the other 4 services in this domain.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.memory import ConversationMemory

logger = logging.getLogger(__name__)


class ConversationMemoryRepository:
    """Persistence for ConversationMemory rows.

    Multi-tenancy invariant (CLAUDE.md REGRA 1): every public method
    enforces `_require_company_id` fail-closed.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _require_company_id(company_id: UUID | str) -> None:
        """Multi-tenancy fail-closed gate."""
        if not company_id:
            raise ValueError(
                "Multi-tenancy invariant violation: company_id required for "
                "ConversationMemoryRepository operations (ADR-001 + REGRA 1)"
            )

    async def get_recent_for_session(
        self,
        *,
        company_id: UUID | str,
        session_id: str,
        limit: int = 50,
    ) -> list[ConversationMemory]:
        """Return the most recent N messages for a (company, session).

        Returns chronologically: oldest first (caller-friendly for chat
        rendering). Storage order in DB is descending by created_at;
        we reverse before returning.
        """
        self._require_company_id(company_id)

        stmt = (
            select(ConversationMemory)
            .where(
                and_(
                    ConversationMemory.company_id == company_id,
                    ConversationMemory.session_id == session_id,
                )
            )
            .order_by(ConversationMemory.created_at.desc())
            .limit(limit)
        )

        result = await self._db.execute(stmt)
        rows = result.scalars().all()
        return list(reversed(rows))
