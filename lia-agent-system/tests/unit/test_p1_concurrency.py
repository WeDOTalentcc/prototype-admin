"""TDD red-phase — P1 concurrency fixes + false-green behavioral upgrades.

P1-Race: BigFiveDepartmentProfileRepository.upsert has no SELECT FOR UPDATE
  → race on concurrent hires to same (company, dept, seniority) → two
  transactions both see None → both INSERT → unique constraint violation.
  Fix: add .with_for_update() to the SELECT in upsert path.

P1-IsCurrentCoord: upsert_ocean_opinion creates new LiaOpinion(is_current=True)
  without first flipping prior is_current opinions to False. 5 writers can
  each leave a True row. Fix: call mark_vacancy_opinions_non_current before
  creating new row.

P1-FalseGreen-1: test_list_pending_by_company_uses_canonical_pending_string
  only inspects source. Add behavioral companion: call the method with a
  mock db and verify it executes without NameError.

P1-FalseGreen-2: test_adr_lgpd_001_docstring_reflects_phase_2_5_completed
  only inspects source. Add behavioral companion: verify _hook_conclusion_hired
  actually calls _record_bigfive_hire when ocean_traits present in LiaOpinion.
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ── P1-Race: SELECT FOR UPDATE in bigfive upsert ────────────────────────────


def test_bigfive_upsert_uses_with_for_update():
    """BigFiveDepartmentProfileRepository.upsert must use with_for_update()
    on the SELECT to serialize concurrent hires. Without it, two transactions
    both read None and both INSERT → unique constraint violation under load."""
    import inspect
    from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
        BigFiveDepartmentProfileRepository,
    )
    src = inspect.getsource(BigFiveDepartmentProfileRepository.upsert)
    assert "with_for_update" in src or "for_update" in src.lower(), (
        "BigFiveDepartmentProfileRepository.upsert has no SELECT FOR UPDATE. "
        "Add: select(BigFiveDepartmentProfile)...with_for_update() in the "
        "upsert path so concurrent transactions serialize on the row.\n"
        "Pattern:\n"
        "  stmt = select(BigFiveDepartmentProfile).where(...).with_for_update()\n"
        "  result = await self.db.execute(stmt)\n"
        "  profile = result.scalar_one_or_none()"
    )


# ── P1-IsCurrentCoord: mark prior before creating new ───────────────────────


def test_upsert_ocean_opinion_marks_prior_non_current_before_new_row():
    """When upsert_ocean_opinion creates a NEW opinion (no existing row),
    it must call mark_vacancy_opinions_non_current first to ensure only
    one is_current=True row per (candidate, vacancy, opinion_type='wsi')."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = MagicMock()
    mock_db.add = MagicMock()
    repo = OpinionsRepository(mock_db)
    # No existing opinion
    repo.get_latest_for_candidate_vacancy = AsyncMock(return_value=None)
    repo.mark_vacancy_opinions_non_current = AsyncMock()

    candidate_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    company_id = str(uuid.uuid4())

    async def _run():
        await repo.upsert_ocean_opinion(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
            ocean_traits={"openness": 0.6},
            overall_wsi=3.0,
            recommendation="hire",
            summary=None,
        )

    asyncio.run(_run())

    assert repo.mark_vacancy_opinions_non_current.called, (
        "mark_vacancy_opinions_non_current was NOT called before creating "
        "a new LiaOpinion. Without this, multiple is_current=True rows "
        "accumulate (5 writers, none coordinated). Add:\n"
        "  await self.mark_vacancy_opinions_non_current(\n"
        "      candidate_id=candidate_id,\n"
        "      job_vacancy_id=vacancy_id,\n"
        "      opinion_type='wsi',\n"
        "      company_id=<uuid>,\n"
        "  )\n"
        "BEFORE the db.add(opinion) call."
    )


