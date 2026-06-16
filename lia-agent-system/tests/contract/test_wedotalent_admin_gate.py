"""
C2 / E1 regression sensor (audit 2026-05-21): tenant-override endpoints
under ``/api/v1/admin/prompts/tenant-overrides/*`` MUST require
``UserRole.wedotalent_admin``. Customer-end roles (admin / recruiter /
viewer) MUST receive 403.

Bug-class context: until 2026-05-21, those endpoints used
``require_admin`` which any customer-end org admin satisfies. That meant
the YAML override UI in plataforma-lia — surfaced to every customer — was
backed by an API that any customer-org admin could call. The role gate
upgrade to ``require_wedotalent_admin`` plus the frontend visibility hide
(E1) close the loop. This module pins the contract so neither half can
regress silently.

Strategy: source-level assertion that each of the four handlers has the
canonical decorator wired. We do NOT hit the running server — that would
turn this into an integration test. The contract under test is "the
endpoint declares the right Dependency"; that lives in the source.
"""
from __future__ import annotations

import inspect

import pytest

from app.api.v1 import admin_prompts
from app.auth.dependencies import require_wedotalent_admin
from app.auth.models import UserRole


def test_user_role_enum_has_wedotalent_admin():
    """Renaming or removing the canonical role string is a wire-breaking
    change. Pin it so any rename is forced through this test."""
    assert UserRole.wedotalent_admin.value == "wedotalent_admin", (
        "UserRole.wedotalent_admin value MUST stay 'wedotalent_admin'. "
        "Renaming this string forces a coordinated change across the "
        "backend gate, the frontend role check (E1), JWT issuer, and the "
        "user-management UI in admin2.wedotalent.cc."
    )


@pytest.mark.parametrize(
    "handler_name",
    [
        "list_tenant_overrides",
        "get_tenant_override",
        "put_tenant_override",
        "delete_tenant_override",
    ],
)
def test_tenant_override_handlers_require_wedotalent_admin(handler_name: str):
    """Each tenant-override handler must declare
    ``Depends(require_wedotalent_admin)`` on its ``current_user`` parameter.

    Source-level assertion: we read the function source and look for the
    canonical call. Faster than spinning up FastAPI's TestClient and
    immune to environment quirks (JWT signing keys, DB session fixtures).
    """
    handler = getattr(admin_prompts, handler_name)
    src = inspect.getsource(handler)
    assert "require_wedotalent_admin" in src, (
        f"{handler_name} no longer declares require_wedotalent_admin. "
        f"Reintroducing require_admin (customer-end role) on this handler "
        f"means any customer-org admin can edit per-tenant YAML overrides. "
        f"See CLAUDE.md 'Admin WeDOTalent Integration Contract' section."
    )
    assert "require_admin)" not in src.replace("require_admin_or_recruiter", ""), (
        f"{handler_name} still references plain require_admin. Either the "
        f"gate was reverted or both decorators are present (ambiguous gate). "
        f"Inspect manually."
    )


@pytest.mark.parametrize(
    "role,expect_admit",
    [
        (UserRole.wedotalent_admin, True),
        (UserRole.admin, False),
        (UserRole.recruiter, False),
        (UserRole.viewer, False),
    ],
)
@pytest.mark.asyncio
async def test_require_wedotalent_admin_only_admits_wedotalent_role(
    role: UserRole, expect_admit: bool
):
    """The dependency MUST admit ONLY ``UserRole.wedotalent_admin``. Customer
    -end roles (admin / recruiter / viewer) must hit 403.

    Exercises the closure directly with a mock user instead of going
    through HTTP — same posture as the offer gate tests above.
    """
    from fastapi import HTTPException
    from unittest.mock import MagicMock

    user = MagicMock()
    user.role = role
    user.is_active = True

    if expect_admit:
        out = await require_wedotalent_admin(current_user=user)
        assert out is user
    else:
        with pytest.raises(HTTPException) as exc_info:
            await require_wedotalent_admin(current_user=user)
        assert exc_info.value.status_code == 403
