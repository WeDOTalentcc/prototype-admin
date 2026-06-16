"""
Sprint 4 RBAC — SCIM Directory Sync canonical contract.

Plan canonical: ~/.claude/plans/jolly-roaming-moler.md.

Pin behavior of WorkOS SCIM dsync.group.user_added/removed and audit log:
  T1. Role recompute picks highest-priv group mapping (admin > manager > recruiter > viewer)
  T2. User without mapped groups → defaults to viewer
  T3. Removing highest-priv group downgrades role
  T4. Same role → no update (idempotent)
  T5. log_user_provisioning persists to SOXAuditLog with 7-year retention
  T6. log_user_provisioning is non-blocking on exception (LGPD Art. 37 V)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.workos import _recompute_user_role_from_groups, _ROLE_HIERARCHY
from app.shared.compliance.audit_service import AuditService


# ============================================================================
# A. Role hierarchy + recompute logic
# ============================================================================


def _make_group(group_id, name="grp"):
    g = MagicMock()
    g.id = group_id if isinstance(group_id, uuid.UUID) else uuid.uuid4()
    g.name = name
    return g


def _make_mapping(role: str):
    m = MagicMock()
    m.role = role
    return m


def _make_user(role: str = "viewer"):
    from app.auth.models import UserRole
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "user@acme.com"
    u.role = UserRole(role)
    return u


@pytest.mark.asyncio
async def test_t1_recompute_picks_highest_privileged_group_mapping():
    """T1. User in groups [recruiter, admin, viewer] → role becomes admin."""
    user = _make_user(role="viewer")
    g1, g2, g3 = _make_group(uuid.uuid4(), "Recruiters"), _make_group(uuid.uuid4(), "Admins"), _make_group(uuid.uuid4(), "Viewers")

    user_repo = AsyncMock()
    workos_repo = AsyncMock()
    workos_repo.list_groups_for_user = AsyncMock(return_value=[g1, g2, g3])

    async def mock_mapping(company_id, gid):
        return {g1.id: _make_mapping("recruiter"), g2.id: _make_mapping("admin"), g3.id: _make_mapping("viewer")}[gid]
    workos_repo.get_role_mapping = mock_mapping

    new_role, old_role = await _recompute_user_role_from_groups(user, "co-1", user_repo, workos_repo)
    assert new_role == "admin"
    assert old_role == "viewer"
    user_repo.update_by_instance.assert_awaited_once()


@pytest.mark.asyncio
async def test_t2_user_without_mappings_defaults_to_viewer():
    """T2. User in groups but none have mapping → defaults to viewer."""
    user = _make_user(role="admin")  # was admin, will downgrade
    g1 = _make_group(uuid.uuid4(), "Unknown")

    user_repo = AsyncMock()
    workos_repo = AsyncMock()
    workos_repo.list_groups_for_user = AsyncMock(return_value=[g1])
    workos_repo.get_role_mapping = AsyncMock(return_value=None)

    new_role, old_role = await _recompute_user_role_from_groups(user, "co-1", user_repo, workos_repo)
    assert new_role == "viewer"
    assert old_role == "admin"


@pytest.mark.asyncio
async def test_t3_removing_highest_priv_group_downgrades_role():
    """T3. After group removal user has [recruiter] mapping only → role becomes recruiter."""
    user = _make_user(role="admin")  # was admin
    g1 = _make_group(uuid.uuid4(), "Recruiters")

    user_repo = AsyncMock()
    workos_repo = AsyncMock()
    workos_repo.list_groups_for_user = AsyncMock(return_value=[g1])
    workos_repo.get_role_mapping = AsyncMock(return_value=_make_mapping("recruiter"))

    new_role, old_role = await _recompute_user_role_from_groups(user, "co-1", user_repo, workos_repo)
    assert new_role == "recruiter"
    assert old_role == "admin"


@pytest.mark.asyncio
async def test_t4_idempotent_when_no_change():
    """T4. Recompute when role already correct → returns old_role=None (no DB write)."""
    user = _make_user(role="manager")
    g1 = _make_group(uuid.uuid4(), "Managers")

    user_repo = AsyncMock()
    workos_repo = AsyncMock()
    workos_repo.list_groups_for_user = AsyncMock(return_value=[g1])
    workos_repo.get_role_mapping = AsyncMock(return_value=_make_mapping("manager"))

    new_role, old_role = await _recompute_user_role_from_groups(user, "co-1", user_repo, workos_repo)
    assert new_role == "manager"
    assert old_role is None  # signals "no change"
    user_repo.update_by_instance.assert_not_called()


def test_role_hierarchy_canonical_order():
    """Lock canonical role hierarchy. Adding/removing roles requires intentional change."""
    assert _ROLE_HIERARCHY["admin"] > _ROLE_HIERARCHY["manager"]
    assert _ROLE_HIERARCHY["manager"] > _ROLE_HIERARCHY["recruiter"]
    assert _ROLE_HIERARCHY["recruiter"] > _ROLE_HIERARCHY["viewer"]
    # wedotalent_admin is NOT in hierarchy (staff role, never assigned via SCIM)
    assert "wedotalent_admin" not in _ROLE_HIERARCHY


# ============================================================================
# B. log_user_provisioning (SOXAuditLog 7-year retention)
# ============================================================================


@pytest.mark.asyncio
async def test_t5_log_user_provisioning_persists_to_sox_audit_log():
    """T5. log_user_provisioning writes SOXAuditLog with USER_MANAGEMENT category + 7-year retention."""
    captured_logs = []

    class FakeSession:
        def add(self, obj):
            captured_logs.append(obj)
        async def commit(self):
            pass

    fake_session = FakeSession()

    class FakeCM:
        async def __aenter__(self):
            return fake_session
        async def __aexit__(self, *args):
            pass

    with patch("app.shared.compliance.audit_service.AsyncSessionLocal", MagicMock(return_value=FakeCM())):
        with patch("app.shared.compliance.audit_service._bind_tenant", AsyncMock()):
            svc = AuditService()
            await svc.log_user_provisioning(
                company_id="co-1",
                actor="scim_webhook",
                action="provision_user",
                target_user_id=str(uuid.uuid4()),
                target_user_email="new@acme.com",
                details={"workos_id": "user_xyz", "initial_role": "viewer"},
            )

    assert len(captured_logs) == 1
    log = captured_logs[0]
    assert log.company_id == "co-1"
    assert log.action == "provision_user"
    assert log.action_category == "user_management"
    assert log.resource_type == "user"
    assert log.retention_years == 7
    # retention_until should be ~7 years out
    delta = log.retention_until - datetime.utcnow()
    assert delta.days >= 365 * 7 - 1
    # actor + email merged into details
    assert log.details["actor"] == "scim_webhook"
    assert log.details["target_user_email"] == "new@acme.com"
    assert log.details["workos_id"] == "user_xyz"


@pytest.mark.asyncio
async def test_t6_log_user_provisioning_is_non_blocking_on_db_failure():
    """T6. DB exception is swallowed (LGPD Art. 37 V: audit failure cannot block request)."""
    class BrokenCM:
        async def __aenter__(self):
            raise RuntimeError("DB down")
        async def __aexit__(self, *args):
            pass

    with patch("app.shared.compliance.audit_service.AsyncSessionLocal", MagicMock(return_value=BrokenCM())):
        svc = AuditService()
        # Should NOT raise
        await svc.log_user_provisioning(
            company_id="co-1",
            actor="scim_webhook",
            action="provision_user",
            target_user_id=str(uuid.uuid4()),
            target_user_email="x@acme.com",
        )
    # If we got here, non-blocking contract is preserved
