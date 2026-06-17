"""
Interview Notes Service — persistent CRUD for InterviewNote records.

Replaces the in-memory `interview_notes_db` dict previously used in
app/api/v1/interview_notes.py. All operations are scoped by company_id
for multi-tenant isolation.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.repositories.interview_note_repository import (
    InterviewNoteRepository,
)
from lia_models.interview import InterviewNote

logger = logging.getLogger(__name__)


async def create_interview_note(
    db: AsyncSession,
    company_id: str,
    created_by: str,
    candidate_id: str,
    candidate_name: str | None,
    job_id: str | None,
    job_title: str | None,
    scheduled_interview_id: str | None,
    interviewer_id: str | None,
    recruiter_name: str | None,
    interview_date: datetime | None,
    interview_type: str,
    questions: list,
    blocks: list,
    general_notes: str | None,
    transcription: str | None,
    transcription_source: str | None,
    lia_parecer: str | None,
    lia_parecer_editado: bool,
    wsi_score: dict | None,
    recommendation: str | None,
    next_stage: str | None,
    feedback_sent: bool,
    feedback_scheduled_for: datetime | None,
    status: str,
) -> InterviewNote:
    note = InterviewNote(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        candidate_id=uuid.UUID(candidate_id),
        candidate_name=candidate_name,
        job_id=uuid.UUID(job_id) if job_id else None,
        job_title=job_title,
        scheduled_interview_id=scheduled_interview_id,
        interviewer_id=interviewer_id,
        recruiter_name=recruiter_name,
        interview_date=interview_date,
        interview_type=interview_type,
        questions=questions,
        blocks=blocks,
        general_notes=general_notes,
        transcription=transcription,
        transcription_source=transcription_source,
        lia_parecer=lia_parecer,
        lia_parecer_editado=lia_parecer_editado,
        wsi_score=wsi_score,
        recommendation=recommendation,
        next_stage=next_stage,
        feedback_sent=feedback_sent,
        feedback_scheduled_for=feedback_scheduled_for,
        status=status,
        created_by=created_by,
    )
    repo = InterviewNoteRepository(db)
    note = await repo.add(note)
    logger.info("InterviewNote created", extra={"note_id": str(note.id), "company_id": company_id})
    return note


async def get_interview_note(
    db: AsyncSession,
    note_id: str,
    company_id: str,
) -> InterviewNote | None:
    repo = InterviewNoteRepository(db)
    return await repo.get_by_id(note_id=note_id, company_id=company_id)


async def get_notes_for_candidate(
    db: AsyncSession,
    candidate_id: str,
    company_id: str,
    job_id: str | None = None,
) -> list[InterviewNote]:
    repo = InterviewNoteRepository(db)
    return await repo.list_for_candidate(
        candidate_id=candidate_id,
        company_id=company_id,
        job_id=job_id,
    )


async def update_interview_note(
    db: AsyncSession,
    note_id: str,
    company_id: str,
    **fields,
) -> InterviewNote | None:
    repo = InterviewNoteRepository(db)
    note = await repo.get_by_id(note_id=note_id, company_id=company_id)
    if not note:
        return None
    note.updated_at = datetime.utcnow()
    note = await repo.update(note, **fields)
    logger.info("InterviewNote updated", extra={"note_id": note_id, "fields": list(fields.keys())})
    return note
