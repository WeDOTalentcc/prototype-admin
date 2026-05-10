"""TDD red-phase — P0 fixes for Phase B approval workflow (post-audit).

3 P0 bugs identified by post-implementation audit (canonical-fix +
feature-impact + governance agents converged):

P0-A: ApprovalRequest.approver_name and approver_email are nullable=False
      (lia_models/approval.py:57-58) but request_feature_flag_toggle never
      sets them (B4 broadcast decision). Every real call -> IntegrityError
      -> HTTP 500. Tests mock the repo so the failure is hidden (false-green).

P0-A`: ApprovalRequest.target_id is UUID(as_uuid=True), but the endpoint
       sets target_id=request.flag_key (string like
       'learning_loops.bigfive_department_history'). asyncpg rejects
       non-UUID strings even with nullable=True. Same false-green.

P0-B: _send_approval_request_email and _send_approval_result_email use
      getattr(EmailService(), 'send_approval_request_email', None). Those
      functions are MODULE-LEVEL in app/api/v1/approvals.py:432/478, NOT
      methods of EmailService. getattr returns None -> silent skip ->
      Decision B2 (email-only notification) is dead code.

Tests assert behavioral contracts that the audit agents would have caught
if integration tests existed. We mock the canonical email module-level
functions and the schema-bound ApprovalRequest write surface.
"""
from __future__ import annotations

import asyncio
import uuid
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
    user.last_name = "Test"
    user.role = UserRole.admin if is_admin else UserRole.recruiter
    return user


# ── P0-A — approver_name/approver_email never empty ─────────────────────────


def test_request_toggle_persists_approver_name_non_empty():
    """ApprovalRequest.approver_name is nullable=False — endpoint MUST
    set a non-empty value. Broadcast workflows (Paulo decision B4) need
    a sentinel like 'Pending DPO Approval', not None or ''."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRequest,
        request_feature_flag_toggle,
    )

    captured: list = []

    async def _capture(approval):
        captured.append(approval)
        approval.id = uuid.uuid4()
        return approval

    mock_repo = MagicMock()
    mock_repo.add_and_flush = AsyncMock(side_effect=_capture)
    mock_repo.find_pending_duplicate = AsyncMock(return_value=None)

    body = FeatureFlagToggleRequest(
        flag_key="learning_loops.bigfive_department_history",
        requested_value=True,
    )

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ), patch(
            "app.api.v1.lia_assistant_flags._send_approval_request_email",
            new=AsyncMock(),
        ):
            await request_feature_flag_toggle(
                request=body, db=AsyncMock(),
                current_user=_make_user(is_admin=False),
            )

    asyncio.run(_run())

    approval = captured[0]
    assert approval.approver_name and approval.approver_name.strip(), (
        f"approver_name must be a non-empty string (column is "
        f"nullable=False). Got {approval.approver_name!r}. Use a "
        f"broadcast sentinel like 'Pending DPO Approval' until B4 "
        f"DPO designation lands."
    )
    # Empty string is technically nullable=False compliant in PG, but
    # makes the audit log impossible to read. Refuse it.
    assert approval.approver_name != "", (
        "Empty string for approver_name is technically valid but breaks "
        "downstream UI/email rendering. Use a sentinel like "
        "'Pending DPO Approval'."
    )


def test_request_toggle_persists_approver_email_non_null():
    """Same as approver_name: column is nullable=False. Broadcast flow
    needs SOME placeholder value (empty string is the minimum that PG
    will accept). Sentinel preferred."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRequest,
        request_feature_flag_toggle,
    )

    captured: list = []

    async def _capture(approval):
        captured.append(approval)
        approval.id = uuid.uuid4()
        return approval

    mock_repo = MagicMock()
    mock_repo.add_and_flush = AsyncMock(side_effect=_capture)
    mock_repo.find_pending_duplicate = AsyncMock(return_value=None)

    body = FeatureFlagToggleRequest(
        flag_key="learning_loops.bigfive_department_history",
        requested_value=True,
    )

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ), patch(
            "app.api.v1.lia_assistant_flags._send_approval_request_email",
            new=AsyncMock(),
        ):
            await request_feature_flag_toggle(
                request=body, db=AsyncMock(),
                current_user=_make_user(is_admin=False),
            )

    asyncio.run(_run())

    approval = captured[0]
    assert approval.approver_email is not None, (
        "approver_email cannot be None — column is nullable=False. Set "
        "to '' (empty placeholder) at minimum, or a broadcast sentinel."
    )


