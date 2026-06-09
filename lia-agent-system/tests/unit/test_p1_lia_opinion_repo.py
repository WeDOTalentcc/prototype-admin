"""TDD red-phase — P1 LiaOpinionRepository ADR-001 + field clobber.

Two P1 items:

P1-LiaRepo: ADR-001 fix — two services do inline select(LiaOpinion):
  - handlers_screening._persist_lia_opinion_with_ocean: _select(LiaOpinion)
  - transition_dispatch_service._record_bigfive_hire: _select(LiaOpinion)
  Both should delegate to OpinionsRepository (already exists in
  app/domains/opinions/repositories/opinions_repository.py).

P1-Clobber: _persist_lia_opinion_with_ocean overwrites wsi_score,
  recommendation, source even when existing opinion came from
  full_interview. A candidate who completed a real interview gets
  downgraded to text_screening when WSI scoring re-runs.
  Fix: only overwrite authority fields when new source has SAME or
  HIGHER priority (cv_analysis < text_screening < full_interview).
  behavioral_analysis['ocean_traits'] ALWAYS updates (new data).
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ── Opinions repo new methods ────────────────────────────────────────────────


def test_opinions_repo_has_get_latest_for_candidate_company():
    """OpinionsRepository must expose get_latest_for_candidate_company so
    _record_bigfive_hire can read ocean_traits without inline SQL."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )
    assert hasattr(OpinionsRepository, "get_latest_for_candidate_company"), (
        "OpinionsRepository missing get_latest_for_candidate_company(candidate_id, company_id). "
        "Add method: returns most recent LiaOpinion ordered by created_at desc, limit 1."
    )


def test_opinions_repo_has_get_latest_for_candidate_vacancy():
    """OpinionsRepository must expose get_latest_for_candidate_vacancy for
    _persist_lia_opinion_with_ocean to look up the existing row."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )
    assert hasattr(OpinionsRepository, "get_latest_for_candidate_vacancy"), (
        "OpinionsRepository missing get_latest_for_candidate_vacancy("
        "candidate_id, vacancy_id, company_id). "
        "Returns most recent is_current LiaOpinion for that (candidate, vacancy, company) triple."
    )


def test_opinions_repo_has_upsert_ocean_opinion():
    """OpinionsRepository must expose upsert_ocean_opinion so the field-
    clobber guard lives in one place (not scattered across callers)."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )
    assert hasattr(OpinionsRepository, "upsert_ocean_opinion"), (
        "OpinionsRepository missing upsert_ocean_opinion(...). "
        "Add: upsert LiaOpinion(opinion_type='wsi') with OCEAN traits, "
        "with source-priority guard to prevent full_interview downgrade."
    )


# ── ADR-001 inline select eliminated ────────────────────────────────────────


def test_persist_lia_opinion_no_inline_select():
    """_persist_lia_opinion_with_ocean must NOT contain inline _select or
    select(LiaOpinion). DB operations must go through OpinionsRepository."""
    import inspect
    from app.api.v1.automation.event_handlers import handlers_screening

    src = inspect.getsource(handlers_screening._persist_lia_opinion_with_ocean)
    assert "_select(LiaOpinion)" not in src, (
        "_persist_lia_opinion_with_ocean still contains _select(LiaOpinion). "
        "Move the SELECT to OpinionsRepository.get_latest_for_candidate_vacancy() "
        "and call that instead."
    )
    assert "select(LiaOpinion)" not in src, (
        "_persist_lia_opinion_with_ocean still contains select(LiaOpinion). "
        "Delegate to OpinionsRepository."
    )


def test_record_bigfive_hire_no_inline_select():
    """_record_bigfive_hire must NOT contain inline _select(LiaOpinion).
    Delegate to OpinionsRepository.get_latest_for_candidate_company()."""
    import inspect
    from app.domains.communication.services import transition_dispatch_service

    src = inspect.getsource(
        transition_dispatch_service.TransitionDispatchService._record_bigfive_hire
    )
    assert "_select(LiaOpinion)" not in src, (
        "_record_bigfive_hire still contains _select(LiaOpinion). "
        "Replace with: OpinionsRepository(self.db).get_latest_for_candidate_company("
        "candidate_id=candidate_id, company_id=str(company_id))"
    )
    assert "select(LiaOpinion)" not in src, (
        "_record_bigfive_hire still contains select(LiaOpinion). "
        "Delegate to OpinionsRepository."
    )


# ── P1-Clobber: field-clobber guard ─────────────────────────────────────────


def _make_mock_opinion(source: str, wsi_score: float = 4.5):
    """Build a MagicMock LiaOpinion with the given source and wsi_score."""
    opinion = MagicMock()
    opinion.source = source
    opinion.wsi_score = wsi_score
    opinion.recommendation = "strong_hire"
    opinion.behavioral_analysis = {"ocean_traits": {}}
    opinion.is_current = True
    opinion.candidate_id = uuid.uuid4()
    opinion.job_vacancy_id = uuid.uuid4()
    opinion.company_id = "00000000-0000-0000-0000-0000000000a1"
    opinion.version = 2
    return opinion


