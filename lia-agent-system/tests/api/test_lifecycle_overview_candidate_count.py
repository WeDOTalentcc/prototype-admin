"""
Task #439 — Lock in real-time `candidate_count` behavior of
``GET /api/v1/job-vacancies/lifecycle-overview``.

Background
----------
Before Task #434, the lifecycle-overview endpoint reported
``candidate_count`` straight from the cached
``JobVacancy.funnel_data["total"]`` column. That value is only refreshed
opportunistically and quickly drifts out of sync with the real number of
``vacancy_candidates`` rows for the job, which is exactly what the "Vagas"
panel of the Visão do Pipeline page is trying to show.

Task #434 changed the endpoint to compute ``candidate_count`` from a live
aggregate over the ``VacancyCandidate`` table, scoped to the current
company. There was no test pinning that behavior, so a future refactor
could silently regress to reading the stale cache. This module is that
test.

What the tests assert
---------------------
1. ``candidate_count`` reflects the **live** number of VacancyCandidate
   rows seeded for the vacancy (N candidates seeded → ``candidate_count == N``).

2. When ``funnel_data["total"]`` is deliberately set to a number that
   disagrees with the real candidate count, the endpoint returns the
   **real** count — proving the cached field is no longer trusted.

3. Tenant isolation: candidates that belong to another company's
   vacancy are not counted toward this company's vacancy.

Implementation strategy
-----------------------
The lifecycle-overview handler is an ``async def`` function. The tests
invoke it directly with an in-memory fake repository and a synthetic
``User`` object instead of going through the full HTTP / auth / DB
stack. The fake repository enforces the same company-scoped filter the
real SQLAlchemy join enforces (``JobVacancy.company_id == company_id``),
so the tenant-isolation assertion exercises the same contract the
production query relies on. Calling the handler directly keeps the test
hermetic — no Postgres, no Redis, no auth middleware — while still
covering the production code path that builds the JSON response.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from app.api.v1.job_vacancies.analytics import (
    JobLifecycleOverviewResponse,
    get_job_lifecycle_overview,
)


COMPANY_A = "company-a"
COMPANY_B = "company-b"


def _make_job(
    *,
    company_id: str,
    title: str,
    funnel_total: int | None = None,
) -> SimpleNamespace:
    """Build a JobVacancy-shaped object with every attribute the
    lifecycle-overview endpoint reads.

    Using ``SimpleNamespace`` keeps the test independent of the
    SQLAlchemy session — the endpoint only ever reads attributes off
    the object, never persists it.
    """
    funnel_data: dict[str, Any] = {}
    if funnel_total is not None:
        funnel_data = {"total": funnel_total}

    return SimpleNamespace(
        id=uuid4(),
        company_id=company_id,
        title=title,
        department="Tech",
        location="Remoto",
        work_model="remoto",
        seniority_level="Pleno",
        # Status "Rascunho" + no enriched JD / no screening config / no
        # ATS marker → classified as the "rascunho" lifecycle stage.
        status="Rascunho",
        stage="Planejamento",
        manager="Manager",
        approval_status=None,
        approval_requested_at=None,
        published_linkedin=False,
        published_website=False,
        published_indeed=False,
        linkedin_post_id=None,
        indeed_job_id=None,
        last_published_at=None,
        screening_questions=[],
        screening_config=None,
        enriched_jd=None,
        source_system=None,
        additional_data=None,
        funnel_data=funnel_data,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        updated_at=datetime(2025, 1, 2, 12, 0, 0),
    )


@dataclass
class _FakeAnalyticsRepo:
    """In-memory stand-in for ``JobVacanciesAnalyticsRepository`` that
    enforces the same per-company filtering contract as the real one.

    ``jobs`` is the global list across all tenants; ``raw_candidate_counts``
    maps a vacancy id (string) to the number of candidates that exist
    for that vacancy. ``get_candidate_counts_by_vacancy_for_company``
    returns only the entries whose owning vacancy belongs to the caller's
    company — exactly like the SQL
    ``JOIN job_vacancies ON ... WHERE company_id = :company_id`` in the
    real repository.
    """
    jobs: list[SimpleNamespace] = field(default_factory=list)
    raw_candidate_counts: dict[str, int] = field(default_factory=dict)

    async def get_all_company_jobs(self, company_id: str) -> list[SimpleNamespace]:
        return [j for j in self.jobs if j.company_id == company_id]

    async def get_candidate_counts_by_vacancy_for_company(
        self, company_id: str
    ) -> dict[str, int]:
        company_vacancy_ids = {
            str(j.id) for j in self.jobs if j.company_id == company_id
        }
        return {
            vid: count
            for vid, count in self.raw_candidate_counts.items()
            if vid in company_vacancy_ids
        }


def _user_for(company_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id="user-1",
        company_id=company_id,
        role="admin",
        is_active=True,
        email="user@test.com",
    )


async def _call_endpoint(
    repo: _FakeAnalyticsRepo, company_id: str
) -> JobLifecycleOverviewResponse:
    """Invoke the FastAPI handler directly, bypassing the HTTP stack."""
    return await get_job_lifecycle_overview(
        vacancies_per_stage=50,
        current_user=_user_for(company_id),
        repo=repo,
    )


def _find_vacancy(
    response: JobLifecycleOverviewResponse, vacancy_id: str
) -> Any | None:
    for stage in response.stages:
        for vac in stage.vacancies:
            if vac.id == vacancy_id:
                return vac
    return None


@pytest.mark.asyncio
async def test_candidate_count_reflects_live_vacancy_candidate_rows():
    """N candidates seeded for the vacancy → ``candidate_count == N``.

    This is the baseline guarantee the Vagas panel needs: the number it
    displays is the number of ``vacancy_candidates`` rows that exist
    right now, not a snapshot taken at some point in the past.
    """
    repo = _FakeAnalyticsRepo()
    job = _make_job(company_id=COMPANY_A, title="Backend Engineer")
    repo.jobs.append(job)
    # Five candidates currently exist for this vacancy.
    repo.raw_candidate_counts[str(job.id)] = 5

    response = await _call_endpoint(repo, COMPANY_A)

    found = _find_vacancy(response, str(job.id))
    assert found is not None, (
        "Seeded vacancy was not returned by lifecycle-overview at all; "
        "cannot validate candidate_count."
    )
    assert found.candidate_count == 5, (
        "lifecycle-overview should report the live number of candidates "
        f"(5), but returned {found.candidate_count}."
    )


@pytest.mark.asyncio
async def test_candidate_count_ignores_stale_funnel_data_total():
    """When ``funnel_data['total']`` disagrees with the real candidate
    count, the endpoint must return the real count.

    This is the explicit behavior change introduced by Task #434 and the
    one a regression is most likely to undo (e.g. by "optimizing" the
    aggregate query away in favor of the cheap cached column).
    """
    repo = _FakeAnalyticsRepo()
    # Cached value claims 99 candidates; reality is 4. The endpoint
    # must report 4 — proving the cache is not consulted.
    job = _make_job(
        company_id=COMPANY_A,
        title="Stale Cache Vacancy",
        funnel_total=99,
    )
    repo.jobs.append(job)
    repo.raw_candidate_counts[str(job.id)] = 4

    response = await _call_endpoint(repo, COMPANY_A)

    found = _find_vacancy(response, str(job.id))
    assert found is not None
    assert found.candidate_count == 4, (
        "lifecycle-overview returned candidate_count="
        f"{found.candidate_count}, which matches neither the live "
        "count (4) nor the stale cache (99). If it equals 99 this is a "
        "regression to the pre-Task #434 behavior of reading "
        "JobVacancy.funnel_data['total'] instead of aggregating "
        "VacancyCandidate rows."
    )


@pytest.mark.asyncio
async def test_candidate_count_does_not_leak_across_tenants():
    """Candidates attached to another company's vacancy must not be
    counted toward this company's vacancy.

    The fake repo enforces the same JOIN-on-company_id filter the real
    SQL query enforces, so this guards the contract that
    ``get_candidate_counts_by_vacancy_for_company`` is invoked with —
    and respects — the requesting user's company id.
    """
    repo = _FakeAnalyticsRepo()
    # Company A: one vacancy with 2 real candidates.
    job_a = _make_job(company_id=COMPANY_A, title="Vaga A")
    repo.jobs.append(job_a)
    repo.raw_candidate_counts[str(job_a.id)] = 2

    # Company B: one vacancy with 50 real candidates. These must NOT
    # show up when querying as Company A, even though they live in the
    # same database.
    job_b = _make_job(company_id=COMPANY_B, title="Vaga B")
    repo.jobs.append(job_b)
    repo.raw_candidate_counts[str(job_b.id)] = 50

    # ── Query as Company A ───────────────────────────────────────────
    response_a = await _call_endpoint(repo, COMPANY_A)
    a_vacancy_ids = {v.id for stage in response_a.stages for v in stage.vacancies}
    assert str(job_a.id) in a_vacancy_ids
    assert str(job_b.id) not in a_vacancy_ids, (
        "Company B's vacancy leaked into Company A's lifecycle-overview "
        "response — tenant isolation on the vacancy listing is broken."
    )

    found_a = _find_vacancy(response_a, str(job_a.id))
    assert found_a is not None
    assert found_a.candidate_count == 2, (
        "Company A's vacancy should report 2 candidates, but reported "
        f"{found_a.candidate_count}. If it is 52, candidates from "
        "Company B's vacancy are being counted, which means the "
        "candidate-count aggregate is no longer scoped by company_id."
    )
    assert response_a.total_vacancies == 1

    # ── Query as Company B (sanity check the fake is symmetrical) ───
    response_b = await _call_endpoint(repo, COMPANY_B)
    found_b = _find_vacancy(response_b, str(job_b.id))
    assert found_b is not None
    assert found_b.candidate_count == 50
    b_vacancy_ids = {v.id for stage in response_b.stages for v in stage.vacancies}
    assert str(job_a.id) not in b_vacancy_ids
