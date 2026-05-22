"""InterviewNoteRepository — DB access for InterviewNote records.

Extracted from app/domains/cv_screening/services/interview_notes_service.py per ADR-001.
All queries scoped by company_id (multi-tenancy invariant).
"""
from __future__ import annotations

import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.interview import InterviewNote


class InterviewNoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        *,
        note_id: str,
        company_id: str,
    ) -> InterviewNote | None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(InterviewNote).where(
                and_(
                    InterviewNote.id == uuid.UUID(note_id),
                    InterviewNote.company_id == uuid.UUID(company_id),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_for_candidate(
        self,
        *,
        candidate_id: str,
        company_id: str,
        job_id: str | None = None,
    ) -> list[InterviewNote]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        conditions = [
            InterviewNote.candidate_id == uuid.UUID(candidate_id),
            InterviewNote.company_id == uuid.UUID(company_id),
        ]
        if job_id:
            conditions.append(InterviewNote.job_id == uuid.UUID(job_id))
        # TENANT-EXEMPT: dynamic builder — conditions list is seeded with
        # InterviewNote.company_id == uuid.UUID(company_id) (above). Sensor cannot
        # trace company_id through and_(*conditions) spread.
        result = await self.db.execute(
            select(InterviewNote)
            .where(and_(*conditions))
            .order_by(InterviewNote.created_at.desc())
        )
        return list(result.scalars().all())

    async def add(self, note: InterviewNote) -> InterviewNote:
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def update(
        self,
        note: InterviewNote,
        **fields,
    ) -> InterviewNote:
        for key, value in fields.items():
            if hasattr(note, key) and value is not None:
                setattr(note, key, value)
        await self.db.commit()
        await self.db.refresh(note)
        return note
