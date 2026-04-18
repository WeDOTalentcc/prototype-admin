"""Task #478 — integration coverage for the same-key safeguard wired into
the candidate / vacancy / application write endpoints.

The unit-level canonicalization is already covered by
``tests/test_idempotency_dual_id.py``. This module exercises the wiring
end-to-end via FastAPI's TestClient: the same logical update retried with
both ID formats (fork UUID and Rails bigint) collapses onto one
idempotency key, and the second call is rejected with HTTP 409.
"""
from __future__ import annotations

import os

# AuthEnforcementMiddleware reads these at import time. Set them BEFORE
# importing app.main so the middleware allows the synthetic-user dev path.
os.environ.setdefault("LIA_DEV_MODE", "true")
os.environ.setdefault("LIA_DEV_API_KEY", "test-dev-key")

from unittest.mock import AsyncMock, MagicMock, patch  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

# Force the middleware module's cached flags to the test values, even if it
# was already imported by an earlier test module.
import app.middleware.auth_enforcement as _auth_mw  # noqa: E402
_auth_mw._DEV_MODE = True
_auth_mw._DEV_API_KEY = "test-dev-key"

from app.main import app  # noqa: E402
from app.core.database import get_db
from app.auth.dependencies import (
    get_current_active_user,
    get_current_user,
    get_current_user_or_demo,
    get_current_user_strict,
)
from app.domains.integrations_hub.services.rails_adapter_dependency import (
    get_rails_adapter,
)
from app.shared.robustness import idempotency as idempotency_module


FORK_UUID = "deadbeef-1234-5678-9abc-def012345678"
RAILS_BIGINT = "9001"
COMPANY_ID = "11111111-1111-1111-1111-111111111111"


class _StubRailsAdapter:
    """Fake adapter that knows the canonical UUID→bigint mapping for the
    test's candidate. Mirrors the surface of `RailsAdapter` that
    `_DUAL_ID_PARAM_RESOLVERS` cares about (`_resolve_rails_candidate_id`)."""

    def __init__(self) -> None:
        self.calls = 0

    async def _resolve_rails_candidate_id(self, candidate_id: str) -> int | None:
        self.calls += 1
        if candidate_id and candidate_id.isdigit():
            return int(candidate_id)
        if candidate_id == FORK_UUID:
            return int(RAILS_BIGINT)
        return None

    async def close(self) -> None:  # pragma: no cover - parity with real adapter
        return None


def _make_mock_db() -> AsyncSession:
    session = AsyncMock(spec=AsyncSession)
    candidate = MagicMock()
    candidate.id = FORK_UUID
    candidate.company_id = COMPANY_ID
    candidate.name = "Test Candidate"
    candidate.email = "test@example.com"
    candidate.status = "active"
    candidate.updated_at = None
    result = MagicMock()
    scalars = MagicMock()
    scalars.first.return_value = candidate
    scalars.all.return_value = [candidate]
    result.scalars.return_value = scalars
    result.scalar_one_or_none.return_value = candidate
    session.execute = AsyncMock(return_value=result)
    session.get = AsyncMock(return_value=candidate)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _mock_user():
    user = MagicMock()
    user.id = "user-1"
    user.company_id = COMPANY_ID
    user.role = "admin"
    user.is_active = True
    user.email = "admin@example.com"
    return user


@pytest.fixture
def stub_adapter() -> _StubRailsAdapter:
    return _StubRailsAdapter()


@pytest.fixture
def client(stub_adapter):
    async def _get_db_override():
        yield _make_mock_db()

    async def _get_adapter_override():
        yield stub_adapter

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_current_active_user] = _mock_user
    app.dependency_overrides[get_current_user_or_demo] = _mock_user
    app.dependency_overrides[get_current_user_strict] = _mock_user
    app.dependency_overrides[get_rails_adapter] = _get_adapter_override

    idempotency_module._reset_for_tests()

    with patch("app.main.init_db", AsyncMock()):
        with TestClient(
            app,
            raise_server_exceptions=False,
            headers={"X-Dev-Api-Key": "test-dev-key"},
        ) as c:
            yield c

    app.dependency_overrides.clear()
    idempotency_module._reset_for_tests()


def test_update_candidate_uuid_and_bigint_collapse_to_duplicate(
    client, stub_adapter
):
    """PUT /candidates/{uuid} followed by PUT /candidates/{bigint} for the
    same logical operation must yield HTTP 409 on the second call: the
    `RailsAdapter._resolve_rails_candidate_id` resolver collapses the two
    ID formats to the same idempotency key."""
    payload = {"current_title": "Senior Engineer"}

    first = client.put(f"/api/v1/candidates/{FORK_UUID}", json=payload)
    # The first call should NOT be rejected as duplicate; it may legitimately
    # 200 / 404 / 422 / 500 depending on downstream mock fidelity, but it
    # must not be 409 — that would mean dedup fired on the very first hit.
    assert first.status_code != 409, (
        f"First call was unexpectedly rejected as duplicate: {first.text}"
    )

    second = client.put(f"/api/v1/candidates/{RAILS_BIGINT}", json=payload)
    assert second.status_code == 409, (
        f"Expected duplicate rejection on retry with bigint; "
        f"got {second.status_code}: {second.text}"
    )
    body = second.json()
    # The global exception middleware wraps HTTPException.detail under
    # "message" (alongside "error", "status_code", "request_id"). Fall back
    # to "detail" for forward-compat if the wrapper is ever removed.
    payload = body.get("message") if isinstance(body, dict) else None
    if not isinstance(payload, dict):
        payload = body.get("detail") if isinstance(body, dict) else None
    assert isinstance(payload, dict), f"Unexpected 409 body: {body!r}"
    assert payload.get("error") == "duplicate_request"
    assert payload.get("idempotency_key")

    # The resolver was hit at least once: at minimum once for the UUID
    # request (the bigint short-circuits via `_to_rails_id`, so the
    # fork-uuid lookup may or may not be invoked depending on iteration
    # order, but the canonicalization branch ran for both calls).
    assert stub_adapter.calls >= 1


def test_distinct_payloads_are_not_collapsed(client):
    """Sanity: two updates for the same candidate but different payloads
    must NOT collide — over-collapsing would silently drop user edits."""
    first = client.put(
        f"/api/v1/candidates/{FORK_UUID}", json={"current_title": "Alpha"}
    )
    assert first.status_code != 409

    second = client.put(
        f"/api/v1/candidates/{FORK_UUID}", json={"current_title": "Beta"}
    )
    assert second.status_code != 409
