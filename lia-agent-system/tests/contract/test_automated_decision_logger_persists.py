"""
WT-2022 P0.C regression sensor (audit 2026-05-21): the
``log_automated_decision`` helper MUST actually persist
``AutomatedDecisionExplanation`` rows for all 4 canonical decision types.

Ghost-helper context: prior to the P0.C fix (commit 2026-05-21), the helper
called ``AutomatedDecisionExplanation(...)`` with kwargs that did not match
the SQLAlchemy model columns (``job_id`` instead of ``vacancy_id``,
``criteria_used`` instead of ``input_criteria``, extra unsupported kwargs
like ``criteria_ignored``, ``confidence_score``, ``review_eligible``,
``extra_metadata``).  The resulting ``TypeError`` was swallowed by a blanket
``except Exception`` returning ``None`` — all 11 wired callers silently
logged ``logger.error`` and ZERO rows were ever written. The
AITransparencyPanel rendered empty → LGPD Art. 20 break in production.

This module pins both contracts:

1. **Kwarg → column mapping** (pure-unit via mocked AsyncSession):
   asserts that ``log_automated_decision(job_id=..., criteria_used=...,
   criteria_ignored=..., confidence_score=..., review_eligible=...,
   extra_metadata=...)`` constructs an ``AutomatedDecisionExplanation``
   instance whose constructor kwargs match the real model columns
   (``vacancy_id``, ``input_criteria``, ``decision_criteria``,
   ``human_review_requested``).  Any future refactor that re-introduces the
   old kwargs will TypeError at construction time and fail CI.

2. **End-to-end persistence** (real ``async_session_factory``): for each of
   the 4 canonical ``decision_type`` strings exercised by the wired callers
   (``wsi_question_generation``, ``candidate_ranking``,
   ``cv_pre_wrf_filter``, ``intake_extraction``), insert a row through the
   helper and re-read it via ``select`` to confirm at least one row exists.
   Cleans up its own rows.

Strategy: hybrid.  The mapping contract is a pure-unit test (fast, no DB).
The persistence sweep uses the real DB session because the bug class under
test (silent swallow of TypeError) only manifests at SQL emit time.  Both
are kept in ``tests/contract/`` because the contract under test is
"helper MUST persist what the caller asked it to persist."
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import delete, select

from app.shared.services.automated_decision_logger import (
    PROTECTED_CRITERIA_PT,
    log_automated_decision,
)


# ---------------------------------------------------------------------------
# Part 1 — Pure-unit kwarg mapping contract (no DB)
# ---------------------------------------------------------------------------


class _ModelConstructorRecorder:
    """Mimic the AutomatedDecisionExplanation constructor and record kwargs.

    Real SQLAlchemy declarative bases reject unknown kwargs at __init__ time
    with ``TypeError: 'foo' is an invalid keyword argument for ...`` — we
    enforce the same contract here so legacy kwargs (job_id, criteria_used)
    fail loudly if they leak into the constructor call.
    """

    ALLOWED_COLUMNS = frozenset(
        {
            "id",
            "company_id",
            "decision_type",
            "candidate_id",
            "vacancy_id",
            "ai_model_used",
            "input_criteria",
            "decision_criteria",
            "explanation_text",
            "explanation_requested_at",
            "explanation_provided_at",
            "human_review_requested",
            "human_review_completed_at",
            "human_review_decision",
            "human_reviewer_id",
            "created_at",
        }
    )

    last_kwargs: dict = {}

    def __init__(self, **kwargs):
        unknown = set(kwargs) - self.ALLOWED_COLUMNS
        if unknown:
            raise TypeError(
                f"_ModelConstructorRecorder: invalid keyword argument(s) for "
                f"AutomatedDecisionExplanation: {sorted(unknown)}"
            )
        type(self).last_kwargs = dict(kwargs)
        self.id = kwargs.get("id") or uuid.uuid4()
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.mark.asyncio
async def test_kwarg_to_column_mapping_no_typeerror():
    """Helper MUST translate external kwargs (job_id, criteria_used, ...) into
    real model columns (vacancy_id, input_criteria, decision_criteria, ...).

    Re-introducing legacy kwargs would TypeError at construction time.
    """
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    test_company_id = str(uuid.uuid4())
    test_job_id = str(uuid.uuid4())
    test_candidate_id = str(uuid.uuid4())

    with patch(
        "app.models.observability.AutomatedDecisionExplanation",
        _ModelConstructorRecorder,
    ):
        decision_id = await log_automated_decision(
            db=db,
            company_id=test_company_id,
            decision_type="cv_pre_wrf_filter",
            explanation_text="contract test mapping",
            candidate_id=test_candidate_id,
            job_id=test_job_id,
            ai_model_used="claude-opus-4-7",
            criteria_used=["skill:python", "experience_years"],
            criteria_ignored=PROTECTED_CRITERIA_PT,
            confidence_score=0.42,
            review_eligible=True,
            extra_metadata={"weights": {"a": 1}, "top_n": 5},
        )

    assert decision_id is not None, "kwarg mapping must succeed and return UUID"

    kw = _ModelConstructorRecorder.last_kwargs
    # External kwarg job_id → column vacancy_id
    assert kw["vacancy_id"] == test_job_id, "job_id MUST map to vacancy_id"
    # External kwarg criteria_used → column input_criteria
    assert kw["input_criteria"] == ["skill:python", "experience_years"], (
        "criteria_used MUST map to input_criteria"
    )
    # Consolidated decision_criteria JSONB
    dc = kw["decision_criteria"]
    assert dc["confidence_score"] == 0.42
    assert dc["review_eligible"] is True
    assert dc["audit_metadata"] == {"weights": {"a": 1}, "top_n": 5}
    assert set(PROTECTED_CRITERIA_PT).issubset(set(dc["criteria_ignored"]))
    # review_eligible=True must also flip human_review_requested
    assert kw["human_review_requested"] is True
    # Forbidden legacy kwargs MUST NOT appear in constructor call
    forbidden = {"job_id", "criteria_used", "criteria_ignored", "confidence_score",
                 "review_eligible", "extra_metadata"}
    leaked = forbidden & set(kw.keys())
    assert not leaked, f"legacy kwargs leaked into model constructor: {leaked}"

    db.add.assert_called_once()
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_protected_criteria_in_criteria_used_raises_fail_loud():
    """LGPD compliance gate: protected criterion in criteria_used MUST raise."""
    db = MagicMock()
    with pytest.raises(ValueError, match="ADR-LGPD-001 VIOLATION"):
        await log_automated_decision(
            db=db,
            company_id=str(uuid.uuid4()),
            decision_type="should_not_pass",
            explanation_text="x",
            criteria_used=["raca", "skill:python"],
        )


@pytest.mark.asyncio
async def test_typeerror_at_persist_reraised_by_default():
    """Pre-fix bug: TypeError swallowed silently.  Post-fix: re-raised."""
    db = MagicMock()
    db.add = MagicMock(side_effect=TypeError("simulated model mismatch"))
    db.flush = AsyncMock()

    class _BoomCtor:
        ALLOWED_COLUMNS = _ModelConstructorRecorder.ALLOWED_COLUMNS

        def __init__(self, **kwargs):
            self.id = uuid.uuid4()

    with patch(
        "app.models.observability.AutomatedDecisionExplanation",
        _BoomCtor,
    ):
        with pytest.raises(TypeError, match="simulated model mismatch"):
            await log_automated_decision(
                db=db,
                company_id=str(uuid.uuid4()),
                decision_type="boom",
                explanation_text="x",
                criteria_used=["skill:python"],
            )


@pytest.mark.asyncio
async def test_typeerror_silenced_when_silent_on_persist_error_true():
    """Fire-and-forget caller (graph.py) can opt into silent degrade."""
    db = MagicMock()
    db.add = MagicMock(side_effect=TypeError("simulated"))
    db.flush = AsyncMock()

    class _BoomCtor:
        def __init__(self, **kwargs):
            self.id = uuid.uuid4()

    with patch(
        "app.models.observability.AutomatedDecisionExplanation",
        _BoomCtor,
    ):
        result = await log_automated_decision(
            db=db,
            company_id=str(uuid.uuid4()),
            decision_type="boom_silenced",
            explanation_text="x",
            criteria_used=["skill:python"],
            silent_on_persist_error=True,
        )
    assert result is None, "silent_on_persist_error must degrade to None"


# ---------------------------------------------------------------------------
# Part 2 — End-to-end persistence sweep (real DB)
# ---------------------------------------------------------------------------


_E2E_MARKER_AUDIT_KEY = "wt_2022_p0c_contract_marker"


@pytest.fixture
def _e2e_marker() -> str:
    """Unique marker stored in decision_criteria.audit_metadata for cleanup."""
    return f"wt-2022-p0c-{uuid.uuid4()}"


@pytest.mark.asyncio
async def test_helper_persists_row_for_all_canonical_decision_types(
    _e2e_marker: str,
):
    """For each canonical decision_type, helper MUST write exactly one row
    and that row MUST be re-readable by SELECT.

    Pre-fix: zero rows written (TypeError swallowed).  Post-fix: one row
    per type.

    Note: the 4 decision types are exercised in a SINGLE test function (not
    parametrized) because ``async_session_factory`` is bound to a
    module-level ``create_async_engine`` whose connection pool sticks to
    the first event loop it sees.  pytest-asyncio creates a fresh loop per
    function-scoped parametrize case, so a parametrized test would error
    with "attached to a different loop" on every case after the first.
    Iterating inside one test keeps everything on the same loop while
    still asserting all 4 types persist correctly.
    """
    try:
        from app.core.database import async_session_factory
    except ImportError:
        pytest.skip("app.core.database.async_session_factory not importable")

    from app.models.observability import AutomatedDecisionExplanation

    canonical_decision_types = [
        "wsi_question_generation",
        "candidate_ranking",
        "cv_pre_wrf_filter",
        "intake_extraction",
    ]

    inserted_ids: list[uuid.UUID] = []
    failures: list[str] = []

    async with async_session_factory() as db:
        try:
            for decision_type in canonical_decision_types:
                test_company_id = str(uuid.uuid4())
                test_job_id = str(uuid.uuid4())
                test_candidate_id = str(uuid.uuid4())

                decision_id = await log_automated_decision(
                    db=db,
                    company_id=test_company_id,
                    decision_type=decision_type,
                    explanation_text=f"contract test for {decision_type}",
                    candidate_id=test_candidate_id,
                    job_id=test_job_id,
                    ai_model_used="contract_test_model",
                    criteria_used=["skill:python", "experience_years"],
                    criteria_ignored=PROTECTED_CRITERIA_PT,
                    confidence_score=0.77,
                    review_eligible=True,
                    extra_metadata={
                        _E2E_MARKER_AUDIT_KEY: _e2e_marker,
                        "type": decision_type,
                    },
                )
                await db.commit()

                if decision_id is None:
                    failures.append(
                        f"{decision_type}: helper returned None (persist "
                        f"failed silently — pre-fix bug)"
                    )
                    continue

                # Re-read by SELECT — load-bearing assertion.
                result = await db.execute(
                    select(AutomatedDecisionExplanation).where(
                        AutomatedDecisionExplanation.decision_type == decision_type,
                        AutomatedDecisionExplanation.company_id == test_company_id,
                    )
                )
                rows = result.scalars().all()
                if len(rows) != 1:
                    failures.append(
                        f"{decision_type}: expected 1 persisted row, got "
                        f"{len(rows)} (pre-fix bug: ZERO rows ever written "
                        f"despite happy logger output)"
                    )
                    continue

                row = rows[0]
                inserted_ids.append(row.id)

                if row.vacancy_id is None:
                    failures.append(f"{decision_type}: vacancy_id not populated")
                if row.input_criteria != ["skill:python", "experience_years"]:
                    failures.append(
                        f"{decision_type}: input_criteria mismatch "
                        f"(got {row.input_criteria!r})"
                    )
                if row.decision_criteria.get("confidence_score") != 0.77:
                    failures.append(
                        f"{decision_type}: decision_criteria.confidence_score "
                        f"mismatch (got {row.decision_criteria!r})"
                    )
                if row.decision_criteria.get("review_eligible") is not True:
                    failures.append(
                        f"{decision_type}: decision_criteria.review_eligible "
                        f"mismatch"
                    )
                audit_meta = row.decision_criteria.get("audit_metadata", {})
                if audit_meta.get(_E2E_MARKER_AUDIT_KEY) != _e2e_marker:
                    failures.append(
                        f"{decision_type}: audit_metadata marker missing "
                        f"(got {audit_meta!r})"
                    )
                if row.human_review_requested is not True:
                    failures.append(
                        f"{decision_type}: human_review_requested not flipped to True"
                    )
        finally:
            # Cleanup all rows inserted by this contract test.
            if inserted_ids:
                await db.execute(
                    delete(AutomatedDecisionExplanation).where(
                        AutomatedDecisionExplanation.id.in_(inserted_ids)
                    )
                )
                await db.commit()

    assert not failures, (
        "AutomatedDecisionExplanation persistence contract failed:\n"
        + "\n".join(f"  - {f}" for f in failures)
    )
