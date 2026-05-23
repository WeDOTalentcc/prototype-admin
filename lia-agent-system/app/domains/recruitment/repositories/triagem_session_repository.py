"""
TriagemSessionRepository — persistence layer for TriagemSession + TriagemMessage.

Owns all ORM read/write operations for the recruitment triagem flow
(canonical chat-based screening session and its messages).

Per ADR-001: services in app/domains/recruitment/services/triagem_session_service/
delegate every `select(TriagemSession)` / `select(TriagemMessage)` here.

Cross-domain reads (JobVacancy, Candidate) remain in their owning repos:
- app/domains/job_management/repositories/job_vacancy_crud_repository.py
- app/domains/candidates/repositories/candidate_repository.py
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.triagem import TriagemMessage, TriagemSession

logger = logging.getLogger(__name__)


class TriagemSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # TriagemSession lookups
    # ------------------------------------------------------------------
    async def get_session_by_token(self, token: str) -> TriagemSession | None:
        """Resolve triagem session by unique token (PUBLIC candidate access).

        Sprint 4 B.2 — fix P0 regressão Sprint 4 B.1 (ca62339cb):

        Endpoints /api/v1/triagem/{token}/* sao PUBLIC (candidato sem JWT).
        request.state.company_id e None, set_tenant_context nao roda,
        triagem_sessions tem FORCE RLS com policy filtrando por
        current_setting(app.company_id) (NULL) -> 0 rows -> 404.

        Fix canonical: usa funcao Postgres SECURITY DEFINER
        resolve_triagem_session_by_token (owned by postgres, bypassa RLS via
        ownership) para o lookup pelo token UNIQUE non-guessable. Depois de
        resolver, set RLS context com session.company_id para queries
        subsequentes na mesma request (messages, updates, etc) operarem
        normalmente sob RLS.

        Token e UUID v4 (~10^36 espaco), nao-guessable. Funcao e read-only
        e ESCOPADA a token-equality (sem LIKE/subquery). GRANT EXECUTE
        somente para lia_app. Definida em alembic/versions/187_triagem_resolve_tenant_secdef.py.

        Refs: AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md.
        """
        # SECURITY DEFINER function bypasses RLS to find the session row by token.
        result = await self.db.execute(
            text(
                "SELECT * FROM resolve_triagem_session_by_token(:token)"
            ).columns(*TriagemSession.__table__.columns),
            {"token": token},
        )
        row = result.mappings().first()
        if row is None:
            return None

        # Hydrate the ORM model from the function's row mapping.
        session = TriagemSession(**dict(row))

        # Set RLS context for the rest of the request so subsequent queries
        # (messages, session updates, etc.) honor multi-tenancy normally.
        # Uses transaction-scoped set_config (third arg true = is_local).
        try:
            await self.db.execute(
                text("SELECT set_config('app.company_id', :cid, true)"),
                {"cid": str(session.company_id)},
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "[Triagem] Failed to set tenant RLS context after token resolution: %s",
                exc,
            )

        return session

    # ------------------------------------------------------------------
    # TriagemMessage lookups
    # ------------------------------------------------------------------
    async def list_messages_for_session(
        self, session_id: uuid.UUID
    ) -> list[TriagemMessage]:
        """All messages for a session ordered by created_at ASC."""
        result = await self.db.execute(
            select(TriagemMessage)
            .where(TriagemMessage.session_id == session_id)
            .order_by(TriagemMessage.created_at)
        )
        return list(result.scalars().all())

    async def list_candidate_messages_for_session(
        self, session_id: uuid.UUID
    ) -> list[TriagemMessage]:
        """All candidate-sender messages for a session ordered by created_at ASC."""
        result = await self.db.execute(
            select(TriagemMessage)
            .where(
                and_(
                    TriagemMessage.session_id == session_id,
                    TriagemMessage.sender == "candidate",
                )
            )
            .order_by(TriagemMessage.created_at)
        )
        return list(result.scalars().all())

    async def list_candidate_messages_in_block(
        self, session_id: uuid.UUID, wsi_block: int
    ) -> list[TriagemMessage]:
        result = await self.db.execute(
            select(TriagemMessage).where(
                and_(
                    TriagemMessage.session_id == session_id,
                    TriagemMessage.sender == "candidate",
                    TriagemMessage.wsi_block == wsi_block,
                )
            )
        )
        return list(result.scalars().all())

    async def list_lia_question_messages_for_session(
        self, session_id: uuid.UUID
    ) -> list[TriagemMessage]:
        """LIA-sender messages of type 'question', ordered by created_at ASC."""
        result = await self.db.execute(
            select(TriagemMessage)
            .where(
                and_(
                    TriagemMessage.session_id == session_id,
                    TriagemMessage.sender == "lia",
                    TriagemMessage.message_type == "question",
                )
            )
            .order_by(TriagemMessage.created_at)
        )
        return list(result.scalars().all())

    async def get_last_lia_question_message(
        self, session_id: uuid.UUID
    ) -> TriagemMessage | None:
        """Most recent LIA-sender 'question' message for a session."""
        result = await self.db.execute(
            select(TriagemMessage)
            .where(
                and_(
                    TriagemMessage.session_id == session_id,
                    TriagemMessage.sender == "lia",
                    TriagemMessage.message_type == "question",
                )
            )
            .order_by(TriagemMessage.created_at.desc())
        )
        return result.scalars().first()

    async def get_message_for_session(
        self, message_id: uuid.UUID, session_id: uuid.UUID
    ) -> TriagemMessage | None:
        """Fetch a single message scoped to its parent session."""
        result = await self.db.execute(
            select(TriagemMessage).where(
                and_(
                    TriagemMessage.id == message_id,
                    TriagemMessage.session_id == session_id,
                )
            )
        )
        return result.scalar_one_or_none()


# ----------------------------------------------------------------------
# Cross-domain helper — JobVacancy lookup with the dual-key fallback used
# by the triagem flow (try Rails-style string job_id first, fall back to
# the internal UUID `id`). Wraps existing JobVacancyCrudRepository methods
# so triagem services don't have to know the import path or do `select()`
# directly.
# ----------------------------------------------------------------------
async def find_job_vacancy_for_triagem(
    db: AsyncSession,
    job_id: str,
    company_id: str | None,
):
    """
    Resolve a JobVacancy by either Rails-style `job_id` (e.g. WDT-2025-001)
    or canonical UUID `id`. Honors company_id when provided.

    Returns the JobVacancy ORM row or None.

    Delegates entirely to JobVacancyCrudRepository — no direct ORM here.
    """
    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCrudRepository,
    )

    repo = JobVacancyCrudRepository(db)

    job = None
    try:
        if company_id:
            job = await repo.get_by_job_id_and_company(job_id, company_id)
        if not job:
            try:
                job_uuid = uuid.UUID(job_id)
            except (ValueError, TypeError):
                return job
            if company_id:
                job = await repo.get_vacancy_by_id_and_company(job_uuid, company_id)
            else:
                job = await repo.get_vacancy_by_id_only(job_uuid)
    except Exception as exc:
        logger.warning(
            f"[Triagem] find_job_vacancy_for_triagem failed (job_id={job_id}): {exc}"
        )
    return job
