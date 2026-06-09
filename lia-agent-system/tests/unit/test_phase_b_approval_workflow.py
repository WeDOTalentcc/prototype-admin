"""TDD red-phase — Phase B: feature flag toggle approval workflow.

Replaces the temporary 'non-admin = 403' HITL gate (Sprint B P1-9) with
a proper second-actor request → approve workflow. Backend ships now;
frontend wires later.

Decisions (Paulo 2026-05-10):
- B1 expiration: 7 days hardcoded
- B2 notification: email-only via EmailService
- B3 self-approval: hard block
- B4 approver: broadcast to all admins (first-to-act wins)
- B5 retention: forever (LGPD/ISO 27001 forensic trail)

Reuses canonical ApprovalRequest table (lia_models/approval.py); extends
ApprovalType enum with FEATURE_FLAG_TOGGLE. Fixes pre-existing bug in
ApprovalsRepository.list_pending_by_company (referenced undefined
variable 'pending' instead of the canonical 'pending' string/enum value).
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


# ── 1. Repo bug fix — list_pending_by_company doesn't crash ─────────────────


def test_list_pending_by_company_uses_canonical_pending_string():
    """ApprovalsRepository.list_pending_by_company had a bug: SELECT
    referenced undefined variable `pending` instead of the canonical
    'pending' string (or ApprovalStatus.PENDING.value). Calling it
    crashed with NameError. Sentinel: source must reference 'pending'
    string or the enum, never a bare identifier."""
    import inspect
    from app.repositories import approvals_repository

    source = inspect.getsource(
        approvals_repository.ApprovalsRepository.list_pending_by_company
    )
    # Canonical: should match either ApprovalStatus.PENDING or 'pending'
    has_canonical = (
        'ApprovalStatus.PENDING' in source
        or "'pending'" in source
        or '"pending"' in source
    )
    assert has_canonical, (
        "list_pending_by_company doesn't reference a canonical pending "
        "value. Use either ApprovalStatus.PENDING.value (preferred) or "
        "the literal string 'pending'. The bare 'pending' identifier "
        "raises NameError."
    )
    # Negative: must NOT contain 'status == pending\\n' as identifier
    assert "status == pending\n" not in source and "status == pending\r" not in source, (
        "list_pending_by_company still references the undefined 'pending' "
        "variable. Replace with ApprovalStatus.PENDING.value."
    )


# ── 2. ApprovalType enum has FEATURE_FLAG_TOGGLE ────────────────────────────


def test_approval_type_includes_feature_flag_toggle():
    """The canonical ApprovalType enum must have FEATURE_FLAG_TOGGLE so
    feature flag toggle requests can be persisted alongside vacancy/hire
    approvals using the same table + repo + email pipeline."""
    from app.models.approval import ApprovalType

    values = {member.value for member in ApprovalType}
    assert "feature_flag_toggle" in values, (
        f"ApprovalType missing FEATURE_FLAG_TOGGLE. Got values={values}. "
        f"Add: FEATURE_FLAG_TOGGLE = 'feature_flag_toggle' in "
        f"libs/models/lia_models/approval.py."
    )


# ── 3. POST /request-toggle creates ApprovalRequest ─────────────────────────


def _make_user(is_admin: bool = False, user_id: str = "user-42",
               company_id: str = "00000000-0000-0000-0000-0000000000a1",
               email: str = "rec@example.com"):
    from app.auth.models import UserRole
    user = MagicMock()
    user.id = user_id
    user.company_id = company_id
    user.email = email
    user.first_name = "Recruiter"
    user.last_name = "Test"
    user.role = UserRole.admin if is_admin else UserRole.recruiter
    return user


def test_request_toggle_endpoint_creates_approval_request_with_flag_payload():
    """POST /lia/feature-flags/request-toggle accepts a flag_key +
    requested_value and persists an ApprovalRequest with target_type=
    feature_flag, target_id=flag_key, target_data containing the request
    payload, and request_type=FEATURE_FLAG_TOGGLE."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRequest,
        request_feature_flag_toggle,
    )

    captured_approvals: list = []

    async def _mock_add_and_flush(approval):
        captured_approvals.append(approval)
        approval.id = "approval-id-1"
        return approval

    mock_repo = MagicMock()
    mock_repo.add_and_flush = AsyncMock(side_effect=_mock_add_and_flush)
    mock_repo.find_pending_duplicate = AsyncMock(return_value=None)

    body = FeatureFlagToggleRequest(
        flag_key="learning_loops.bigfive_department_history",
        requested_value=True,
        rollout_percentage=100,
        category="learning_loops",
        justification="Habilitar loop pro pilot",
    )

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ), patch(
            "app.api.v1.lia_assistant_flags._send_approval_request_email",
            new=AsyncMock(),
        ):
            return await request_feature_flag_toggle(
                request=body,
                db=AsyncMock(),
                current_user=_make_user(is_admin=False),
            )

    response = asyncio.run(_run())

    assert mock_repo.add_and_flush.called, (
        "request_feature_flag_toggle did not call add_and_flush. Persist "
        "the ApprovalRequest using the canonical ApprovalsRepository."
    )
    approval = captured_approvals[0]
    assert approval.request_type == "feature_flag_toggle"
    assert approval.target_type == "feature_flag"
    assert approval.target_data.get("flag_key") == "learning_loops.bigfive_department_history"
    assert approval.target_data.get("requested_value") is True
    assert approval.status == "pending"


