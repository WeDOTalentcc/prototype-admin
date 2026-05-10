"""TDD red-phase — P0-1 IDOR fix in set_feature_flag (Sprint B post-audit).

Audit finding (canonical-fix agent): set_feature_flag in
app/api/v1/lia_assistant_flags.py passes request.company_id directly to
ff_svc.set_flag. An attacker authenticated as company A can flip a flag
in company B by sending company_id=B in the body. Violates CLAUDE.md
non-negotiable rule #1 (multi-tenancy: never trust company_id from
payload, always use JWT/session value).

Fix: introduce _enforce_flag_tenant() that:
- For non-admin users: forces request_company_id to match JWT, raises
  403 on mismatch, defaults to JWT when payload is None.
- For admin users: passes through as-is (admins manage global flags
  and cross-tenant operations explicitly).

Sentinels guard against regression to payload-trust pattern.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _make_user(user_id: str = "user-42", company_id: str = "co-A", is_admin: bool = False):
    from app.auth.models import UserRole
    user = MagicMock()
    user.id = user_id
    user.company_id = company_id
    user.email = "rec@example.com"
    user.role = UserRole.admin if is_admin else UserRole.recruiter
    return user


def _make_flag_request(flag_key: str = "learning_loops.jd_similar_suggestion",
                       is_enabled: bool = True,
                       company_id: str | None = "co-A"):
    # Default to a non-sensitive flag so HITL gate (P1-9) doesn't
    # interfere with IDOR/audit-log tests. Tests specifically for HITL
    # use sensitive flags explicitly.
    from app.api.v1.lia_assistant_flags import FeatureFlagRequest
    return FeatureFlagRequest(
        flag_key=flag_key,
        is_enabled=is_enabled,
        company_id=company_id,
        rollout_percentage=100,
        category="learning_loops",
        created_by="user-42",
    )


def _make_ff_svc():
    """ff_svc whose set_flag captures the company_id it actually receives."""
    svc = MagicMock()
    svc.set_flag = AsyncMock(return_value={
        "success": True,
        "flag_id": "ff-1",
        "flag_key": "x",
        "is_enabled": True,
        "company_id": "co-A",
        "rollout_percentage": 100,
    })
    return svc


# ── P0-1 — IDOR cross-tenant blocked for non-admin ──────────────────────────


def test_non_admin_cross_tenant_set_flag_raises_403():
    """A non-admin user from company A who sends company_id=B in the body
    must be blocked with HTTP 403. This is the IDOR fix."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        await set_feature_flag(
            request=_make_flag_request(company_id="co-B"),  # ← attacker payload
            db=AsyncMock(),
            current_user=_make_user(company_id="co-A", is_admin=False),
            ff_svc=ff_svc,
        )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_run())

    assert exc_info.value.status_code == 403, (
        f"Expected 403 (forbidden) but got {exc_info.value.status_code}. "
        f"Non-admin set_feature_flag with mismatched company_id must be "
        f"rejected. Add _enforce_flag_tenant() that raises HTTPException "
        f"403 when request.company_id != JWT company_id and user is not admin."
    )
    # Critical: ff_svc.set_flag MUST NOT have been called
    assert not ff_svc.set_flag.called, (
        "ff_svc.set_flag was called despite cross-tenant rejection. "
        "The 403 must short-circuit BEFORE any DB mutation."
    )


def test_non_admin_matching_tenant_set_flag_succeeds():
    """When request.company_id matches JWT, non-admin can flip their own
    company's flag (normal flow)."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            await set_feature_flag(
                request=_make_flag_request(company_id="co-A"),
                db=AsyncMock(),
                current_user=_make_user(company_id="co-A", is_admin=False),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())

    assert ff_svc.set_flag.called
    kwargs = ff_svc.set_flag.call_args.kwargs
    assert str(kwargs["company_id"]) == "co-A", (
        f"set_flag received company_id={kwargs['company_id']!r}, expected 'co-A'. "
        f"_enforce_flag_tenant must return the matched JWT company_id."
    )


def test_non_admin_omitted_company_id_defaults_to_jwt():
    """When request.company_id is None, non-admin gets JWT default
    (cannot accidentally hit a global flag)."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            await set_feature_flag(
                request=_make_flag_request(company_id=None),  # omitted
                db=AsyncMock(),
                current_user=_make_user(company_id="co-A", is_admin=False),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())

    assert ff_svc.set_flag.called
    kwargs = ff_svc.set_flag.call_args.kwargs
    assert str(kwargs["company_id"]) == "co-A", (
        f"With request.company_id=None, _enforce_flag_tenant must default "
        f"to current_user.company_id (got {kwargs['company_id']!r})."
    )


def test_admin_can_set_global_flag():
    """Admin (UserRole.admin) sending company_id=None must be allowed
    to set a global flag (None reaches set_flag)."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            await set_feature_flag(
                request=_make_flag_request(company_id=None),
                db=AsyncMock(),
                current_user=_make_user(company_id="co-A", is_admin=True),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())

    assert ff_svc.set_flag.called
    kwargs = ff_svc.set_flag.call_args.kwargs
    assert kwargs["company_id"] is None, (
        f"Admin with company_id=None must be allowed to set global flag, "
        f"but ff_svc.set_flag received company_id={kwargs['company_id']!r}. "
        f"_enforce_flag_tenant must pass through admin requests as-is."
    )


def test_admin_cross_tenant_allowed():
    """Admin can flip flags on any company (cross-tenant management)."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = _make_ff_svc()

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(),
        ):
            await set_feature_flag(
                request=_make_flag_request(company_id="co-B"),
                db=AsyncMock(),
                current_user=_make_user(company_id="co-A", is_admin=True),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())

    assert ff_svc.set_flag.called
    kwargs = ff_svc.set_flag.call_args.kwargs
    assert str(kwargs["company_id"]) == "co-B", (
        "Admin cross-tenant flag set should pass through unchanged."
    )
