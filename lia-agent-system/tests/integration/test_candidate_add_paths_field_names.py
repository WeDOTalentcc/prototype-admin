"""Task #1309 regression: two candidate-add paths constructed VacancyCandidate
with kwargs that are NOT columns on the model (``job_vacancy_id``, ``sub_status``,
``is_active``). SQLAlchemy's declarative ``__init__`` raises ``TypeError`` for
unknown kwargs, so "add approved candidates from a shared search to a job" and
the candidate-lists "add to job" helper were effectively broken at runtime.

These tests exercise each path and confirm a VacancyCandidate row is actually
created with the real columns (``vacancy_id`` + ``status``). They also cover the
lookup queries that run within the same paths, which referenced the non-existent
``VacancyCandidate.job_vacancy_id`` attribute (an ``AttributeError`` at query
build time).
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from lia_models.candidate import VacancyCandidate


# ── Path 2: candidate-lists "add to job" repository helper ───────────────────


@pytest.mark.asyncio
async def test_candidate_list_repo_creates_vacancy_candidate():
    from app.domains.candidate_lists.repositories.candidate_list_repository import (
        CandidateListRepository,
    )

    db = AsyncMock()
    db.add = lambda obj: None  # add() is sync on a real session
    repo = CandidateListRepository(db)

    company_id = str(uuid.uuid4())
    job_uuid = uuid.uuid4()
    candidate_uuid = uuid.uuid4()

    with patch(
        "app.shared.services.stage_id_resolver.resolve_recruitment_stage_id",
        new=AsyncMock(return_value=None),
    ):
        vc = await repo.create_vacancy_candidate(
            company_id=company_id,
            job_vacancy_id=job_uuid,
            candidate_id=candidate_uuid,
        )

    assert isinstance(vc, VacancyCandidate)
    assert vc.vacancy_id == job_uuid
    assert vc.candidate_id == candidate_uuid
    assert vc.company_id == company_id
    assert vc.status == "sourced"
    assert vc.stage == "sourcing"


@pytest.mark.asyncio
async def test_candidate_list_repo_find_uses_vacancy_id_column():
    """find_vacancy_candidate must reference VacancyCandidate.vacancy_id, not the
    non-existent job_vacancy_id (which raised AttributeError at query build)."""
    from app.domains.candidate_lists.repositories.candidate_list_repository import (
        CandidateListRepository,
    )

    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    repo = CandidateListRepository(db)

    result = await repo.find_vacancy_candidate(uuid.uuid4(), uuid.uuid4())

    assert result is None
    db.execute.assert_awaited_once()


# ── Path 1: shared-search "add approved to job" endpoint ─────────────────────


@pytest.mark.asyncio
async def test_shared_search_add_to_job_creates_vacancy_candidate():
    from app.api.v1.shared_searches import AddToJobRequest, add_approved_to_job

    company_id = str(uuid.uuid4())
    candidate_uuid = uuid.uuid4()
    search_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    user = SimpleNamespace(company_id=company_id)

    created: list[VacancyCandidate] = []

    repo = AsyncMock()
    repo.db = AsyncMock()
    repo.get_by_id_and_company.return_value = SimpleNamespace(id=uuid.uuid4())
    repo.get_approved_feedbacks.return_value = [
        SimpleNamespace(candidate_id=candidate_uuid, comment=None)
    ]
    repo.get_vacancy_candidate.return_value = None
    repo.create_vacancy_candidate.side_effect = lambda vc: created.append(vc)

    data = AddToJobRequest(job_id=job_id, all_approved=True)

    with patch(
        "app.shared.services.stage_id_resolver.resolve_recruitment_stage_id",
        new=AsyncMock(return_value=None),
    ):
        response = await add_approved_to_job(
            search_id=search_id,
            data=data,
            repo=repo,
            current_user=user,
            company_id=company_id,
        )

    assert response["success"] is True
    assert response["added"] == 1
    assert len(created) == 1
    vc = created[0]
    assert isinstance(vc, VacancyCandidate)
    assert vc.vacancy_id == uuid.UUID(job_id)
    assert vc.candidate_id == candidate_uuid
    assert vc.status == "sourced"
    assert vc.stage == "sourcing"


@pytest.mark.asyncio
async def test_shared_search_repo_get_uses_vacancy_id_column():
    """get_vacancy_candidate must reference VacancyCandidate.vacancy_id, not the
    non-existent job_vacancy_id (which raised AttributeError at query build)."""
    from app.domains.shared_searches.repositories.shared_search_repository import (
        SharedSearchRepository,
    )

    db = AsyncMock()
    db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
    repo = SharedSearchRepository(db)

    result = await repo.get_vacancy_candidate(uuid.uuid4(), uuid.uuid4())

    assert result is None
    db.execute.assert_awaited_once()