def test_request_toggle_rejects_non_sensitive_flag():
    """Non-sensitive flags don't need the approval workflow — they go
    through direct /set. The request endpoint must reject them with 400
    so users don't pile up unnecessary approval requests."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRequest,
        request_feature_flag_toggle,
    )

    body = FeatureFlagToggleRequest(
        flag_key="learning_loops.jd_similar_suggestion",  # NOT sensitive
        requested_value=True,
        rollout_percentage=100,
    )

    async def _run():
        await request_feature_flag_toggle(
            request=body,
            db=AsyncMock(),
            current_user=_make_user(is_admin=False),
        )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())
    assert exc_info.value.status_code == 400, (
        f"Expected 400 for non-sensitive flag in request-toggle endpoint, "
        f"got {exc_info.value.status_code}. Sensitive-only check must "
        f"reject with a message directing user to /feature-flags/set."
    )


# ── 4. POST /approve/{id} — admin approves, set_flag fires ──────────────────


def test_approve_request_invokes_set_flag_with_admin_context():
    """Admin (different from requester) approves: set_feature_flag is
    called with the requested value, ApprovalRequest.status flips to
    approved."""
    from app.api.v1.lia_assistant_flags import approve_feature_flag_toggle

    approval = MagicMock()
    approval.id = "approval-id-1"
    approval.requester_id = "user-42"  # different from approver
    approval.status = "pending"
    approval.target_data = {
        "flag_key": "learning_loops.bigfive_department_history",
        "requested_value": True,
        "rollout_percentage": 100,
        "category": "learning_loops",
        "company_id_enforced": "00000000-0000-0000-0000-0000000000a1",
    }
    approval.target_id = "learning_loops.bigfive_department_history"
    approval.company_id = "00000000-0000-0000-0000-0000000000a1"
    approval.requester_email = "user-42@example.com"
    approval.expires_at = None  # Pydantic response expects None or datetime
    approval.resolved_at = None
    approval.resolved_by = None

    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=approval)

    mock_ff_svc = MagicMock()
    mock_ff_svc.set_flag = AsyncMock(return_value={
        "success": True, "flag_id": "ff-1",
        "flag_key": "learning_loops.bigfive_department_history",
        "is_enabled": True, "company_id": "00000000-0000-0000-0000-0000000000a1",
    })

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
            return await approve_feature_flag_toggle(
                request_id="approval-id-1",
                db=AsyncMock(),
                current_user=_make_user(
                    is_admin=True, user_id="admin-99",
                    email="admin@example.com",
                ),
                ff_svc=mock_ff_svc,
            )

    asyncio.run(_run())

    assert mock_ff_svc.set_flag.called, (
        "approve_feature_flag_toggle did not invoke ff_svc.set_flag after "
        "approval. The approve endpoint must complete the toggle by "
        "invoking the canonical set_feature_flag write path."
    )
    kwargs = mock_ff_svc.set_flag.call_args.kwargs
    assert kwargs.get("flag_key") == "learning_loops.bigfive_department_history"
    assert kwargs.get("is_enabled") is True
    assert approval.status == "approved", (
        f"approval.status={approval.status!r}, expected 'approved'. "
        f"Update status BEFORE returning the response."
    )


def test_self_approval_blocked():
    """Admin cannot approve their own request — second-actor invariant."""
    from app.api.v1.lia_assistant_flags import approve_feature_flag_toggle

    approval = MagicMock()
    approval.id = "approval-id-1"
    approval.requester_id = "admin-99"  # same id as the approver below
    approval.status = "pending"
    approval.target_data = {
        "flag_key": "learning_loops.bigfive_department_history",
        "requested_value": True,
    }

    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=approval)

    mock_ff_svc = MagicMock()
    mock_ff_svc.set_flag = AsyncMock()

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ):
            await approve_feature_flag_toggle(
                request_id="approval-id-1",
                db=AsyncMock(),
                current_user=_make_user(is_admin=True, user_id="admin-99"),
                ff_svc=mock_ff_svc,
            )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())
    assert exc_info.value.status_code == 403, (
        f"Self-approval should return 403, got {exc_info.value.status_code}. "
        f"Block when current_user.id == approval.requester_id."
    )
    assert not mock_ff_svc.set_flag.called, (
        "set_flag was called despite self-approval rejection — must short-"
        "circuit BEFORE invoking the toggle."
    )


def test_non_admin_cannot_approve():
    """Non-admin users cannot approve requests — 403."""
    from app.api.v1.lia_assistant_flags import approve_feature_flag_toggle

    approval = MagicMock()
    approval.id = "approval-id-1"
    approval.requester_id = "user-99"
    approval.status = "pending"

    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=approval)

    mock_ff_svc = MagicMock()

    async def _run():
        await approve_feature_flag_toggle(
            request_id="approval-id-1",
            db=AsyncMock(),
            current_user=_make_user(is_admin=False, user_id="user-42"),
            ff_svc=mock_ff_svc,
        )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())
    assert exc_info.value.status_code == 403


# ── 5. P1-9 fallback path still works (parallel sentinel) ───────────────────


def test_p1_9_403_fallback_remains_for_direct_set_attempts():
    """The pre-existing /feature-flags/set 403 gate (P1-9) MUST remain
    intact: a non-admin trying the direct set path is still rejected.
    The new request-toggle endpoint is OPT-IN, not a replacement of the
    immediate gate."""
    import inspect
    from app.api.v1 import lia_assistant_flags

    source = inspect.getsource(lia_assistant_flags)
    assert "_enforce_hitl_gate" in source, (
        "_enforce_hitl_gate disappeared from lia_assistant_flags. The "
        "P1-9 fallback rejection MUST remain — request-toggle is opt-in. "
        "Restore the gate in set_feature_flag."
    )
