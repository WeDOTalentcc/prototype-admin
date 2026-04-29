"""
EntityResolverService — resolves entity hints (names, IDs) to concrete DB records.

Computational guide: reduces P(LIA asking > 2 context questions) by resolving
entities from the DB directly. No LLM inference required.

PR-J harness-engineering.
Multi-tenant: ALL queries enforce company_id (CLAUDE.md Non-Negotiable #1).
Max 2 disambiguation questions before suggesting navigation to UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy


@dataclass
class EntityResolutionResult:
    resolved: bool
    entity_type: str
    entity_id: str | None = None
    preview: dict[str, Any] | None = None
    navigate_to: str | None = None
    ambiguous: bool = False
    candidates_preview: list[dict[str, Any]] = field(default_factory=list)


class EntityResolverService:
    """Resolves text hints to entity IDs. Pure SQL, multi-tenant, no LLM."""

    @staticmethod
    async def resolve(
        entity_type: str,
        hint: str,
        company_id: str,
        db: AsyncSession,
    ) -> EntityResolutionResult:
        """
        Resolve `hint` to entity of `entity_type` within `company_id`.
        Returns resolved entity or fallback navigation suggestion.
        """
        if entity_type == "candidate":
            return await EntityResolverService._resolve_candidate(hint, company_id, db)
        if entity_type == "job":
            return await EntityResolverService._resolve_job(hint, company_id, db)
        if entity_type == "interview":
            # Interview context resolves via candidate
            return await EntityResolverService._resolve_candidate(hint, company_id, db)
        return EntityResolutionResult(
            resolved=False,
            entity_type=entity_type,
            navigate_to="/visao-do-funil",
        )

    @staticmethod
    async def _resolve_candidate(
        hint: str,
        company_id: str,
        db: AsyncSession,
    ) -> EntityResolutionResult:
        hint_clean = hint.strip()
        hint_lower = hint_clean.lower()

        # Direct UUID / prefixed ID match
        if len(hint_clean) >= 32:
            stmt = select(Candidate).where(
                Candidate.id == hint_clean,
                Candidate.company_id == company_id,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row:
                return EntityResolutionResult(
                    resolved=True,
                    entity_type="candidate",
                    entity_id=str(row.id),
                    preview={
                        "name": row.name,
                        "email": getattr(row, "email", None),
                        "stage": getattr(row, "current_stage", None),
                    },
                )

        # Name / email fuzzy match (ILIKE)
        stmt = (
            select(Candidate)
            .where(
                Candidate.company_id == company_id,
                or_(
                    func.lower(Candidate.name).contains(hint_lower),
                    func.lower(getattr(Candidate, "email", Candidate.name)).contains(
                        hint_lower
                    ),
                ),
            )
            .limit(5)
        )
        rows = (await db.execute(stmt)).scalars().all()

        if not rows:
            return EntityResolutionResult(
                resolved=False,
                entity_type="candidate",
                navigate_to="/funil-de-talentos",
            )

        if len(rows) == 1:
            c = rows[0]
            return EntityResolutionResult(
                resolved=True,
                entity_type="candidate",
                entity_id=str(c.id),
                preview={
                    "name": c.name,
                    "email": getattr(c, "email", None),
                    "stage": getattr(c, "current_stage", None),
                },
            )

        # Ambiguous — return up to 3 previews for one disambiguation question
        return EntityResolutionResult(
            resolved=False,
            entity_type="candidate",
            ambiguous=True,
            candidates_preview=[
                {
                    "id": str(c.id),
                    "name": c.name,
                    "stage": getattr(c, "current_stage", None),
                }
                for c in rows[:3]
            ],
        )

    @staticmethod
    async def _resolve_job(
        hint: str,
        company_id: str,
        db: AsyncSession,
    ) -> EntityResolutionResult:
        hint_lower = hint.strip().lower()
        stmt = (
            select(JobVacancy)
            .where(
                JobVacancy.company_id == company_id,
                func.lower(JobVacancy.title).contains(hint_lower),
            )
            .limit(3)
        )
        rows = (await db.execute(stmt)).scalars().all()

        if not rows:
            return EntityResolutionResult(
                resolved=False,
                entity_type="job",
                navigate_to="/jobs",
            )

        if len(rows) == 1:
            j = rows[0]
            return EntityResolutionResult(
                resolved=True,
                entity_type="job",
                entity_id=str(j.id),
                preview={"title": j.title, "status": getattr(j, "status", None)},
            )

        return EntityResolutionResult(
            resolved=False,
            entity_type="job",
            ambiguous=True,
            candidates_preview=[
                {"id": str(j.id), "title": j.title}
                for j in rows
            ],
        )
