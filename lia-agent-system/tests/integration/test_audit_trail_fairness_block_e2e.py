"""
Task #365 — End-to-end integration test for the fairness-block audit trail.

The unit tests in ``tests/unit/test_scoring_services_fairness_audit.py`` mock
``audit_service.log_decision`` and only prove that each scoring service *calls*
the audit logger when FairnessGuard blocks a candidate. They do **not** prove
the audit row actually lands in the ``audit_logs`` table with the regulator-
facing evidence the EU AI Act and LGPD require.

This module closes that loop. Each of the five candidate-scoring services is
exercised against an **in-memory aiosqlite** ``audit_logs`` table by
monkey-patching ``app.shared.compliance.audit_service.AsyncSessionLocal``.
After the service is invoked with a discriminatory input, we query the real
``audit_logs`` table and assert the persisted row carries:

* ``action == "cv_screening.fairness_block"``
* the candidate / job ``subject_id`` (when the call site has them)
* ``regulatory_basis`` containing both ``EU_AI_ACT_HIGH_RISK`` and
  ``LGPD_ART_20`` inside the ``reasoning`` JSON column
* the FairnessGuard category that triggered the block (in ``reasoning``)

The test runs in CI without external dependencies — only the ``audit_logs``
table is created on aiosqlite (its column types are SQLite-compatible).
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from lia_models.audit_log import AuditLog


# Discriminatory phrases that FairnessGuard hard-blocks in the
# "aparencia_fisica" and "idade" categories. Same constants as the unit tests.
DISCRIMINATORY_APPEARANCE = "Procuramos candidato com excelente aparência"
DISCRIMINATORY_AGE = "Buscamos apenas jovens para essa vaga"


# ─────────────────────────────────────────────────────────────────────────────
# In-memory audit DB fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def audit_db_sessionmaker():
    """Spin up an in-memory aiosqlite engine, create the ``audit_logs`` table,
    and yield an ``async_sessionmaker`` bound to it.

    ``audit_service.AsyncSessionLocal`` is monkey-patched in each test to use
    this sessionmaker so calls land in this real (test) database.
    """
    # File-backed SQLite (not :memory:) so the audit_logs table is visible to
    # every connection — including ones opened by fire-and-forget audit tasks
    # scheduled via ``schedule_audit_log`` from the sync scoring services.
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "audit.sqlite"
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            future=True,
        )
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: AuditLog.__table__.create(sync_conn))

        sessionmaker = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        try:
            yield sessionmaker
        finally:
            await engine.dispose()


def _patched_audit_session(sessionmaker):
    """Replace ``audit_service.AsyncSessionLocal`` with the in-memory factory."""
    return patch(
        "app.shared.compliance.audit_service.AsyncSessionLocal",
        new=sessionmaker,
    )


async def _wait_for_fairness_block_rows(
    sessionmaker,
    *,
    expected: int = 1,
    timeout: float = 2.0,
) -> list[AuditLog]:
    """Poll the in-memory audit_logs table until ``expected`` rows are present.

    The sync scoring services (``LIAScoreService``, ``PreQualificationService``,
    ``EligibilityVerificationService``) emit the audit row via
    ``schedule_audit_log`` which schedules a fire-and-forget task on the
    running loop. Polling the actual table — instead of broadly draining every
    pending asyncio task — keeps the test deterministic and immune to
    unrelated background tasks living in the test runtime.
    """
    deadline = asyncio.get_running_loop().time() + timeout
    rows: list[AuditLog] = []
    while True:
        async with sessionmaker() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.action == "cv_screening.fairness_block"
                )
            )
            rows = list(result.scalars().all())
        if len(rows) >= expected:
            return rows
        if asyncio.get_running_loop().time() >= deadline:
            return rows
        await asyncio.sleep(0.02)


def _assert_regulator_evidence(
    row: AuditLog,
    *,
    expected_agent: str,
    expected_category: str,
    expected_subject_id: str | None = None,
) -> None:
    """Common assertions every persisted fairness-block row must satisfy."""
    assert row.action == "cv_screening.fairness_block"
    assert row.agent_name == expected_agent
    assert row.decision == "rejected"
    assert row.human_review_required is True

    reasoning = row.reasoning or []
    assert isinstance(reasoning, list) and reasoning

    # FairnessGuard category that triggered the block is in the reasoning trail.
    expected_line = f"FairnessGuard blocked: category={expected_category}"
    assert any(
        isinstance(r, str) and r == expected_line
        for r in reasoning
    ), f"expected category line {expected_line!r} not in reasoning: {reasoning!r}"

    # Regulatory basis (EU AI Act high-risk + LGPD Art. 20) is persisted.
    basis_entries = [
        r for r in reasoning
        if isinstance(r, dict) and "regulatory_basis" in r
    ]
    assert basis_entries, (
        f"regulatory_basis dict missing from reasoning: {reasoning!r}"
    )
    basis = basis_entries[0]["regulatory_basis"]
    assert "EU_AI_ACT_HIGH_RISK" in basis
    assert "LGPD_ART_20" in basis

    if expected_subject_id is not None:
        # Either the column or the subject_id breadcrumb in reasoning carries it.
        column_match = (
            row.candidate_id == expected_subject_id
            or row.job_vacancy_id == expected_subject_id
        )
        breadcrumb_match = any(
            isinstance(r, str) and f"subject_id={expected_subject_id}" in r
            for r in reasoning
        )
        assert column_match or breadcrumb_match, (
            f"subject_id {expected_subject_id} not present on row "
            f"(candidate_id={row.candidate_id}, job_vacancy_id={row.job_vacancy_id})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# C1 — CVScoringService.screen_candidate
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cv_scoring_service_persists_fairness_block_row(audit_db_sessionmaker):
    from app.domains.cv_screening.services import cv_scoring_service as mod

    svc = mod.CVScoringService()
    candidate_id = str(uuid4())
    vacancy_id = str(uuid4())
    candidate_data = {
        "id": candidate_id,
        "name": "Test",
        "resume_text": DISCRIMINATORY_APPEARANCE,
    }

    with _patched_audit_session(audit_db_sessionmaker), \
         patch.object(svc, "_get_candidate_data",
                      new_callable=AsyncMock, return_value=candidate_data), \
         patch.object(svc, "_get_job_requirements",
                      new_callable=AsyncMock, return_value=[MagicMock()]), \
         patch.object(svc, "_get_job_info",
                      new_callable=AsyncMock, return_value={"title": "Dev"}), \
         patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                      new_callable=AsyncMock):
        result = await svc.screen_candidate(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id="company-001",
            db=AsyncMock(),
        )
        assert result["error"] == "fairness_block"
        

        rows = await _wait_for_fairness_block_rows(audit_db_sessionmaker)

    assert len(rows) == 1, f"expected exactly one persisted row, got {len(rows)}"
    _assert_regulator_evidence(
        rows[0],
        expected_agent="cv_scoring_service",
        expected_category="aparencia_fisica",
        expected_subject_id=candidate_id,
    )
    assert rows[0].company_id == "company-001"


# ─────────────────────────────────────────────────────────────────────────────
# C2 — LIAScoreService.calculate_score (sync service via schedule_audit_log)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lia_score_service_persists_fairness_block_row(audit_db_sessionmaker):
    from app.domains.cv_screening.services import lia_score_service as mod
    from app.shared.compliance.scoring_safeguards import FairnessBlockedError

    svc = mod.LIAScoreService()
    candidate_id = str(uuid4())
    job_id = str(uuid4())
    candidate = {"id": candidate_id, "skills": ["python"], "company_id": "company-002"}
    criteria = {
        "query": DISCRIMINATORY_AGE,
        "company_id": "company-002",
        "job_id": job_id,
    }

    with _patched_audit_session(audit_db_sessionmaker):
        with pytest.raises(FairnessBlockedError):
            svc.calculate_score(candidate=candidate, criteria=criteria)
        

        rows = await _wait_for_fairness_block_rows(audit_db_sessionmaker)

    assert len(rows) == 1
    _assert_regulator_evidence(
        rows[0],
        expected_agent="lia_score_service",
        expected_category="idade",
        expected_subject_id=candidate_id,
    )
    assert rows[0].job_vacancy_id == job_id


# ─────────────────────────────────────────────────────────────────────────────
# C3 — PreQualificationService.evaluate (sync service via schedule_audit_log)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pre_qualification_service_persists_fairness_block_row(audit_db_sessionmaker):
    from app.domains.cv_screening.services import pre_qualification_service as mod
    from app.shared.compliance.scoring_safeguards import FairnessBlockedError

    svc = mod.PreQualificationService()

    with _patched_audit_session(audit_db_sessionmaker):
        with pytest.raises(FairnessBlockedError):
            svc.evaluate(
                adherence_score=80.0,
                matched_requirements=[],
                missing_requirements=[],
                job_title=DISCRIMINATORY_AGE,
                company_name="ACME",
            )
        

        rows = await _wait_for_fairness_block_rows(audit_db_sessionmaker)

    assert len(rows) == 1
    _assert_regulator_evidence(
        rows[0],
        expected_agent="pre_qualification_service",
        expected_category="idade",
    )


# ─────────────────────────────────────────────────────────────────────────────
# C4 — EligibilityVerificationService.check_answer (sync service)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_eligibility_verification_service_persists_fairness_block_row(
    audit_db_sessionmaker,
):
    from app.domains.cv_screening.services import (
        eligibility_verification_service as mod,
    )
    from app.shared.compliance.scoring_safeguards import FairnessBlockedError

    svc = mod.EligibilityVerificationService()
    question = mod.EligibilityQuestion(
        id="q1",
        question_text=DISCRIMINATORY_APPEARANCE,
        question_type="text",
        options=None,
        is_eliminatory=True,
        expected_answer="sim",
        category="default",
    )

    with _patched_audit_session(audit_db_sessionmaker):
        with pytest.raises(FairnessBlockedError):
            svc.check_answer(question=question, answer="sim")
        

        rows = await _wait_for_fairness_block_rows(audit_db_sessionmaker)

    assert len(rows) == 1
    _assert_regulator_evidence(
        rows[0],
        expected_agent="eligibility_verification_service",
        expected_category="aparencia_fisica",
    )


# ─────────────────────────────────────────────────────────────────────────────
# C5 — EvaluationCriteriaService.get_criteria_for_requirements (async service)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evaluation_criteria_service_persists_fairness_block_row(
    audit_db_sessionmaker,
):
    from app.domains.cv_screening.services import evaluation_criteria_service as mod
    from app.shared.compliance.scoring_safeguards import FairnessBlockedError

    svc = mod.EvaluationCriteriaService()
    mock_db = AsyncMock()

    with _patched_audit_session(audit_db_sessionmaker):
        with pytest.raises(FairnessBlockedError):
            await svc.get_criteria_for_requirements(
                db=mock_db,
                requirements=[DISCRIMINATORY_APPEARANCE, "Python avançado"],
            )
        

        rows = await _wait_for_fairness_block_rows(audit_db_sessionmaker)

    assert len(rows) == 1
    _assert_regulator_evidence(
        rows[0],
        expected_agent="evaluation_criteria_service",
        expected_category="aparencia_fisica",
    )
    mock_db.execute.assert_not_called()
