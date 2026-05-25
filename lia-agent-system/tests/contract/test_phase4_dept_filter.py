"""
Sprint 2 Phase 4 RBAC — Department scope filter for candidates.

Unit tests for _filter_candidates_by_dept_scope helper.

Canonical principle: soft-launch posture. NULL on either side (user.department_id
or vacancy.department_id) = legacy, no enforcement. Zero breakage migration.

Cases covered:
  T1. User has no dept_id → all candidates visible (legacy user)
  T2. User is admin → all candidates visible
  T3. Candidate has 0 vacancy associations → visible (talent pool)
  T4. Candidate vacancies all match user dept → visible
  T5. Candidate vacancies all mismatch user dept → filtered
  T6. Candidate has ≥1 legacy (NULL) vacancy → visible
  T7. Mixed: at least one matching → visible
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.candidates.candidates_crud import _filter_candidates_by_dept_scope


class _FakeRow:
    def __init__(self, cid: str, dept: str | None):
        self.cid = cid
        self.dept = dept


def _make_candidate(cid: str | None = None):
    c = MagicMock()
    c.id = uuid.UUID(cid) if cid else uuid.uuid4()
    return c


def _make_user(dept_id: str | None, role: str = "recruiter"):
    u = MagicMock()
    u.department_id = uuid.UUID(dept_id) if dept_id else None
    # Avoid MagicMock auto-attribute: explicitly set role attribute
    from app.auth.models import UserRole
    u.role = UserRole(role) if role else None
    return u


def _patch_session(rows: list[_FakeRow]):
    """Patch AsyncSessionLocal to return rows from the JOIN query."""
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(return_value=rows)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    return patch(
        "app.core.database.AsyncSessionLocal",
        MagicMock(return_value=mock_session_cm),
    )


@pytest.mark.asyncio
async def test_t1_user_no_dept_returns_all_unchanged():
    """T1. Legacy user (dept_id=None) → no filtering."""
    user = _make_user(dept_id=None)
    candidates = [_make_candidate() for _ in range(3)]
    result = await _filter_candidates_by_dept_scope(candidates, user)
    assert result == candidates


@pytest.mark.asyncio
async def test_t2_admin_returns_all_unchanged():
    """T2. Admin bypass."""
    user = _make_user(dept_id=str(uuid.uuid4()), role="admin")
    candidates = [_make_candidate() for _ in range(3)]
    result = await _filter_candidates_by_dept_scope(candidates, user)
    assert result == candidates


@pytest.mark.asyncio
async def test_t3_candidate_no_vacancies_is_visible():
    """T3. Talent pool (no VacancyCandidate rows) → visible."""
    user = _make_user(dept_id=str(uuid.uuid4()))
    candidates = [_make_candidate() for _ in range(2)]
    with _patch_session(rows=[]):
        result = await _filter_candidates_by_dept_scope(candidates, user)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_t4_candidate_dept_matches_user_dept_visible():
    """T4. Candidate vacancy dept == user dept → visible."""
    user_dept = str(uuid.uuid4())
    user = _make_user(dept_id=user_dept)
    cand = _make_candidate()
    rows = [_FakeRow(cid=str(cand.id), dept=user_dept)]
    with _patch_session(rows=rows):
        result = await _filter_candidates_by_dept_scope([cand], user)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_t5_candidate_dept_mismatch_filtered():
    """T5. All vacancies in different dept → filtered out."""
    user = _make_user(dept_id=str(uuid.uuid4()))
    other_dept = str(uuid.uuid4())
    cand = _make_candidate()
    rows = [_FakeRow(cid=str(cand.id), dept=other_dept)]
    with _patch_session(rows=rows):
        result = await _filter_candidates_by_dept_scope([cand], user)
    assert result == []


@pytest.mark.asyncio
async def test_t6_candidate_has_legacy_vacancy_visible():
    """T6. ≥1 vacancy with dept=None (legacy) → visible (soft-launch)."""
    user = _make_user(dept_id=str(uuid.uuid4()))
    cand = _make_candidate()
    rows = [_FakeRow(cid=str(cand.id), dept=None)]
    with _patch_session(rows=rows):
        result = await _filter_candidates_by_dept_scope([cand], user)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_t7_mixed_at_least_one_match_visible():
    """T7. Multiple vacancies, ≥1 matches user dept → visible."""
    user_dept = str(uuid.uuid4())
    other_dept = str(uuid.uuid4())
    user = _make_user(dept_id=user_dept)
    cand = _make_candidate()
    rows = [
        _FakeRow(cid=str(cand.id), dept=other_dept),
        _FakeRow(cid=str(cand.id), dept=user_dept),
    ]
    with _patch_session(rows=rows):
        result = await _filter_candidates_by_dept_scope([cand], user)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_t8_empty_input_returns_empty():
    """T8. Empty candidates list → returns empty without query."""
    user = _make_user(dept_id=str(uuid.uuid4()))
    result = await _filter_candidates_by_dept_scope([], user)
    assert result == []