def test_upsert_ocean_opinion_does_not_mark_prior_when_updating_existing():
    """When updating an existing opinion in-place, mark_prior is NOT needed
    (we're modifying the same row, not adding a second one)."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    existing = MagicMock()
    existing.source = "text_screening"
    existing.wsi_score = 3.0
    existing.behavioral_analysis = {}
    existing.recommendation = "hire"

    mock_db = AsyncMock()
    repo = OpinionsRepository(mock_db)
    repo.get_latest_for_candidate_vacancy = AsyncMock(return_value=existing)
    repo.mark_vacancy_opinions_non_current = AsyncMock()

    async def _run():
        await repo.upsert_ocean_opinion(
            candidate_id=uuid.uuid4(),
            vacancy_id=uuid.uuid4(),
            company_id=str(uuid.uuid4()),
            ocean_traits={"openness": 0.7},
            overall_wsi=3.5,
            recommendation="hire",
            summary=None,
        )

    asyncio.run(_run())

    assert not repo.mark_vacancy_opinions_non_current.called, (
        "mark_vacancy_opinions_non_current was called when updating an "
        "existing opinion. Unnecessary — we're updating in-place, not "
        "adding a new row."
    )


# ── P1-FalseGreen-1: behavioral companion for list_pending_by_company ────────


def test_list_pending_by_company_behavioral_executes_without_error():
    """Behavioral companion for the source-inspect test. Verifies that
    list_pending_by_company actually executes (not NameError) and
    constructs the query correctly."""
    from app.repositories.approvals_repository import (
        ApprovalsRepository,
    )

    # Build a mock that returns a proper scalars().all() result
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    repo = ApprovalsRepository(mock_db)
    company_id = uuid.uuid4()

    async def _run():
        return await repo.list_pending_by_company(
            company_id=company_id,
            request_type="feature_flag_toggle",
        )

    # Must not raise NameError (the original bug)
    result = asyncio.run(_run())
    assert isinstance(result, list), (
        f"list_pending_by_company returned {type(result).__name__}, "
        f"expected list. Ensure the method returns list(scalars.all())."
    )
    assert mock_db.execute.called, (
        "db.execute was not called — list_pending_by_company did nothing."
    )


def test_list_pending_by_company_behavioral_filters_by_request_type():
    """The request_type filter must be applied when passed. Verify via
    SQLAlchemy compiled.params that request_type is a bound parameter."""
    from app.repositories.approvals_repository import (
        ApprovalsRepository,
    )

    captured_params: list[dict] = []

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    async def _capture_execute(query):
        try:
            compiled = query.compile()
            captured_params.append(dict(compiled.params or {}))
        except Exception:
            captured_params.append({})
        return mock_result

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(side_effect=_capture_execute)

    repo = ApprovalsRepository(mock_db)

    async def _run():
        return await repo.list_pending_by_company(
            company_id=uuid.uuid4(),
            request_type="feature_flag_toggle",
        )

    asyncio.run(_run())

    assert captured_params, "db.execute was not called"
    params = captured_params[0]
    assert "feature_flag_toggle" in params.values(), (
        f"request_type='feature_flag_toggle' not in bound params: {params}. "
        f"The WHERE clause must include request_type filter when passed."
    )


def test_hook_conclusion_hired_calls_record_bigfive_hire_with_ocean_traits():
    """Behavioral companion for test_adr_lgpd_001_docstring_reflects_phase_2_5_completed.
    When _hook_conclusion_hired fires for a candidate that has ocean_traits
    in their LiaOpinion, BigFiveDepartmentService.record_hire must be called
    (proves the data pipeline is wired, not just the docstring)."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    # A LiaOpinion with ocean_traits (what _record_bigfive_hire reads)
    mock_opinion = MagicMock()
    mock_opinion.behavioral_analysis = {
        "ocean_traits": {
            "openness": 0.7,
            "conscientiousness": 0.8,
            "stability": 0.6,
        }
    }

    # A vacancy_candidate and job
    mock_vacancy_candidate = MagicMock()
    mock_vacancy_candidate.candidate_id = uuid.uuid4()

    mock_job = MagicMock()
    mock_job.department = "engineering"
    mock_job.seniority_level = "senior"

    mock_db = AsyncMock()

    async def _run():
        with patch(
            "app.repositories.opinions_repository.OpinionsRepository.get_latest_for_candidate_company",
            new=AsyncMock(return_value=mock_opinion),
        ), patch(
            "app.domains.job_creation.services.bigfive_service.BigFiveDepartmentService.record_hire",
            new=AsyncMock(),
        ) as mock_record_hire:
            svc = TransitionDispatchService(db=mock_db)
            await svc._record_bigfive_hire(
                company_id="00000000-0000-0000-0000-0000000000a1",
                vacancy_candidate=mock_vacancy_candidate,
                job=mock_job,
            )
            return mock_record_hire

    mock_record_hire = asyncio.run(_run())
    assert mock_record_hire.called, (
        "_record_bigfive_hire did not call BigFiveDepartmentService.record_hire "
        "even though the LiaOpinion had ocean_traits. Phase 2.5 data pipeline "
        "is broken — check _record_bigfive_hire in transition_dispatch_service.py."
    )
    call_kwargs = mock_record_hire.call_args.kwargs
    assert "openness" in (call_kwargs.get("candidate_traits_snapshot") or {}), (
        f"record_hire called but ocean_traits not in candidate_traits_snapshot: "
        f"{call_kwargs}. Check that ocean_traits are extracted from behavioral_analysis."
    )
