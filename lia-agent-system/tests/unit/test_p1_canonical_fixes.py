"""TDD red-phase — P1 canonical fixes batch.

3 P1 items from post-tickets audit:

P1-1 Idempotency in request-toggle: 409 if PENDING request already
     exists for (company_id, flag_key, requester_id). Prevents recruiter
     double-submit spam and audit log bloat.

P1-2 ALLOWED_TRAITS single source of truth: frozenset currently defined
     in bigfive_department_profile_repository.py AND duplicated as a
     local set literal in score_calculator.py. Moving to
     app/shared/ocean_constants.py ensures a drift-proof canonical.

P1-3 target_description PII redaction: request.justification is stored
     verbatim in ApprovalRequest.target_description (forever per B5
     retention). If recruiter pastes a CPF/email/phone in the free-text
     field it becomes a LGPD Art. 11 incident. Apply mask_pii before
     persist.
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


# ── P1-1 Idempotency ──────────────────────────────────────────────────────────


def test_request_toggle_idempotency_409_on_duplicate_pending():
    """Second submit with same (company_id, flag_key, requester_id) while
    a PENDING request exists must return 409. Prevents duplicate pending
    rows that spam the admin review queue."""
    from app.api.v1.lia_assistant_flags import (
        FeatureFlagToggleRequest,
        request_feature_flag_toggle,
    )

    # Simulate existing pending approval for the same key + requester
    existing = MagicMock()
    existing.id = "existing-approval-id"
    existing.status = "pending"

    mock_repo = MagicMock()
    mock_repo.add_and_flush = AsyncMock()
    # find_pending_duplicate returns the existing one → must trigger 409
    mock_repo.find_pending_duplicate = AsyncMock(return_value=existing)

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
            return await request_feature_flag_toggle(
                request=body,
                db=AsyncMock(),
                current_user=_make_user(is_admin=False, user_id="user-42"),
            )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())

    assert exc_info.value.status_code == 409, (
        f"Expected 409 for duplicate pending request, got "
        f"{exc_info.value.status_code}. Add idempotency check before "
        f"add_and_flush: call repo.find_pending_duplicate(company_id, "
        f"flag_key, requester_id) and raise 409 if result is not None."
    )
    assert not mock_repo.add_and_flush.called, (
        "add_and_flush was called despite duplicate pending — must "
        "short-circuit BEFORE persisting."
    )


def test_request_toggle_idempotency_allows_different_requester():
    """Different user in same company CAN submit a request for the same
    flag even when the first user's request is pending. Each requester
    is responsible for their own approval trail."""
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
    # No existing pending for THIS requester (different user's request exists
    # in the DB but find_pending_duplicate filters by requester_id too)
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
            return await request_feature_flag_toggle(
                request=body,
                db=AsyncMock(),
                current_user=_make_user(is_admin=False, user_id="user-99"),
            )

    asyncio.run(_run())

    assert mock_repo.add_and_flush.called, (
        "add_and_flush was NOT called for different requester. When "
        "find_pending_duplicate returns None, the request must proceed."
    )


def test_request_toggle_idempotency_allows_resubmission_after_resolved():
    """After a previous request is approved/rejected/cancelled, the same
    user CAN submit a new request. find_pending_duplicate only checks
    status=pending."""
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
    # No pending duplicate (prior request was resolved)
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
            return await request_feature_flag_toggle(
                request=body,
                db=AsyncMock(),
                current_user=_make_user(is_admin=False, user_id="user-42"),
            )

    asyncio.run(_run())

    assert mock_repo.add_and_flush.called, (
        "Re-submission after resolved prior request must succeed. "
        "find_pending_duplicate returning None means no pending block."
    )


def test_approvals_repo_has_find_pending_duplicate_method():
    """ApprovalsRepository must expose find_pending_duplicate(company_id,
    flag_key, requester_id) so the endpoint can check for idempotency."""
    from app.repositories.approvals_repository import (
        ApprovalsRepository,
    )
    assert hasattr(ApprovalsRepository, "find_pending_duplicate"), (
        "ApprovalsRepository missing find_pending_duplicate method. Add:\n"
        "  async def find_pending_duplicate(\n"
        "    self, company_id, flag_key: str, requester_id\n"
        "  ) -> Optional[ApprovalRequest]:\n"
        "    # SELECT ... WHERE company_id=:cid AND request_type='feature_flag_toggle'\n"
        "    #   AND target_name=:flag_key AND requester_id=:rid\n"
        "    #   AND status='pending' LIMIT 1"
    )


# ── P1-2 ALLOWED_TRAITS single source ────────────────────────────────────────


def test_ocean_constants_module_exists():
    """app/shared/ocean_constants.py must exist with ALLOWED_TRAITS."""
    import app.shared.ocean_constants as oc
    assert hasattr(oc, "ALLOWED_TRAITS"), (
        "app/shared/ocean_constants.py missing ALLOWED_TRAITS. Create:\n"
        "  ALLOWED_TRAITS = frozenset({'openness', 'conscientiousness',\n"
        "      'extraversion', 'agreeableness', 'stability'})"
    )
    assert isinstance(oc.ALLOWED_TRAITS, frozenset), (
        "ALLOWED_TRAITS must be a frozenset (immutable)."
    )
    expected = frozenset({"openness", "conscientiousness", "extraversion",
                          "agreeableness", "stability"})
    assert oc.ALLOWED_TRAITS == expected, (
        f"ALLOWED_TRAITS={oc.ALLOWED_TRAITS!r}, expected={expected!r}. "
        f"Check the 5-trait OCEAN set."
    )


def test_bigfive_repo_uses_shared_ocean_constants():
    """bigfive_department_profile_repository must import ALLOWED_TRAITS
    from app.shared.ocean_constants (single source of truth) rather than
    defining its own frozenset."""
    import inspect
    from app.domains.job_creation.repositories import (
        bigfive_department_profile_repository as repo_mod,
    )
    src = inspect.getsource(repo_mod)
    assert "from app.shared.ocean_constants import ALLOWED_TRAITS" in src, (
        "bigfive_department_profile_repository still defines ALLOWED_TRAITS "
        "locally. Replace the frozenset with:\n"
        "  from app.shared.ocean_constants import ALLOWED_TRAITS"
    )


def test_score_calculator_uses_shared_ocean_constants():
    """score_calculator._aggregate_ocean_traits must not have a local
    copy of the trait set — it must import ALLOWED_TRAITS from
    app.shared.ocean_constants so any update propagates everywhere."""
    import inspect
    from app.domains.cv_screening.services.wsi_service import score_calculator as sc_mod

    src = inspect.getsource(sc_mod.WSIScoreCalculator._aggregate_ocean_traits)
    assert "valid_traits" not in src, (
        "score_calculator._aggregate_ocean_traits still uses a local "
        "'valid_traits' dict literal. Replace with the imported constant:\n"
        "  from app.shared.ocean_constants import ALLOWED_TRAITS\n"
        "  # then use: if trait not in ALLOWED_TRAITS"
    )
    # Verify the import is at module level
    module_src = inspect.getsource(sc_mod)
    assert "from app.shared.ocean_constants import ALLOWED_TRAITS" in module_src, (
        "score_calculator.py missing: from app.shared.ocean_constants import ALLOWED_TRAITS"
    )


def test_allowed_traits_import_is_identical_across_consumers():
    """All consumers must see the same frozenset object (via import)."""
    from app.shared.ocean_constants import ALLOWED_TRAITS as shared_traits
    from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
        ALLOWED_TRAITS as repo_traits,
    )
    from app.domains.cv_screening.services.wsi_service.score_calculator import (
        ALLOWED_TRAITS as calc_traits,
    )
    assert shared_traits == repo_traits == calc_traits, (
        f"ALLOWED_TRAITS mismatch: shared={shared_traits!r}, "
        f"repo={repo_traits!r}, calc={calc_traits!r}. All must be "
        f"identical — import from the single source."
    )


# ── P1-3 target_description PII redaction ────────────────────────────────────


def test_request_toggle_redacts_cpf_in_justification():
    """A recruiter pasting a candidate CPF in the 'justification' field
    must NOT have it stored verbatim. target_description must be redacted
    before persisting (LGPD Art. 11 / B5 forever-retention contract)."""
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
        justification="Habilitar para candidato 123.456.789-09 do departamento X",
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

    asyncio.run(_run())

    approval = captured[0]
    desc = approval.target_description or ""
    assert "123.456.789-09" not in desc, (
        f"CPF found in target_description={desc!r}. Apply mask_pii() "
        f"from app.shared.pii_masking to request.justification before "
        f"setting target_description on the ApprovalRequest."
    )


def test_request_toggle_redacts_email_in_justification():
    """Email address in justification must also be scrubbed."""
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
        justification="Ativar para recruiter joao.silva@empresa.com.br do time Y",
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

    asyncio.run(_run())

    approval = captured[0]
    desc = approval.target_description or ""
    assert "joao.silva@empresa.com.br" not in desc, (
        f"Email found in target_description={desc!r}. mask_pii() from "
        f"app.shared.pii_masking covers email patterns — apply it to "
        f"request.justification before persisting."
    )


def test_request_toggle_null_justification_not_broken():
    """justification is optional — None must pass through cleanly without
    crashing the PII redaction path."""
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
        # no justification
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

    asyncio.run(_run())

    # Should not raise; target_description may be None or ""
    assert mock_repo.add_and_flush.called
