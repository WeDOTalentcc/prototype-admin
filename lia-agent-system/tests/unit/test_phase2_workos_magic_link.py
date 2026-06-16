"""
Phase 2 tests — WorkOS issue-token + Magic-link FastAPI endpoints.

Tests:
1. workos/issue-token returns 503 when WORKOS_FASTAPI_JWT=False (default)
2. workos/issue-token returns 403 when INTERNAL_API_SECRET mismatch
3. workos/issue-token returns 404 when user not found
4. workos/issue-token returns JWT when user exists and flag on
5. magic-link/verify returns 401 for unknown uid
6. magic-link/send + verify round-trip (Redis mock)
7. magic_link_service: verify wrong token hash → None
8. magic_link_service: verify expired/missing → None
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette import status


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_app():
    """Build minimal FastAPI with the auth router."""
    from app.api.v1.auth import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


# ── 1. workos/issue-token: flag off → 503 ────────────────────────────────────

def test_workos_issue_token_flag_off():
    """When WORKOS_FASTAPI_JWT=False (default), endpoint returns 503."""
    from app.repositories.dependencies import get_user_repo
    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=None)
    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock()

    app = _make_app()
    app.dependency_overrides[get_user_repo] = lambda: mock_repo
    from app.shared.compliance.audit_service import get_audit_service
    app.dependency_overrides[get_audit_service] = lambda: mock_audit

    with patch("app.core.config.settings") as mock_cfg:
        mock_cfg.WORKOS_FASTAPI_JWT = False
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/workos/issue-token",
            json={"email": "user@example.com"},
        )
    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# ── 2. workos/issue-token: bad internal secret → 403 ─────────────────────────

def test_workos_issue_token_bad_secret():
    """Wrong X-Internal-Auth header → 403."""
    from app.repositories.dependencies import get_user_repo
    from app.shared.compliance.audit_service import get_audit_service
    mock_repo = MagicMock()
    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock()
    app = _make_app()
    app.dependency_overrides[get_user_repo] = lambda: mock_repo
    app.dependency_overrides[get_audit_service] = lambda: mock_audit

    with patch.dict("os.environ", {"INTERNAL_API_SECRET": "correct-secret"}), \
         patch("app.core.config.settings") as mock_cfg:
        mock_cfg.WORKOS_FASTAPI_JWT = True
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/workos/issue-token",
            json={"email": "user@example.com"},
            headers={"X-Internal-Auth": "wrong-secret"},
        )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


# ── 3. workos/issue-token: user not found → 404 ───────────────────────────────

def test_workos_issue_token_user_not_found():
    """User not in FastAPI DB → 404."""
    from app.repositories.dependencies import get_user_repo
    from app.shared.compliance.audit_service import get_audit_service
    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=None)
    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock()
    app = _make_app()
    app.dependency_overrides[get_user_repo] = lambda: mock_repo
    app.dependency_overrides[get_audit_service] = lambda: mock_audit

    with patch.dict("os.environ", {"INTERNAL_API_SECRET": ""}), \
         patch("app.core.config.settings") as mock_cfg:
        mock_cfg.WORKOS_FASTAPI_JWT = True
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/workos/issue-token",
            json={"email": "nouser@example.com"},
        )
    assert resp.status_code == status.HTTP_404_NOT_FOUND


# ── 4. workos/issue-token: success → JWT ─────────────────────────────────────

def test_workos_issue_token_success():
    """Active user + flag on → returns FastAPI JWT."""
    from app.repositories.dependencies import get_user_repo
    from app.shared.compliance.audit_service import get_audit_service

    mock_user = MagicMock()
    mock_user.id = "user-uuid-1234"
    mock_user.is_active = True
    mock_user.role = MagicMock(value="recruiter")
    mock_user.company_id = "company-uuid-5678"

    mock_repo = MagicMock()
    mock_repo.get_by_email = AsyncMock(return_value=mock_user)
    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock()

    app = _make_app()
    app.dependency_overrides[get_user_repo] = lambda: mock_repo
    app.dependency_overrides[get_audit_service] = lambda: mock_audit

    with patch.dict("os.environ", {"INTERNAL_API_SECRET": ""}), \
         patch("app.core.config.settings") as mock_cfg:
        mock_cfg.WORKOS_FASTAPI_JWT = True
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/v1/auth/workos/issue-token",
            json={"email": "sso@example.com", "workos_id": "wos_abc"},
        )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["issued_for"] == "workos_sso"


# ── 5. magic-link/verify: unknown uid → 401 ─────────────────────────────────

def test_magic_link_verify_unknown_uid():
    """Verify with uid not in Redis → 401."""
    from app.repositories.dependencies import get_user_repo
    from app.shared.compliance.audit_service import get_audit_service
    mock_repo = MagicMock()
    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock()
    app = _make_app()
    app.dependency_overrides[get_user_repo] = lambda: mock_repo
    app.dependency_overrides[get_audit_service] = lambda: mock_audit

    with patch("app.auth.magic_link_service.verify_magic_link", new_callable=AsyncMock, return_value=None):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/v1/auth/magic-link/verify?token=bad&uid=bad-uid")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ── 6. magic-link send + verify round-trip ───────────────────────────────────

@pytest.mark.asyncio
async def test_magic_link_service_round_trip():
    """generate + verify round-trip using mocked Redis."""
    from app.auth.magic_link_service import generate_magic_link, verify_magic_link

    store: dict = {}

    class FakeRedis:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def set(self, key, value, ex=None): store[key] = value
        async def get(self, key): return store.get(key)
        async def delete(self, key): store.pop(key, None)

    with patch("app.core.redis_client.get_redis_connection", new_callable=AsyncMock, return_value=FakeRedis()), \
         patch.dict("os.environ", {"APP_ENV": "development"}):
        magic_url = await generate_magic_link(
            email="test@example.com",
            frontend_url="https://app.example.com",
            first_login=True,
        )

    assert "token=" in magic_url and "uid=" in magic_url
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(magic_url).query)
    token = qs["token"][0]
    uid = qs["uid"][0]

    # Verify with correct token
    with patch("app.core.redis_client.get_redis_connection", new_callable=AsyncMock, return_value=FakeRedis()):
        # Put the stored value back (store still has it from generate)
        class FakeRedis2:
            async def __aenter__(self): return self
            async def __aexit__(self, *a): pass
            async def get(self, key): return store.get(key)
            async def delete(self, key): store.pop(key, None)

        result = await verify_magic_link(token=token, uid=uid)

    assert result is not None
    assert result["email"] == "test@example.com"
    assert result["first_login"] is True
    # Single-use: second verify should return None
    with patch("app.core.redis_client.get_redis_connection", new_callable=AsyncMock, return_value=FakeRedis2()):
        result2 = await verify_magic_link(token=token, uid=uid)
    assert result2 is None


# ── 7. wrong token hash → None ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_magic_link_verify_wrong_token():
    """Verify with correct uid but wrong token → None."""
    from app.auth.magic_link_service import verify_magic_link, _hash_token

    stored_payload = json.dumps({
        "email": "x@example.com",
        "hash": _hash_token("real-token"),
        "first_login": False,
    })

    class FakeRedis:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def get(self, key): return stored_payload
        async def delete(self, key): pass

    with patch("app.core.redis_client.get_redis_connection", new_callable=AsyncMock, return_value=FakeRedis()):
        result = await verify_magic_link(token="wrong-token", uid="some-uid")
    assert result is None


# ── 8. Redis unavailable → None ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_magic_link_verify_redis_unavailable():
    """Redis unavailable → None (fail-open for verify)."""
    from app.auth.magic_link_service import verify_magic_link

    with patch("app.core.redis_client.get_redis_connection", new_callable=AsyncMock, return_value=None):
        result = await verify_magic_link(token="any", uid="any")
    assert result is None
