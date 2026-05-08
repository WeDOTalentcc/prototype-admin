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


    # ── Sprint Q2 ADR-001 cleanup: extracted from memory_service.py ──────

    async def search_similar_messages(
        self,
        *,
        company_id: UUID | str,
        query_embedding: list[float],
        session_id: str | None = None,
        user_id: str | None = None,
        limit: int = 5,
        min_similarity: float = 0.7,
    ) -> list[tuple[ConversationMemory, float]]:
        """Vector-similarity search over ConversationMemory using pgvector.

        Returns list of (memory, similarity_score) tuples filtered by
        min_similarity, capped at `limit`.
        """
        self._require_company_id(company_id)

        from sqlalchemy import text

        filters = [ConversationMemory.company_id == company_id]
        if session_id:
            filters.append(ConversationMemory.session_id == session_id)
        if user_id:
            filters.append(ConversationMemory.user_id == user_id)

        similarity_expr = text(
            "1 - (embedding <=> :query_embedding::vector)"
        )

        stmt = (
            select(
                ConversationMemory,
                similarity_expr.bindparams(
                    query_embedding=str(query_embedding)
                ).label("similarity"),
            )
            .where(and_(*filters))
            .where(ConversationMemory.embedding.isnot(None))
            .order_by(text("similarity DESC"))
            .limit(limit * 2)
        )

        result = await self._db.execute(stmt)
        rows = result.all()

        out: list[tuple[ConversationMemory, float]] = []
        for memory, similarity in rows:
            if similarity >= min_similarity:
                out.append((memory, float(similarity)))
            if len(out) >= limit:
                break
        return out

    async def search_knowledge_base(
        self,
        *,
        company_id: UUID | str,
        query_embedding: list[float],
        document_types: list[str] | None = None,
        limit: int = 5,
        min_similarity: float = 0.7,
    ) -> list[tuple[object, float]]:
        """Vector-similarity search over KnowledgeBase using pgvector."""
        self._require_company_id(company_id)

        from sqlalchemy import text

        from lia_models.memory import KnowledgeBase

        filters = [KnowledgeBase.company_id == company_id]
        if document_types:
            filters.append(KnowledgeBase.document_type.in_(document_types))

        similarity_expr = text(
            "1 - (embedding <=> :query_embedding::vector)"
        )

        stmt = (
            select(
                KnowledgeBase,
                similarity_expr.bindparams(
                    query_embedding=str(query_embedding)
                ).label("similarity"),
            )
            .where(and_(*filters))
            .where(KnowledgeBase.embedding.isnot(None))
            .order_by(text("similarity DESC"))
            .limit(limit * 2)
        )

        result = await self._db.execute(stmt)
        rows = result.all()

        out: list[tuple[object, float]] = []
        for kb_entry, similarity in rows:
            if similarity >= min_similarity:
                out.append((kb_entry, float(similarity)))
            if len(out) >= limit:
                break
        return out