# ── P0-A` — target_id is UUID column ────────────────────────────────────────


def test_request_toggle_does_not_pass_string_to_target_id():
    """ApprovalRequest.target_id is UUID(as_uuid=True). The endpoint
    must NOT pass a string flag_key like
    'learning_loops.bigfive_department_history' here — asyncpg rejects.
    flag_key belongs in target_data, not target_id."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRequest,
        request_feature_flag_toggle,
    )

    captured: list = []

    async def _capture(approval):
        captured.append(approval)
        approval.id = uuid.uuid4()
        return approval

    mock_repo = MagicMock()
    mock_repo.add_and_flush = AsyncMock(side_effect=_capture)
    mock_repo.find_pending_duplicate = AsyncMock(return_value=None)

    body = FeatureFlagToggleRequest(
        flag_key="learning_loops.bigfive_department_history",
        requested_value=True,
    )

    async def _run():
        with patch(
            "app.api.v1.lia_assistant_flags._build_approvals_repo",
            return_value=mock_repo,
        ), patch(
            "app.api.v1.lia_assistant_flags._send_approval_request_email",
            new=AsyncMock(),
        ):
            await request_feature_flag_toggle(
                request=body, db=AsyncMock(),
                current_user=_make_user(is_admin=False),
            )

    asyncio.run(_run())

    approval = captured[0]
    target = approval.target_id
    if target is not None:
        # If set, MUST be a UUID-castable value (not a free-text flag_key)
        try:
            uuid.UUID(str(target))
        except (TypeError, ValueError):
            pytest.fail(
                f"target_id={target!r} is not a UUID. Move flag_key into "
                f"target_data (already there) and set target_id=None — "
                f"the column is UUID(as_uuid=True) and asyncpg rejects "
                f"non-UUID strings."
            )
    # flag_key MUST still appear in target_data
    assert (approval.target_data or {}).get("flag_key") == \
        "learning_loops.bigfive_department_history", (
        "flag_key must remain in target_data so /pending-approvals and "
        "/approve can read it."
    )


# ── P0-B — Email module-level functions wired correctly ─────────────────────


def test_request_email_helper_calls_canonical_module_function():
    """_send_approval_request_email in lia_assistant_flags MUST delegate
    to the canonical app.api.v1.approvals.send_approval_request_email
    module-level function — which DOES exist. The previous getattr
    on EmailService() returned None and silently skipped notifications."""
    import importlib
    import app.api.v1.lia_assistant_flags as flags_mod

    # The endpoint helper must reference the canonical sender by name,
    # either via direct import or via inline import of the approvals
    # module. Source-inspection sentinel:
    import inspect
    src = inspect.getsource(flags_mod._send_approval_request_email)
    assert (
        "from app.api.v1.approvals import send_approval_request_email" in src
        or "approvals.send_approval_request_email" in src
        or "import send_approval_request_email" in src
    ), (
        "_send_approval_request_email no longer references the canonical "
        "sender at app.api.v1.approvals.send_approval_request_email. The "
        "previous getattr(EmailService(), 'send_approval_request_email') "
        "returned None and silently skipped notifications. Restore the "
        "delegation via import + call."
    )


def test_result_email_helper_calls_canonical_module_function():
    """Same expectation for the result email."""
    import inspect
    import app.api.v1.lia_assistant_flags as flags_mod

    src = inspect.getsource(flags_mod._send_approval_result_email)
    assert (
        "from app.api.v1.approvals import send_approval_result_email" in src
        or "approvals.send_approval_result_email" in src
        or "import send_approval_result_email" in src
    ), (
        "_send_approval_result_email no longer references the canonical "
        "sender at app.api.v1.approvals.send_approval_result_email. "
        "Notifications would silently no-op. Restore the delegation."
    )
