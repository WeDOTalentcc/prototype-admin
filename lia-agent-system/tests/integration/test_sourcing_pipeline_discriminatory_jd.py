"""
Integration test — Full sourcing pipeline against a discriminatory JD.

Exercises ``SourcingPipelineService.run_pipeline_for_job`` end-to-end and
verifies the C6/C7 compliance gates wired into the pipeline service:

1. A job whose description contains explicit discriminatory criteria
   (gender / age) results in **zero** candidates being added to the pipeline,
   AND the rejection is **persisted to the ``audit_logs`` table** with
   ``decision="rejected"`` for the offending ``job_vacancy_id``.
2. PII (email, CPF, phone) inside the job vacancy is **never forwarded to
   the Pearch external service** — even on a clean (non-discriminatory) job
   that does reach the global-search call.

Persistence is exercised against a real **in-memory aiosqlite** database for
the ``audit_logs`` table (the only ORM model touched by the audit writer is
SQLite-compatible — ``String``/``Float``/``DateTime``/``JSON``/``Boolean``/
``Text``). The pipeline's own DB session (which would touch
``job_vacancies`` / ``interviews`` / ``candidates`` — those models use
PostgreSQL-specific UUID/ARRAY columns) is mocked at the boundary so the
test can run without standing up Postgres.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from lia_models.audit_log import AuditLog


# ─────────────────────────────────────────────────────────────────────────────
# In-memory audit DB fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def audit_db_sessionmaker():
    """
    Spin up an in-memory aiosqlite engine, create just the ``audit_logs`` table,
    and yield an ``async_sessionmaker`` bound to it. ``audit_service`` is
    monkey-patched in the tests below to use this sessionmaker instead of the
    real Postgres ``AsyncSessionLocal``.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        # Only the AuditLog table — keeps the schema bootstrap minimal and
        # avoids pulling in PostgreSQL-only column types from sibling models.
        await conn.run_sync(lambda sync_conn: AuditLog.__table__.create(sync_conn))

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        yield sessionmaker
    finally:
        await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Job + DB-session fixtures for the pipeline itself
# ─────────────────────────────────────────────────────────────────────────────

DISCRIMINATORY_DESCRIPTION = (
    "Buscamos apenas homens jovens com idade máxima 30 anos. "
    "Contato: recrutador joao.silva@example.com, "
    "telefone +55 11 91234-5678, CPF 123.456.789-09."
)

CLEAN_JOB_TITLE_WITH_PII = (
    "Engenheiro Backend (contato joao.silva@example.com, CPF 123.456.789-09)"
)


def _make_job(*, title, description, requirements, technical_requirements=None):
    job = MagicMock()
    job.id = "job-test-1"
    job.title = title
    job.description = description
    job.location = "São Paulo"
    job.company_id = "company-test-1"
    job.requirements = requirements
    job.technical_requirements = technical_requirements or []
    job.created_at = datetime.utcnow()
    job.status = "open"
    return job


