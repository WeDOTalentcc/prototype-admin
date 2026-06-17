"""TDD red-phase — P1-9 HITL gate on sensitive feature flags.

Audit finding (governance agent): C2 audit log captures who flipped a
feature flag, but provides no HITL gate. CLAUDE.md compliance-risk says
'Decisão automatizada (Art. 20) exige direito de revisão humana'. The
log enables forensics, NOT review.

Fix: a canonical list of SENSITIVE_FLAGS_REQUIRING_HITL. When a non-
admin tries to flip one of these flags, the endpoint rejects with HTTP
403 directing them to a DPO/admin. Admins (UserRole.admin) can flip
sensitive flags directly — they ARE the human review.

Phase 2 follow-up: a full second-actor approval workflow (request token
+ approve endpoint + UI) lands when the toggle UI ships. Until then,
this gate enforces the human-review principle by routing sensitive
toggles through admins.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _make_user(is_admin: bool = False, company_id: str = "co-A"):
    from app.auth.models import UserRole
    user = MagicMock()
    user.id = "user-42"
    user.company_id = company_id
    user.email = "rec@example.com"
    user.role = UserRole.admin if is_admin else UserRole.recruiter
    return user


def _make_request(flag_key: str, company_id: str | None = "co-A"):
    from app.api.v1.lia_assistant_flags import FeatureFlagRequest
    return FeatureFlagRequest(
        flag_key=flag_key, is_enabled=True, company_id=company_id,
        rollout_percentage=100, category="learning_loops", created_by="user-42",
    )


def _make_ff_svc():
    svc = MagicMock()
    svc.set_flag = AsyncMock(return_value={
        "success": True, "flag_id": "ff-1", "flag_key": "x",
        "is_enabled": True, "company_id": "co-A",
    })
    return svc


def test_sensitive_flags_canonical_list_includes_bigfive_dept_and_wsi_eff():
    """The canonical list of sensitive flags must include the two LGPD-
    risky learning loops."""
    from app.api.v1.lia_assistant_flags import SENSITIVE_FLAGS_REQUIRING_HITL

    sensitive = set(SENSITIVE_FLAGS_REQUIRING_HITL)
    # The fully-qualified flag_key formats used by policy_sync_service:
    expected_keys = {
        "learning_loops.bigfive_department_history",
        "learning_loops.wsi_question_effectiveness",
    }
    assert expected_keys.issubset(sensitive), (
        f"SENSITIVE_FLAGS_REQUIRING_HITL is missing keys. Expected at "
        f"least {expected_keys}, got {sensitive}. These flags drive "
        f"population-level LGPD-sensitive behaviors and must require HITL."
    )


def test_non_admin_cannot_flip_sensitive_flag():
    """Non-admin trying to flip a sensitive flag gets 403."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        await set_feature_flag(
            request=_make_request("learning_loops.bigfive_department_history"),
            db=AsyncMock(),
            current_user=_make_user(is_admin=False),
            ff_svc=ff_svc,
        )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())

    assert exc_info.value.status_code == 403, (
        f"Expected 403 for non-admin flipping sensitive flag, got "
        f"{exc_info.value.status_code}. Add a HITL gate that rejects "
        f"sensitive flag toggles by non-admin users with a clear error "
        f"directing them to a DPO/admin."
    )
    detail = str(exc_info.value.detail).lower()
    assert "dpo" in detail or "admin" in detail or "approval" in detail or "review" in detail, (
        f"Rejection message should direct the user to DPO/admin/approval "
        f"flow. Got: {exc_info.value.detail!r}"
    )
    assert not ff_svc.set_flag.called, (
        "ff_svc.set_flag was called despite HITL rejection — the gate "
        "must short-circuit BEFORE any DB mutation."
    )


def test_admin_can_flip_sensitive_flag():
    """Admin can flip sensitive flags directly — they are the human review."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            await set_feature_flag(
                request=_make_request("learning_loops.bigfive_department_history"),
                db=AsyncMock(),
                current_user=_make_user(is_admin=True),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())
    assert ff_svc.set_flag.called, (
        "Admin should be able to flip sensitive flags directly — they "
        "are the human reviewer per ADR-LGPD-001 / Art. 20 contract."
    )


def test_non_sensitive_flag_unaffected_by_hitl_gate():
    """Non-sensitive flags continue to flow normally for non-admin."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            await set_feature_flag(
                request=_make_request("learning_loops.jd_similar_suggestion"),
                db=AsyncMock(),
                current_user=_make_user(is_admin=False),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())
    assert ff_svc.set_flag.called, (
        "Non-sensitive flag (jd_similar_suggestion) was rejected. The "
        "HITL gate must apply ONLY to flags in SENSITIVE_FLAGS_REQUIRING_HITL."
    )
