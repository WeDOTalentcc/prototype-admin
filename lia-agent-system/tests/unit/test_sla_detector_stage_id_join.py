"""Task #1303: SlaNearExpirationDetector joins by recruitment_stage_id.

The detector must resolve a candidate's stage SLA by the structural link
(``VacancyCandidate.recruitment_stage_id`` ↔ ``RecruitmentStage.id``) when the
link is present, and only fall back to fragile name matching for legacy rows
without the id. A naming divergence (accentuation/casing/rename) must NOT
silently disable the alert when the id link exists.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.shared.services.proactive_detector_service import (
    SlaNearExpirationDetector,
)


def _stage_result(rows):
    res = MagicMock()
    res.all = lambda: rows
    return res


def _candidate_result(candidates):
    res = MagicMock()
    res.scalars = lambda: MagicMock(all=lambda: candidates)
    return res


def _fake_db(stage_rows, candidates):
    """db.execute() is called twice: stages first, candidates second."""
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[_stage_result(stage_rows), _candidate_result(candidates)]
    )
    return db


def _candidate(*, recruitment_stage_id, stage, elapsed_hours):
    cand = MagicMock()
    cand.recruitment_stage_id = recruitment_stage_id
    cand.stage = stage
    cand.status = "screening"
    cand.candidate_id = uuid.uuid4()
    cand.stage_entered_at = datetime.utcnow() - timedelta(hours=elapsed_hours)
    return cand


@pytest.mark.asyncio
async def test_id_join_fires_when_name_diverges():
    """Stage renamed/divergent text but id link intact → alert still fires."""
    stage_id = uuid.uuid4()
    # 100h SLA; candidate at 90h elapsed → 90% (between 80% and 100%).
    stage_rows = [(stage_id, "Entrevista Técnica", 100)]
    cand = _candidate(
        recruitment_stage_id=stage_id,
        stage="entrevista tecnica",  # diverges from canonical name (accent/case)
        elapsed_hours=90,
    )
    db = _fake_db(stage_rows, [cand])

    detector = SlaNearExpirationDetector()
    hints = await detector.detect(db, str(uuid.uuid4()))

    assert len(hints) == 1
    assert hints[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_name_fallback_for_legacy_rows_without_id():
    """Legacy row (recruitment_stage_id is None) still matches by name."""
    stage_id = uuid.uuid4()
    stage_rows = [(stage_id, "Triagem", 100)]
    cand = _candidate(
        recruitment_stage_id=None,
        stage="Triagem",  # exact name match (legacy path)
        elapsed_hours=90,
    )
    db = _fake_db(stage_rows, [cand])

    detector = SlaNearExpirationDetector()
    hints = await detector.detect(db, str(uuid.uuid4()))

    assert len(hints) == 1


@pytest.mark.asyncio
async def test_legacy_name_mismatch_does_not_fire():
    """Legacy row with no id and a name that does not match → no alert
    (documents the exact failure mode Task #1303 fixes for linked rows)."""
    stage_id = uuid.uuid4()
    stage_rows = [(stage_id, "Triagem", 100)]
    cand = _candidate(
        recruitment_stage_id=None,
        stage="triagem",  # case divergence, no id link → no SLA resolved
        elapsed_hours=90,
    )
    db = _fake_db(stage_rows, [cand])

    detector = SlaNearExpirationDetector()
    hints = await detector.detect(db, str(uuid.uuid4()))

    assert hints == []
