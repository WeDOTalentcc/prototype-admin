"""TDD red-phase — Phase B completion: /reject endpoint + expiry sweep.

Closes the workflow loop:
- /approve happy path: shipped (3d3e1c31a + d452a6533)
- /reject: admin denies the request with reason
- Expiry sweep: pending requests older than expires_at auto-cancel

Mirrors the /approve guards (admin-only, self-rejection blocked, status
must be pending). Uses canonical ApprovalStatus enum + ApprovalsRepository
+ canonical email sender (P0-B fix).
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _make_user(is_admin: bool = False, user_id: str = "user-42",
               company_id: str = "00000000-0000-0000-0000-0000000000a1",
               email: str = "rec@example.com"):
    from app.auth.models import UserRole
    user = MagicMock()
    user.id = user_id
    user.company_id = company_id
    user.email = email
    user.first_name = "Recruiter"
    user.role = UserRole.admin if is_admin else UserRole.recruiter
    return user


def _make_approval(*, status: str = "pending",
                   requester_id: str = "user-42",
                   expires_at=None):
    approval = MagicMock()
    approval.id = "approval-id-1"
    approval.requester_id = requester_id
    approval.status = status
    approval.target_data = {
        "flag_key": "learning_loops.bigfive_department_history",
        "requested_value": True,
        "rollout_percentage": 100,
        "category": "learning_loops",
        "company_id_enforced": "00000000-0000-0000-0000-0000000000a1",
    }
    approval.target_id = None
    approval.target_name = "learning_loops.bigfive_department_history"
    approval.company_id = "00000000-0000-0000-0000-0000000000a1"
    approval.requester_email = "user-42@example.com"
    approval.expires_at = expires_at
    approval.resolved_at = None
    approval.resolved_by = None
    approval.rejection_reason = None
    return approval


# ── /reject endpoint ────────────────────────────────────────────────────────


def test_reject_endpoint_exists_and_is_callable():
    """The reject endpoint function must exist with the canonical name."""
    from app.api.v1.lia_assistant_flags import reject_feature_flag_toggle
    assert callable(reject_feature_flag_toggle)


def test_reject_flips_status_and_does_not_call_set_flag():
    """Admin rejects: approval.status -> rejected; ff_svc.set_flag NOT
    called; rejection_reason persisted; audit log fires with
    workflow_state=rejected."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRejectRequest,
        reject_feature_flag_toggle,
    )

    approval = _make_approval()
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=approval)

    mock_ff_svc = MagicMock()
    mock_ff_svc.set_flag = AsyncMock()  # MUST NOT be called

    body = FeatureFlagToggleRejectRequest(
        rejection_reason="bias risk too high right now",
    )

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ), patch(
            "app.api.v1.lia_assistant_flags._send_approval_result_email",
            new=AsyncMock(),
        ), patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            return await reject_feature_flag_toggle(
                request_id="approval-id-1",
                request=body,
                db=AsyncMock(),
                current_user=_make_user(is_admin=True, user_id="admin-99"),
                ff_svc=mock_ff_svc,
            )

    asyncio.run(_run())

    assert not mock_ff_svc.set_flag.called, (
        "ff_svc.set_flag was invoked during /reject — rejection MUST "
        "NOT trigger the toggle. Block before any set_flag call."
    )
    assert approval.status == "rejected", (
        f"approval.status={approval.status!r}, expected 'rejected' after "
        f"reject endpoint. Update status before returning."
    )
    assert approval.rejection_reason == "bias risk too high right now", (
        "rejection_reason from body not persisted on approval row. "
        "Forensic trail requires the reason stay with the row."
    )


def test_reject_blocks_self_rejection():
    """Admin cannot reject their own request — second-actor invariant
    applies symmetrically to approve and reject."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRejectRequest,
        reject_feature_flag_toggle,
    )

    approval = _make_approval(requester_id="admin-99")  # same as approver
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=approval)

    body = FeatureFlagToggleRejectRequest(rejection_reason="x")

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ):
            await reject_feature_flag_toggle(
                request_id="approval-id-1",
                request=body,
                db=AsyncMock(),
                current_user=_make_user(is_admin=True, user_id="admin-99"),
                ff_svc=MagicMock(),
            )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())
    assert exc_info.value.status_code == 403, (
        f"Self-rejection should return 403, got {exc_info.value.status_code}. "
        f"Mirror the self-approval guard in approve_feature_flag_toggle."
    )


def test_reject_blocks_non_admin():
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRejectRequest,
        reject_feature_flag_toggle,
    )

    body = FeatureFlagToggleRejectRequest(rejection_reason="x")

    async def _run():
        await reject_feature_flag_toggle(
            request_id="approval-id-1",
            request=body,
            db=AsyncMock(),
            current_user=_make_user(is_admin=False),
            ff_svc=MagicMock(),
        )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())
    assert exc_info.value.status_code == 403


def test_reject_409_when_already_resolved():
    """Cannot reject an already-approved or already-rejected request."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRejectRequest,
        reject_feature_flag_toggle,
    )

    approval = _make_approval(status="approved")
    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=approval)

    body = FeatureFlagToggleRejectRequest(rejection_reason="x")

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ):
            await reject_feature_flag_toggle(
                request_id="approval-id-1",
                request=body,
                db=AsyncMock(),
                current_user=_make_user(is_admin=True, user_id="admin-99"),
                ff_svc=MagicMock(),
            )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())
    assert exc_info.value.status_code == 409


# ── Expiry sweep ────────────────────────────────────────────────────────────


def test_expiry_sweep_function_exists():
    from app.api.v1.lia_assistant_flags import sweep_expired_approvals
    assert callable(sweep_expired_approvals)


def test_expiry_sweep_cancels_only_pending_past_expires_at():
    """sweep_expired_approvals: iterate pending requests, mark as
    cancelled when expires_at < now. Returns count of cancelled rows."""
    from app.api.v1.lia_assistant_flags import sweep_expired_approvals

    now = datetime.utcnow()
    expired = _make_approval(expires_at=now - timedelta(days=1))
    expired.id = "expired-1"
    fresh = _make_approval(expires_at=now + timedelta(days=3))
    fresh.id = "fresh-1"
    no_expiry = _make_approval(expires_at=None)
    no_expiry.id = "no-exp-1"

    mock_repo = MagicMock()
    mock_repo.list_pending_by_company = AsyncMock(
        return_value=[expired, fresh, no_expiry],
    )

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ), patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            return await sweep_expired_approvals(
                db=AsyncMock(),
                company_id="00000000-0000-0000-0000-0000000000a1",
            )

    cancelled_count = asyncio.run(_run())

    assert cancelled_count == 1, (
        f"sweep returned {cancelled_count}, expected exactly 1 (only the "
        f"expired row). Fresh and no-expiry rows must be left alone."
    )
    assert expired.status == "cancelled"
    assert fresh.status == "pending", "fresh row must NOT be cancelled"
    assert no_expiry.status == "pending", "no-expiry row must NOT be cancelled"


def test_expiry_sweep_filters_by_request_type_feature_flag_toggle():
    """sweep MUST only touch feature_flag_toggle requests — vacancy/hire
    approvals belong to other workflows with their own expiry policy."""
    import inspect
    from app.api.v1 import lia_assistant_flags

    src = inspect.getsource(lia_assistant_flags.sweep_expired_approvals)
    assert "feature_flag_toggle" in src or "FEATURE_FLAG_TOGGLE" in src, (
        "sweep_expired_approvals must filter list_pending_by_company by "
        "request_type='feature_flag_toggle' so other approval workflows "
        "are not affected."
    )