def test_upsert_ocean_opinion_does_not_clobber_full_interview_source():
    """When the existing LiaOpinion has source='full_interview', the
    upsert MUST NOT change source, wsi_score, or recommendation to
    text_screening values. full_interview > text_screening in priority."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    existing = _make_mock_opinion(source="full_interview", wsi_score=4.8)
    original_source = "full_interview"
    original_score = 4.8
    original_rec = "strong_hire"

    mock_db = AsyncMock()
    repo = OpinionsRepository(mock_db)

    # Patch get_latest_for_candidate_vacancy to return the full_interview opinion
    repo.get_latest_for_candidate_vacancy = AsyncMock(return_value=existing)

    async def _run():
        await repo.upsert_ocean_opinion(
            candidate_id=existing.candidate_id,
            vacancy_id=existing.job_vacancy_id,
            company_id=existing.company_id,
            ocean_traits={"openness": 0.7, "conscientiousness": 0.8},
            overall_wsi=3.5,  # LOWER than existing 4.8 — must not overwrite
            recommendation="hire",  # different from strong_hire — must not overwrite
            summary="WSI screening summary",
        )

    asyncio.run(_run())

    assert existing.source == original_source, (
        f"source was overwritten: {existing.source!r} (was {original_source!r}). "
        f"When existing.source='full_interview', text_screening upsert must "
        f"NOT overwrite source/wsi_score/recommendation. Add priority guard:\n"
        f"  _SOURCE_PRIORITY = {{'cv_analysis': 0, 'text_screening': 1, 'full_interview': 2}}\n"
        f"  if _SOURCE_PRIORITY['text_screening'] >= _SOURCE_PRIORITY[existing.source]:"
    )
    assert existing.wsi_score == original_score, (
        f"wsi_score overwritten: {existing.wsi_score} (was {original_score}). "
        f"full_interview score must not be downgraded by text_screening."
    )
    assert existing.recommendation == original_rec, (
        f"recommendation overwritten: {existing.recommendation!r} (was {original_rec!r}). "
        f"full_interview recommendation must not be downgraded."
    )


def test_upsert_ocean_opinion_updates_behavioral_always():
    """behavioral_analysis['ocean_traits'] MUST be updated even when the
    existing source is full_interview. Ocean traits are new measurement
    data — they should always be persisted regardless of source priority."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    existing = _make_mock_opinion(source="full_interview", wsi_score=4.8)
    existing.behavioral_analysis = {"existing_key": "value", "ocean_traits": {}}

    mock_db = AsyncMock()
    repo = OpinionsRepository(mock_db)
    repo.get_latest_for_candidate_vacancy = AsyncMock(return_value=existing)

    new_ocean = {"openness": 0.7, "conscientiousness": 0.8, "stability": 0.6}

    async def _run():
        await repo.upsert_ocean_opinion(
            candidate_id=existing.candidate_id,
            vacancy_id=existing.job_vacancy_id,
            company_id=existing.company_id,
            ocean_traits=new_ocean,
            overall_wsi=3.5,
            recommendation="hire",
            summary=None,
        )

    asyncio.run(_run())

    ba = existing.behavioral_analysis or {}
    assert ba.get("ocean_traits") == new_ocean, (
        f"behavioral_analysis['ocean_traits'] not updated: {ba.get('ocean_traits')!r}. "
        f"Ocean traits must always be written even when source is full_interview — "
        f"they represent new measurement data, not an authority downgrade."
    )
    # Existing unrelated keys should be preserved
    assert ba.get("existing_key") == "value", (
        "Existing behavioral_analysis keys were lost. Merge, don't replace."
    )


def test_upsert_ocean_opinion_does_overwrite_for_text_screening_source():
    """When existing source is text_screening (same level), the upsert
    MUST update wsi_score + recommendation + source (refresh in place)."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    existing = _make_mock_opinion(source="text_screening", wsi_score=2.1)

    mock_db = AsyncMock()
    repo = OpinionsRepository(mock_db)
    repo.get_latest_for_candidate_vacancy = AsyncMock(return_value=existing)

    async def _run():
        await repo.upsert_ocean_opinion(
            candidate_id=existing.candidate_id,
            vacancy_id=existing.job_vacancy_id,
            company_id=existing.company_id,
            ocean_traits={"openness": 0.6},
            overall_wsi=3.8,  # updated score
            recommendation="hire",
            summary=None,
        )

    asyncio.run(_run())

    assert existing.wsi_score == pytest.approx(3.8), (
        f"wsi_score not updated from text_screening: {existing.wsi_score}. "
        f"Same-priority source upsert must refresh authority fields."
    )


def test_upsert_ocean_opinion_creates_new_when_no_existing():
    """When no existing LiaOpinion, upsert_ocean_opinion must create a
    new LiaOpinion with opinion_type='wsi' and source='text_screening'."""
    from app.repositories.opinions_repository import (
        OpinionsRepository,
    )

    mock_db = MagicMock()
    mock_db.add = MagicMock()
    # mark_vacancy_opinions_non_current calls db.execute — needs AsyncMock
    mock_db.execute = AsyncMock(return_value=MagicMock())
    repo = OpinionsRepository(mock_db)
    repo.get_latest_for_candidate_vacancy = AsyncMock(return_value=None)

    candidate_id = uuid.uuid4()
    vacancy_id = uuid.uuid4()
    company_id = str(uuid.uuid4())

    async def _run():
        await repo.upsert_ocean_opinion(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
            ocean_traits={"openness": 0.5},
            overall_wsi=3.0,
            recommendation="hire",
            summary="summary text",
        )

    asyncio.run(_run())

    assert mock_db.add.called, (
        "db.add was not called when no existing opinion. New LiaOpinion "
        "must be created via db.add(opinion)."
    )
    added_opinion = mock_db.add.call_args[0][0]
    from app.models.lia_opinion import LiaOpinion
    assert isinstance(added_opinion, LiaOpinion), (
        f"db.add received {type(added_opinion).__name__}, expected LiaOpinion."
    )
    assert added_opinion.opinion_type == "wsi"
    assert added_opinion.source == "text_screening"
    assert (added_opinion.behavioral_analysis or {}).get("ocean_traits") == {"openness": 0.5}
