"""Sprint 7 RBAC — mutation gate canonical contract.

Plan: ~/.claude/plans/jolly-roaming-moler.md.

Fail-secure write protection complementing Sprint 6 read filter.
Read filter (Sprint 6) = fail-open (hide gracefully).
Mutation gate (Sprint 7) = fail-secure (block on uncertainty).
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.shared.rbac.mutation_gate import assert_mutation_allowed
from app.shared.rbac.visible_scope import VisibleScope


def _make_user(role: str, dept_id: str | None = None, uid: str | None = None, email: str = "me@a.com"):
    from app.auth.models import UserRole
    u = MagicMock()
    u.id = uuid.UUID(uid) if uid else uuid.uuid4()
    u.email = email
    u.department_id = uuid.UUID(dept_id) if dept_id else None
    u.role = UserRole(role)
    return u


def _make_resource(**attrs):
    """Build a MagicMock resource with given attrs (and None for others)."""
    r = MagicMock()
    # Configure each attr explicitly so getattr returns the value (or None)
    r.configure_mock(**{
        "created_by": None,
        "recruiter_email": None,
        "department_id": None,
        "assigned_to_user_id": None,
        "interviewer_email": None,
        **attrs,
    })
    return r


def _patch_scope(scope: VisibleScope):
    return patch(
        "app.shared.rbac.mutation_gate.compute_visible_scope",
        AsyncMock(return_value=scope),
    )


@pytest.mark.asyncio
async def test_t1_none_resource_returns_silently():
    """T1: None resource → no gate (no-op)."""
    await assert_mutation_allowed(None, _make_user(role="recruiter"))


@pytest.mark.asyncio
async def test_t2_admin_bypass():
    """T2: admin role → always allowed (no exception)."""
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id=None,
                         is_admin=True, role="admin")
    res = _make_resource(department_id=str(uuid.uuid4()), created_by="other@a.com")
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="admin"))  # no raise


@pytest.mark.asyncio
async def test_t3_legacy_user_bypass():
    """T3: user with no dept_id AND no subordinates → bypass (soft-launch compat)."""
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id=None,
                         is_admin=False, role="recruiter")
    res = _make_resource(department_id=str(uuid.uuid4()), created_by="other@a.com")
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="recruiter"))


@pytest.mark.asyncio
async def test_t4_owner_self_allowed():
    """T4: resource created_by self → allowed (recruiter edits own work)."""
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id=str(uuid.uuid4()),
                         is_admin=False, role="recruiter")
    res = _make_resource(created_by="ME@a.com", department_id=str(uuid.uuid4()))  # diff dept!
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="recruiter"))  # owner trumps dept


@pytest.mark.asyncio
async def test_t5_recruiter_email_self_allowed():
    """T5: resource recruiter_email == self → allowed (Sprint 1 visibility extends to mutate)."""
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id=str(uuid.uuid4()),
                         is_admin=False, role="recruiter")
    res = _make_resource(recruiter_email="ME@a.com")
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="recruiter"))


@pytest.mark.asyncio
async def test_t6_dept_in_own_scope_allowed():
    """T6: resource dept matches own dept → allowed."""
    own_dept = str(uuid.uuid4())
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id=own_dept,
                         is_admin=False, role="recruiter")
    res = _make_resource(department_id=own_dept, created_by="other@a.com")
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="recruiter"))


@pytest.mark.asyncio
async def test_t7_dept_in_subordinate_scope_allowed_for_manager():
    """T7: resource dept matches subordinate dept → manager allowed."""
    sub_dept = str(uuid.uuid4())
    scope = VisibleScope(
        user_id="u", user_email="me@a.com", own_dept_id=str(uuid.uuid4()),
        is_admin=False, role="manager",
        subordinate_dept_ids=frozenset({sub_dept}),
        subordinate_user_emails=frozenset({"sub@a.com"}),
    )
    res = _make_resource(department_id=sub_dept, created_by="sub@a.com")
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="manager"))


@pytest.mark.asyncio
async def test_t8_subordinate_owner_allowed():
    """T8: resource owned by subordinate but in OTHER dept → manager allowed via owner."""
    scope = VisibleScope(
        user_id="u", user_email="me@a.com", own_dept_id=str(uuid.uuid4()),
        is_admin=False, role="manager",
        subordinate_user_emails=frozenset({"sub@a.com"}),
    )
    res = _make_resource(department_id=str(uuid.uuid4()), created_by="SUB@A.com")
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="manager"))


@pytest.mark.asyncio
async def test_t9_out_of_scope_raises_403():
    """T9: resource in other dept, not owned by self/subordinate → 403."""
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id=str(uuid.uuid4()),
                         is_admin=False, role="recruiter")
    res = _make_resource(department_id=str(uuid.uuid4()), created_by="stranger@a.com")
    with _patch_scope(scope):
        with pytest.raises(HTTPException) as exc:
            await assert_mutation_allowed(res, _make_user(role="recruiter"))
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_t10_assignee_self_allowed_for_task():
    """T10: task assigned_to_user_id == self → allowed."""
    user_uid = str(uuid.uuid4())
    scope = VisibleScope(user_id=user_uid, user_email="me@a.com",
                         own_dept_id=str(uuid.uuid4()),
                         is_admin=False, role="recruiter")
    res = _make_resource(assigned_to_user_id=user_uid)
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="recruiter"))


@pytest.mark.asyncio
async def test_t11_assignee_subordinate_allowed_for_manager():
    """T11: task assigned to subordinate → manager allowed."""
    sub_uid = str(uuid.uuid4())
    scope = VisibleScope(
        user_id=str(uuid.uuid4()), user_email="me@a.com",
        own_dept_id=str(uuid.uuid4()),
        is_admin=False, role="manager",
        subordinate_user_ids=frozenset({sub_uid}),
    )
    res = _make_resource(assigned_to_user_id=sub_uid)
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="manager"))


@pytest.mark.asyncio
async def test_t12_interviewer_self_allowed():
    """T12: interview interviewer_email == self → allowed."""
    scope = VisibleScope(user_id="u", user_email="me@a.com",
                         own_dept_id=str(uuid.uuid4()),
                         is_admin=False, role="recruiter")
    res = _make_resource(interviewer_email="me@a.com")
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="recruiter"))


@pytest.mark.asyncio
async def test_t13_scope_failure_raises_503_fail_secure():
    """T13: compute_visible_scope raises → 503 (fail-secure, NOT silent bypass)."""
    res = _make_resource(department_id=str(uuid.uuid4()))
    with patch(
        "app.shared.rbac.mutation_gate.compute_visible_scope",
        AsyncMock(side_effect=RuntimeError("DB down")),
    ):
        with pytest.raises(HTTPException) as exc:
            await assert_mutation_allowed(res, _make_user(role="recruiter"))
        assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_t14_dict_resource_works():
    """T14: works with dict resources (not only ORM)."""
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id="d1",
                         is_admin=False, role="recruiter")
    res = {"department_id": "d1", "created_by": "x@a.com"}
    with _patch_scope(scope):
        await assert_mutation_allowed(res, _make_user(role="recruiter"))


@pytest.mark.asyncio
async def test_t15_403_includes_resource_label():
    """T15: 403 detail message uses resource_label for debuggability."""
    scope = VisibleScope(user_id="u", user_email="me@a.com", own_dept_id=str(uuid.uuid4()),
                         is_admin=False, role="recruiter")
    res = _make_resource(department_id=str(uuid.uuid4()), created_by="stranger@a.com")
    with _patch_scope(scope):
        with pytest.raises(HTTPException) as exc:
            await assert_mutation_allowed(res, _make_user(role="recruiter"),
                                          resource_label="vaga 'Tech Lead'")
        assert "vaga 'Tech Lead'" in exc.value.detail
