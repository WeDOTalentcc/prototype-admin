"""
Unit tests — CVScoringService._update_candidate_score

Verifies that the screening-score update path uses the correct
VacancyCandidate.vacancy_id column (not the non-existent job_vacancy_id),
that the matching row has its score fields written, and that a missing row
is handled gracefully (no exception raised).
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.cv_screening.services.cv_scoring_service import CVScoringService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vc(**extra):
    """Return a minimal VacancyCandidate-like mock with score attributes."""
    vc = MagicMock()
    vc.cv_score = None
    vc.cv_fit_score = None
    vc.sub_status = None
    vc.screening_completed_at = None
    vc.ai_analysis = {}
    for k, v in extra.items():
        setattr(vc, k, v)
    return vc


def _make_db(scalar_result):
    """Return an AsyncSession mock whose execute() returns scalar_result."""
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = scalar_result

    db = AsyncMock()
    db.execute.return_value = result_mock
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_candidate_score_uses_vacancy_id_column():
    """
    _update_candidate_score must query on VacancyCandidate.vacancy_id.
    Before the fix it queried on the non-existent job_vacancy_id, raising
    AttributeError at query-build time so the row was never updated.
    """
    service = CVScoringService()

    candidate_id = str(uuid.uuid4())
    vacancy_id = str(uuid.uuid4())

    vc = _make_vc()
    db = _make_db(vc)

    await service._update_candidate_score(
        candidate_id=candidate_id,
        vacancy_id=vacancy_id,
        score=82.5,
        cv_fit_score=78.0,
        sub_status="aprovado",
        db=db,
    )

    db.execute.assert_awaited_once()
    compiled_where = str(db.execute.call_args[0][0])
    assert "vacancy_candidates.vacancy_id" in compiled_where, (
        "Query must filter on vacancy_id, not job_vacancy_id"
    )
    assert "vacancy_candidates.candidate_id" in compiled_where


@pytest.mark.asyncio
async def test_update_candidate_score_writes_fields_when_row_found():
    """When a matching VacancyCandidate exists, all score fields are updated."""
    service = CVScoringService()

    vc = _make_vc()
    db = _make_db(vc)

    await service._update_candidate_score(
        candidate_id=str(uuid.uuid4()),
        vacancy_id=str(uuid.uuid4()),
        score=90.0,
        cv_fit_score=85.5,
        sub_status="triagem_concluida",
        db=db,
    )

    assert vc.cv_score == 90.0
    assert vc.cv_fit_score == 85.5
    assert vc.sub_status == "triagem_concluida"
    assert vc.screening_completed_at is not None
    assert isinstance(vc.ai_analysis, dict)
    assert "cv_screening" in vc.ai_analysis
    assert vc.ai_analysis["cv_screening"]["rubric_score"] == 90.0
    assert vc.ai_analysis["cv_screening"]["cv_fit_score"] == 85.5
    assert vc.ai_analysis["cv_screening"]["sub_status"] == "triagem_concluida"


@pytest.mark.asyncio
async def test_update_candidate_score_no_error_when_row_not_found():
    """When no matching row exists, the method must return silently."""
    service = CVScoringService()

    db = _make_db(scalar_result=None)

    await service._update_candidate_score(
        candidate_id=str(uuid.uuid4()),
        vacancy_id=str(uuid.uuid4()),
        score=50.0,
        cv_fit_score=45.0,
        sub_status="reprovado",
        db=db,
    )
