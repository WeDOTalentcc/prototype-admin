"""Wave 4 audit 2026-05-22 — P1 sensor: SCIM cross-tenant email collision.

Pre-Wave-4 contract bug
───────────────────────
``app/api/v1/workos.py`` handler ``scim_user_created`` looked up
``existing_by_email`` GLOBALLY (across all tenants) and, on hit, silently
overwrote ``workos_id``, ``workos_directory_id``, and ``is_scim_managed``
fields — without checking whether the existing user already belonged to a
DIFFERENT tenant.

Net effect: tenant B's IdP could hijack tenant A's user record by
provisioning the same email via SCIM. Subsequent SSO logins for that
email would route through tenant B's directory.

Policy = REJECT (conservative default)
─────────────────────────────────────
- Email exists in tenant A AND SCIM call comes from tenant B → HTTP 409.
- Email exists with NULL company_id (legacy unassigned) → link allowed.
- Email exists in same tenant → link allowed (idempotent SCIM).
- Email not found → create new user.

Cross-tenant merges go through ops (admin@wedotalent.cc) after both
tenants consent — never automatic from SCIM.

Test strategy: pure unit test with mocked repositories. We exercise the
handler function directly (not via HTTP) to keep this in tests/contract/.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.workos import scim_user_created
from app.auth.workos_schemas import SCIMUserCreated


def _make_repos(
    *,
    existing_user_company_id: str | None = None,
    config_company_id: str | None = None,
    existing_user_id: uuid.UUID | None = None,
    existing_user_present: bool = True,
):
    """Build mocked user_repo + workos_repo with configurable existing user."""
    user_repo = MagicMock()
    workos_repo = MagicMock()

    existing_user = None
    if existing_user_present:
        existing_user = MagicMock()
        existing_user.id = existing_user_id or uuid.uuid4()
        existing_user.company_id = existing_user_company_id

    user_repo.get_by_email = AsyncMock(return_value=existing_user)
    user_repo.get_by_workos_id = AsyncMock(return_value=None)
    user_repo.update_by_instance = AsyncMock()
    user_repo.create = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))

    company_config = None
    if config_company_id:
        company_config = MagicMock()
        company_config.company_id = config_company_id

    workos_repo.get_config_by_directory = AsyncMock(return_value=company_config)
    workos_repo.log_sso_event = AsyncMock()

    return user_repo, workos_repo


def _make_user_data(email: str = "user@example.com", directory_id: str = "dir-B"):
    return SCIMUserCreated(
        workos_id="user_B_workos",
        directory_id=directory_id,
        email=email,
        first_name="Test",
        last_name="User",
    )


@pytest.mark.asyncio
async def test_cross_tenant_collision_rejected_409():
    """SCIM from tenant B for email already in tenant A -> HTTP 409."""
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    user_repo, workos_repo = _make_repos(
        existing_user_company_id=tenant_a,
        config_company_id=tenant_b,
    )

    with pytest.raises(HTTPException) as exc_info:
        await scim_user_created(
            user_data=_make_user_data(),
            user_repo=user_repo,
            workos_repo=workos_repo,
            company_id=tenant_b,
        )

    assert exc_info.value.status_code == 409
    assert "another tenant" in exc_info.value.detail.lower()

    # The original user was NOT overwritten
    user_repo.update_by_instance.assert_not_awaited()

    # Audit trail logged
    workos_repo.log_sso_event.assert_awaited()
    logged_event = workos_repo.log_sso_event.await_args[0][0]
    assert logged_event["event_type"] == "scim.user.collision_rejected"
    assert logged_event["payload"]["action"] == "rejected_cross_tenant_collision"
    # email_hash_prefix present, full email NOT in payload (LGPD)
    assert "email_hash_prefix" in logged_event["payload"]


@pytest.mark.asyncio
async def test_same_tenant_link_allowed():
    """SCIM from tenant A for email in tenant A -> link (idempotent)."""
    tenant_a = str(uuid.uuid4())
    user_repo, workos_repo = _make_repos(
        existing_user_company_id=tenant_a,
        config_company_id=tenant_a,
    )

    result = await scim_user_created(
        user_data=_make_user_data(directory_id="dir-A"),
        user_repo=user_repo,
        workos_repo=workos_repo,
        company_id=tenant_a,
    )

    assert result.success is True
    user_repo.update_by_instance.assert_awaited()  # linked
    # No collision rejection
    logged_event = workos_repo.log_sso_event.await_args[0][0]
    assert logged_event["event_type"] != "scim.user.collision_rejected"


@pytest.mark.asyncio
async def test_unassigned_legacy_user_link_allowed():
    """Existing user with company_id=None (legacy) -> link to incoming tenant."""
    tenant_b = str(uuid.uuid4())
    user_repo, workos_repo = _make_repos(
        existing_user_company_id=None,  # legacy unassigned
        config_company_id=tenant_b,
    )

    result = await scim_user_created(
        user_data=_make_user_data(),
        user_repo=user_repo,
        workos_repo=workos_repo,
        company_id=tenant_b,
    )

    assert result.success is True
    user_repo.update_by_instance.assert_awaited()
    # company_id was set to tenant_b
    update_kwargs = user_repo.update_by_instance.await_args
    # Second positional arg is the update_data dict
    update_data = update_kwargs[0][1]
    assert update_data.get("company_id") == tenant_b


@pytest.mark.asyncio
async def test_no_existing_user_creates_new():
    """Email not found -> standard SCIM create flow."""
    tenant_b = str(uuid.uuid4())
    user_repo, workos_repo = _make_repos(
        existing_user_present=False,
        config_company_id=tenant_b,
    )

    result = await scim_user_created(
        user_data=_make_user_data(),
        user_repo=user_repo,
        workos_repo=workos_repo,
        company_id=tenant_b,
    )

    assert result.success is True
    user_repo.create.assert_awaited()
