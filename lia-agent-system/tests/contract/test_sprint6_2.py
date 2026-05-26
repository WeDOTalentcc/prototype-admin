"""
Sprint 6.2 RBAC — interviews + tasks visible scope filter contract.

Plan: ~/.claude/plans/jolly-roaming-moler.md.

Pin filter behavior for:
  - _filter_tasks_by_visible_scope (tasks endpoint)
  - interview filter inline (interviews list endpoint)
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.tasks import _filter_tasks_by_visible_scope
from app.shared.rbac.visible_scope import VisibleScope


def _make_task(assignee_id: str | None = None, tid: str | None = None):
    t = MagicMock()
    t.id = tid or str(uuid.uuid4())
    t.assigned_to_user_id = assignee_id
    return t


def _make_user(role: str, dept_id: str | None = None, uid: str | None = None):
    from app.auth.models import UserRole
    u = MagicMock()
    u.id = uuid.UUID(uid) if uid else uuid.uuid4()
    u.email = "u@a.com"
    u.department_id = uuid.UUID(dept_id) if dept_id else None
    u.role = UserRole(role)
    return u


def _patch_scope(scope: VisibleScope):
    """Patch compute_visible_scope to return the given scope."""
    return patch(
        "app.shared.rbac.visible_scope.compute_visible_scope",
        AsyncMock(return_value=scope),
    )


def _patch_subordinate_query(rows):
    """Patch DB query for subordinate lookup."""
    mock_result = MagicMock()
    mock_result.fetchall = MagicMock(return_value=rows)
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_db)
    cm.__aexit__ = AsyncMock(return_value=None)
    return patch(
        "app.shared.rbac.visible_scope.AsyncSessionLocal",
        MagicMock(return_value=cm),
    )


# ============================================================================
# Task filter
# ============================================================================


@pytest.mark.asyncio
async def test_t1_empty_tasks_returns_empty():
    """T1: empty input → empty output (no DB query)."""
    user = _make_user(role="manager")
    out = await _filter_tasks_by_visible_scope([], user)
    assert out == []


@pytest.mark.asyncio
async def test_t2_admin_bypass_all_tasks_visible():
    """T2: admin → all tasks visible (no filter)."""
    user = _make_user(role="admin", dept_id=str(uuid.uuid4()))
    tasks = [_make_task(assignee_id=str(uuid.uuid4())) for _ in range(3)]
    with _patch_subordinate_query([]):
        out = await _filter_tasks_by_visible_scope(tasks, user)
    assert len(out) == 3


@pytest.mark.asyncio
async def test_t3_legacy_user_no_enforcement():
    """T3: user without dept AND no subordinates → bypass (soft-launch compat)."""
    user = _make_user(role="recruiter", dept_id=None)
    tasks = [_make_task(assignee_id=str(uuid.uuid4())) for _ in range(2)]
    # Recruiter skips DB lookup → scope has no subordinates → bypass
    out = await _filter_tasks_by_visible_scope(tasks, user)
    assert len(out) == 2


@pytest.mark.asyncio
async def test_t4_unassigned_task_visible_to_all():
    """T4: assigned_to_user_id=None (unassigned) → visible to all in tenant."""
    user_uid = str(uuid.uuid4())
    user = _make_user(role="recruiter", dept_id=str(uuid.uuid4()), uid=user_uid)
    tasks = [_make_task(assignee_id=None), _make_task(assignee_id=str(uuid.uuid4()))]
    # Recruiter has dept_id set → enforcement applies. But unassigned tasks still visible.
    out = await _filter_tasks_by_visible_scope(tasks, user)
    # task 1 (unassigned) visible; task 2 (assigned to random other) filtered
    assert len(out) == 1
    assert out[0].assigned_to_user_id is None


@pytest.mark.asyncio
async def test_t5_self_assigned_task_visible():
    """T5: task assigned to self → visible."""
    user_uid = str(uuid.uuid4())
    user = _make_user(role="recruiter", dept_id=str(uuid.uuid4()), uid=user_uid)
    tasks = [_make_task(assignee_id=user_uid)]
    out = await _filter_tasks_by_visible_scope(tasks, user)
    assert len(out) == 1


@pytest.mark.asyncio
async def test_t6_subordinate_assigned_task_visible_to_manager():
    """T6: manager sees task assigned to direct subordinate."""
    user_uid = str(uuid.uuid4())
    sub_uid = str(uuid.uuid4())
    user = _make_user(role="manager", dept_id=str(uuid.uuid4()), uid=user_uid)
    tasks = [_make_task(assignee_id=sub_uid)]
    # Mock subordinate lookup to return this subordinate
    sub_row = MagicMock()
    sub_row.uid = sub_uid
    sub_row.email = "sub@a.com"
    sub_row.dept = str(uuid.uuid4())
    with _patch_subordinate_query([sub_row]):
        out = await _filter_tasks_by_visible_scope(tasks, user)
    assert len(out) == 1


@pytest.mark.asyncio
async def test_t7_other_user_assigned_task_filtered_out():
    """T7: task assigned to non-subordinate other user → filtered."""
    user = _make_user(role="recruiter", dept_id=str(uuid.uuid4()), uid=str(uuid.uuid4()))
    tasks = [_make_task(assignee_id=str(uuid.uuid4()))]  # random other user
    out = await _filter_tasks_by_visible_scope(tasks, user)
    assert len(out) == 0


@pytest.mark.asyncio
async def test_t8_compute_scope_failure_non_blocking_returns_unfiltered():
    """T8: if compute_visible_scope raises, return tasks unfiltered (defensive)."""
    user = _make_user(role="manager", dept_id=str(uuid.uuid4()))
    tasks = [_make_task(assignee_id=str(uuid.uuid4())) for _ in range(2)]
    # Patch compute_visible_scope to raise
    with patch(
        "app.shared.rbac.visible_scope.compute_visible_scope",
        AsyncMock(side_effect=RuntimeError("DB down")),
    ):
        out = await _filter_tasks_by_visible_scope(tasks, user)
    # Must not raise; tasks returned unfiltered as soft fallback
    assert len(out) == 2
