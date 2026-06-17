"""Phase C.2 pin — POST /job-vacancies/{id}/unpublish behavior + idempotency.

Tests the repository method `unpublish_vacancy` directly (in-memory fake
vacancy) — keeps the test hermetic without spinning up Postgres / FastAPI.
The endpoint surface is exercised at the route layer in a separate
integration test if desired; this test pins the BUSINESS RULE:

  1. Clears published_linkedin/indeed/website + last_published_at.
  2. Idempotent — second call returns changed=False.
  3. Status field is NOT touched (recruiter chooses Pausar/Concluir
     separately via JobStatusModal).
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.job_management.repositories.job_vacancy_lifecycle_repository import (
    JobVacancyLifecycleRepository,
)


def _make_repo() -> JobVacancyLifecycleRepository:
    """Construct a repo with a fake async session — flush/refresh are awaitable
    no-ops; the methods under test do not touch the DB beyond those calls."""
    fake_db = SimpleNamespace(
        flush=AsyncMock(),
        refresh=AsyncMock(),
    )
    return JobVacancyLifecycleRepository(fake_db)


def _make_vacancy(*, published: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        id="vac-1",
        status="Ativa",
        published_linkedin=published,
        published_indeed=published,
        published_website=published,
        last_published_at=datetime(2026, 5, 1, 12, 0, 0) if published else None,
        updated_at=datetime(2026, 5, 1, 12, 0, 0),
    )


@pytest.mark.asyncio
async def test_unpublish_clears_all_publication_flags():
    repo = _make_repo()
    vac = _make_vacancy(published=True)

    job, changed = await repo.unpublish_vacancy(vac)

    assert changed is True
    assert job.published_linkedin is False
    assert job.published_indeed is False
    assert job.published_website is False
    assert job.last_published_at is None


@pytest.mark.asyncio
async def test_unpublish_does_not_change_status():
    """Status field is untouched — recruiter picks Pausar/Concluir separately."""
    repo = _make_repo()
    vac = _make_vacancy(published=True)

    job, _ = await repo.unpublish_vacancy(vac)

    assert job.status == "Ativa", (
        "unpublish_vacancy must NOT mutate status. "
        "Caller chooses Pausar/Concluir via JobStatusModal."
    )


@pytest.mark.asyncio
async def test_unpublish_is_idempotent_when_already_unpublished():
    repo = _make_repo()
    vac = _make_vacancy(published=False)  # already unpublished

    job, changed = await repo.unpublish_vacancy(vac)

    assert changed is False, (
        "Second / repeat call must return changed=False so the route can "
        "respond {changed: false} without emitting an audit event."
    )
    assert job.published_linkedin is False
    assert job.last_published_at is None


@pytest.mark.asyncio
async def test_unpublish_skips_db_flush_when_unchanged():
    """Optimization sensor: idempotent calls should not hit flush+refresh."""
    repo = _make_repo()
    vac = _make_vacancy(published=False)

    await repo.unpublish_vacancy(vac)

    repo.db.flush.assert_not_called()
    repo.db.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_unpublish_calls_db_flush_when_changed():
    repo = _make_repo()
    vac = _make_vacancy(published=True)

    await repo.unpublish_vacancy(vac)

    repo.db.flush.assert_called_once()
    repo.db.refresh.assert_called_once()
