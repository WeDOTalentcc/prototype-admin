"""
Sprint 6 RBAC — visible scope (1-level manager hierarchy) canonical contract.

Plan: ~/.claude/plans/jolly-roaming-moler.md.

Tests for compute_visible_scope + candidate filter integration.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.rbac.visible_scope import VisibleScope, compute_visible_scope


def _make_user(role: str | None, dept_id: str | None = None, uid: str | None = None, email: str | None = "u@a.com"):
    from app.auth.models import UserRole
    u = MagicMock()
    u.id = uuid.UUID(uid) if uid else uuid.uuid4()
    u.email = email
    u.department_id = uuid.UUID(dept_id) if dept_id else None
    u.role = UserRole(role) if role else None
    return u


def _patch_session(rows: list):
    """Patch AsyncSessionLocal to return rows from subordinate lookup."""
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(return_value=rows)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    return patch(
        "app.shared.rbac.visible_scope.AsyncSessionLocal",
        MagicMock(return_value=mock_session_cm),
    )


def _row(uid: str, email: str, dept: str | None):
    r = MagicMock()
    r.uid = uid
    r.email = email
    r.dept = dept
    return r


# ============================================================================
# A. compute_visible_scope
# ============================================================================


@pytest.mark.asyncio
async def test_t1_none_user_returns_empty_scope():
    """T1: None current_user → empty VisibleScope (defensive)."""
    s = await compute_visible_scope(None)
    assert s.user_id is None
    assert s.is_admin is False
    assert s.has_subordinates is False


@pytest.mark.asyncio
async def test_t2_recruiter_role_skips_subordinate_lookup():
    """T2: recruiter role → no hierarchy lookup (only managers/admins)."""
    user = _make_user(role="recruiter", dept_id=str(uuid.uuid4()))
    # No patch needed — recruiter path shouldn't query DB
    s = await compute_visible_scope(user)
    assert s.role == "recruiter"
    assert s.has_subordinates is False
    assert s.subordinate_user_ids == frozenset()


@pytest.mark.asyncio
async def test_t3_manager_loads_direct_subordinates():
    """T3: manager role → fetches direct subordinates from users WHERE manager_id == self.id."""
    user_uid = str(uuid.uuid4())
    own_dept = str(uuid.uuid4())
    sub_dept_1 = str(uuid.uuid4())
    sub_dept_2 = str(uuid.uuid4())
    user = _make_user(role="manager", dept_id=own_dept, uid=user_uid)

    rows = [
        _row(str(uuid.uuid4()), "sub1@a.com", sub_dept_1),
        _row(str(uuid.uuid4()), "sub2@a.com", sub_dept_2),
        _row(str(uuid.uuid4()), "SUB3@A.COM", sub_dept_1),  # case-insensitive expected
    ]
    with _patch_session(rows):
        s = await compute_visible_scope(user)

    assert s.role == "manager"
    assert s.has_subordinates is True
    assert len(s.subordinate_user_ids) == 3
    assert "sub1@a.com" in s.subordinate_user_emails
    assert "sub3@a.com" in s.subordinate_user_emails  # lowercased
    assert sub_dept_1 in s.subordinate_dept_ids
    assert sub_dept_2 in s.subordinate_dept_ids


@pytest.mark.asyncio
async def test_t4_admin_loads_subordinates_too():
    """T4: admin role → also queries subordinates (admin may be tagged as manager too)."""
    user = _make_user(role="admin", dept_id=str(uuid.uuid4()))
    with _patch_session([_row(str(uuid.uuid4()), "x@a.com", str(uuid.uuid4()))]):
        s = await compute_visible_scope(user)
    assert s.is_admin is True
    assert s.has_subordinates is True


@pytest.mark.asyncio
async def test_t5_viewer_role_skips_subordinate_lookup():
    """T5: viewer role → no hierarchy lookup."""
    user = _make_user(role="viewer", dept_id=str(uuid.uuid4()))
    s = await compute_visible_scope(user)
    assert s.has_subordinates is False


@pytest.mark.asyncio
async def test_t6_visible_dept_ids_union():
    """T6: visible_dept_ids = own_dept ∪ subordinate_depts."""
    own_dept = str(uuid.uuid4())
    sub_dept = str(uuid.uuid4())
    user = _make_user(role="manager", dept_id=own_dept)
    with _patch_session([_row(str(uuid.uuid4()), "s@a.com", sub_dept)]):
        s = await compute_visible_scope(user)
    assert own_dept in s.visible_dept_ids
    assert sub_dept in s.visible_dept_ids
    assert len(s.visible_dept_ids) == 2


@pytest.mark.asyncio
async def test_t7_manager_without_subordinates_returns_empty():
    """T7: manager role mas ninguém aponta pra ele → has_subordinates=False."""
    user = _make_user(role="manager", dept_id=str(uuid.uuid4()))
    with _patch_session([]):  # zero rows
        s = await compute_visible_scope(user)
    assert s.has_subordinates is False
    assert s.subordinate_user_ids == frozenset()


@pytest.mark.asyncio
async def test_t8_db_failure_is_non_blocking():
    """T8: DB exception during subordinate lookup → fallback to no-subordinates scope."""
    user = _make_user(role="manager", dept_id=str(uuid.uuid4()))
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(side_effect=RuntimeError("DB down"))
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    with patch(
        "app.shared.rbac.visible_scope.AsyncSessionLocal",
        MagicMock(return_value=mock_session_cm),
    ):
        s = await compute_visible_scope(user)
    # Must not raise; subordinate lists empty
    assert s.has_subordinates is False


def test_t9_visible_user_ids_includes_self_and_subordinates():
    """T9: visible_user_ids = {self.id} ∪ subordinate_user_ids."""
    uid = str(uuid.uuid4())
    sub1 = str(uuid.uuid4())
    sub2 = str(uuid.uuid4())
    s = VisibleScope(
        user_id=uid,
        user_email="me@a.com",
        own_dept_id=None,
        is_admin=False,
        role="manager",
        subordinate_user_ids=frozenset([sub1, sub2]),
    )
    assert uid in s.visible_user_ids
    assert sub1 in s.visible_user_ids
    assert sub2 in s.visible_user_ids
    assert len(s.visible_user_ids) == 3


def test_t10_visible_dept_ids_excludes_none():
    """T10: visible_dept_ids skips None own_dept."""
    sub_dept = str(uuid.uuid4())
    s = VisibleScope(
        user_id="u",
        user_email="m@a.com",
        own_dept_id=None,
        is_admin=False,
        role="manager",
        subordinate_dept_ids=frozenset([sub_dept]),
    )
    assert s.visible_dept_ids == frozenset([sub_dept])