def _build_pipeline_db(job):
    """
    Mock ``AsyncSession`` for the pipeline. The pipeline issues a small,
    deterministic sequence of queries; we feed canned results from a queue
    and any unexpected query falls back to "no rows".
    """
    db = MagicMock()

    def _scalar_one_or_none(value):
        r = MagicMock()
        r.scalar_one_or_none.return_value = value
        return r

    def _scalar(value):
        r = MagicMock()
        r.scalar.return_value = value
        return r

    def _empty_distinct():
        r = MagicMock()
        r.fetchall.return_value = []
        scalars = MagicMock()
        scalars.all.return_value = []
        r.scalars.return_value = scalars
        return r

    queue = [
        _scalar_one_or_none(job),  # JobVacancy lookup
        _scalar(0),                # _build_job_status: total Interview count
        _scalar(0),                # _build_job_status: qualified Interview count
        # If FairnessGuard does NOT block (clean-job path), the local search
        # then issues these two queries before bailing because no candidates
        # match. Provide them defensively.
        _empty_distinct(),         # existing candidate_ids on this job
        _empty_distinct(),         # all active candidates (none seeded)
        _scalar_one_or_none(None), # existing sourcing task lookup
    ]

    async def execute(*args, **kwargs):
        if queue:
            return queue.pop(0)
        return _scalar_one_or_none(None)

    db.execute = AsyncMock(side_effect=execute)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — discriminatory JD blocks pipeline AND persists audit_logs rows
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_discriminatory_jd_blocks_pipeline_and_persists_audit_rows(
    audit_db_sessionmaker,
):
    """
    Run the full ``SourcingPipelineService.run_pipeline_for_job`` against a
    discriminatory JD. Assert that:

    * No ``Interview`` row is added to the pipeline DB session.
    * After the run, the in-memory ``audit_logs`` table contains at least one
      row with ``decision="rejected"`` for this job, written by the actual
      ``audit_service.log_decision`` (no mocking of the audit service itself).
    """
    from app.domains.sourcing.services.sourcing_pipeline_service import (
        SourcingPipelineService,
    )

    job = _make_job(
        title="Atendente",
        description=DISCRIMINATORY_DESCRIPTION,
        requirements=["comunicação"],
    )
    db = _build_pipeline_db(job)

    svc = SourcingPipelineService()

    with patch(
        "app.shared.compliance.audit_service.AsyncSessionLocal",
        new=audit_db_sessionmaker,
    ), patch(
        "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
        new_callable=AsyncMock,
    ):
        result = await svc.run_pipeline_for_job(
            db, job.id, force_global_search=True
        )

    assert result.success is True, result.error_message
    assert result.candidates_added == 0
    assert result.candidates_found_local == 0
    assert result.candidates_found_global == 0

    # No Interview row was added to the pipeline session.
    interview_adds = [
        c for c in db.add.call_args_list
        if type(c.args[0]).__name__ == "Interview"
    ]
    assert interview_adds == [], (
        f"Discriminatory JD must not produce Interview rows, got {interview_adds}"
    )

    # ── audit_logs DB contents ──────────────────────────────────────────────
    async with audit_db_sessionmaker() as session:
        rows = (
            await session.execute(
                select(AuditLog).where(
                    AuditLog.job_vacancy_id == str(job.id),
                    AuditLog.decision == "rejected",
                )
            )
        ).scalars().all()

    assert len(rows) >= 1, (
        f"Expected ≥ 1 rejected AuditLog row for job {job.id}, got {len(rows)}"
    )
    for row in rows:
        assert row.company_id == job.company_id
        assert row.agent_name == "sourcing_pipeline_service"
        assert row.decision_type == "reject_candidate"
        # criteria_ignored must include protected attributes (anti-bias contract).
        assert "gender" in (row.criteria_ignored or [])
        assert "age" in (row.criteria_ignored or [])

    # The rejection reasoning explicitly mentions the discriminatory block.
    joined_reasoning = " | ".join(
        " ".join(r.reasoning or []) for r in rows
    )
    assert "discriminatory" in joined_reasoning.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — PII in the job is NEVER forwarded to Pearch (real call path)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pii_in_job_is_masked_before_reaching_pearch(
    audit_db_sessionmaker,
):
    """
    Use a *clean* (non-discriminatory) job that nonetheless carries PII in
    fields that DO end up in the Pearch query (title, location, skills) plus
    the description. Run the pipeline with ``force_global_search=True`` so
    ``_run_global_search`` actually reaches the (mocked) Pearch call. Assert
    the query string Pearch sees has email / CPF / phone removed.
    """
    from app.domains.sourcing.services import sourcing_pipeline_service as mod
    from app.domains.sourcing.services.sourcing_pipeline_service import (
        SourcingPipelineService,
    )

    # PII is intentionally placed in BOTH the description (email + CPF, per
    # the task spec "PII in the job description is not forwarded to Pearch")
    # AND in title / technical_requirements (which the current
    # _run_global_search implementation actually concatenates into the query
    # string) so the assertion is non-vacuous regardless of which fields end
    # up in the outbound query.
    job = _make_job(
        title=CLEAN_JOB_TITLE_WITH_PII,
        description=(
            "Vaga sênior de back-end. "
            "Recrutador joao.silva@example.com, CPF 123.456.789-09, "
            "telefone +55 11 91234-5678."
        ),
        requirements=["Python", "FastAPI"],
        technical_requirements=[
            {"technology": "Python", "level": "Avançado"},
            {"technology": "FastAPI", "level": "Pleno"},
            {"technology": "contato joao.silva@example.com", "level": "n/a"},
        ],
    )
    db = _build_pipeline_db(job)

    pearch_calls: list[str] = []

    async def fake_pearch_search(query, search_type="fast", limit=20):
        pearch_calls.append(query)
        resp = MagicMock()
        resp.candidates = []
        return resp

    svc = SourcingPipelineService()

    with patch(
        "app.shared.compliance.audit_service.AsyncSessionLocal",
        new=audit_db_sessionmaker,
    ), patch(
        "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
        new_callable=AsyncMock,
    ), patch.object(
        mod.pearch_service, "search_candidates", side_effect=fake_pearch_search
    ):
        result = await svc.run_pipeline_for_job(
            db, job.id, force_global_search=True
        )

    assert result.success is True, result.error_message

    # Pearch MUST have been invoked in this clean-job scenario.
    assert len(pearch_calls) >= 1, (
        "Expected Pearch to be called for a non-blocked job under "
        "force_global_search=True"
    )

    for query in pearch_calls:
        assert "joao.silva@example.com" not in query, (
            f"Email PII leaked to Pearch: {query!r}"
        )
        assert "123.456.789-09" not in query, (
            f"CPF PII leaked to Pearch: {query!r}"
        )
        assert "91234-5678" not in query, (
            f"Phone PII leaked to Pearch: {query!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — local-only path also blocks discriminatory JDs
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_local_path_alone_blocks_discriminatory_jd(
    audit_db_sessionmaker,
):
    """
    Without forcing global search, the local-search path must also block on
    discriminatory criteria and persist at least one ``rejected`` audit row.
    """
    from app.domains.sourcing.services.sourcing_pipeline_service import (
        SourcingPipelineService,
    )

    job = _make_job(
        title="Atendente",
        description=DISCRIMINATORY_DESCRIPTION,
        requirements=["comunicação"],
    )
    db = _build_pipeline_db(job)

    svc = SourcingPipelineService()
    svc.config.auto_expand_to_global = False

    with patch(
        "app.shared.compliance.audit_service.AsyncSessionLocal",
        new=audit_db_sessionmaker,
    ), patch(
        "app.shared.compliance.fairness_guard.FairnessGuard.log_check",
        new_callable=AsyncMock,
    ):
        result = await svc.run_pipeline_for_job(
            db, job.id, force_global_search=False
        )

    assert result.success is True, result.error_message
    assert result.candidates_added == 0

    async with audit_db_sessionmaker() as session:
        rows = (
            await session.execute(
                select(AuditLog).where(
                    AuditLog.job_vacancy_id == str(job.id),
                    AuditLog.decision == "rejected",
                )
            )
        ).scalars().all()

    assert len(rows) >= 1
