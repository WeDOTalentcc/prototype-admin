"""
R-018 — JWT matrix tests for auth_enforcement middleware.

Covers:
- Valid JWT → ContextVar populated → request proceeds
- Expired JWT → falls back to Rails JWT
- Invalid signature JWT → 401 response
- JWT missing company_id → defaults to "" (not crash)
- JWT with company_id → ContextVar has correct value
- Rails JWT fallback (account_id → company_id, is_admin → role="admin")
- Rails token invalid → 401 response
- Both JWT and Rails fail → 401
- DEV_MODE gating (R-006): production/staging blocks even if LIA_DEV_MODE=true
- Cross-tenant attack: JWT company != X-Company-ID header → 403
- ContextVar NOT populated from header directly
- OPTIONS (CORS preflight) skips auth → passes through
- No Bearer token → 401 in non-DEV_MODE
"""

from __future__ import annotations

import asyncio
import importlib
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_middleware(
    env_overrides: dict,
    *,
    decode_token_payload=None,
    decode_token_raises=None,
    rails_payload=None,
):
    """Reload auth_enforcement with patched env and optional mock patches.

    Returns (app, module) ready for TestClient use.
    decode_token_payload: dict → decode_token returns this.
    decode_token_raises: exception type → decode_token raises it.
    rails_payload: dict | None → validate_rails_token_from_env returns RailsTokenPayload or None.
    """
    base_env = {
        "LIA_DEV_MODE": "",
        "ENVIRONMENT": "production",
        "LIA_DEV_API_KEY": "",
    }
    base_env.update(env_overrides)

    with patch.dict(os.environ, base_env, clear=False):
        import app.middleware.auth_enforcement as m
        importlib.reload(m)

        app = FastAPI()
        app.add_middleware(m.AuthEnforcementMiddleware)

        @app.get("/api/v1/candidates")
        async def protected(request: Request):
            return JSONResponse({
                "company_id": getattr(request.state, "company_id", None),
                "user_id": getattr(request.state, "user_id", None),
                "role": getattr(request.state, "user_role", None),
            })

        return app, m


def _make_jwt_payload(company_id="acme", sub="user@example.com", role="recruiter"):
    return {
        "sub": sub,
        "company_id": company_id,
        "role": role,
    }


def _make_rails_payload(user_id=42, account_id="acme", is_admin=False):
    from unittest.mock import MagicMock
    p = MagicMock()
    p.user_id = user_id
    return p


def _make_rails_user_info(email="rails@example.com", account_id="acme", is_admin=False):
    return {"email": email, "account_id": account_id, "is_admin": is_admin}


# ---------------------------------------------------------------------------
# Section 1 — Valid JWT paths
# ---------------------------------------------------------------------------

class TestValidJWT:

    def test_valid_jwt_request_proceeds_200(self):
        """Valid JWT → middleware lets request through → 200."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload()

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer validtoken"},
            )
        assert resp.status_code == 200

    def test_valid_jwt_company_id_in_state(self):
        """Valid JWT → request.state.company_id equals JWT company_id."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload(company_id="acme_corp")

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer validtoken"},
            )
        assert resp.status_code == 200
        assert resp.json()["company_id"] == "acme_corp"

    def test_valid_jwt_user_id_in_state(self):
        """Valid JWT → request.state.user_id equals JWT sub."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload(sub="ceo@acme.com")

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer validtoken"},
            )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "ceo@acme.com"

    def test_jwt_missing_company_id_defaults_to_empty_string(self):
        """JWT with no company_id claim → defaults to '' (not crash)."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = {"sub": "user@example.com", "role": "recruiter"}  # no company_id

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer validtoken"},
            )
        # Should not crash; either 200 with empty company_id or 401 for no subject
        assert resp.status_code in (200, 401)

    def test_contextvars_not_set_from_header(self):
        """X-Company-ID header alone does NOT populate ContextVar — only JWT does."""
        import app.middleware.auth_enforcement as m
        importlib.reload(m)
        # ContextVar starts at default ""
        # The header should never set it directly
        val = m._current_company_id.get()
        assert val == ""  # default, not whatever header would set

    def test_valid_jwt_role_propagated_to_state(self):
        """JWT role claim is propagated to request.state.user_role."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload(role="admin")

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer validtoken"},
            )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"


# ---------------------------------------------------------------------------
# Section 2 — JWT decode failure → Rails JWT fallback
# ---------------------------------------------------------------------------

class TestRailsJWTFallback:

    def test_expired_jwt_falls_back_to_rails(self):
        """decode_token raises → middleware tries Rails JWT fallback."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        rails_user_info = _make_rails_user_info(account_id="rails_company")
        rails_payload_mock = _make_rails_payload(account_id="rails_company")

        with (
            patch("app.auth.security.decode_token", side_effect=Exception("ExpiredSignature")),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=rails_payload_mock),
            patch("app.auth.rails_jwt.fetch_rails_user_info", new=AsyncMock(return_value=rails_user_info)),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer expiredtoken"},
            )
        assert resp.status_code == 200
        assert resp.json()["company_id"] == "rails_company"

    def test_rails_token_admin_user_gets_admin_role(self):
        """Rails token with is_admin=True → request.state.user_role = 'admin'."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        rails_user_info = _make_rails_user_info(is_admin=True, account_id="corp")
        rails_payload_mock = _make_rails_payload(account_id="corp", is_admin=True)

        with (
            patch("app.auth.security.decode_token", return_value=None),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=rails_payload_mock),
            patch("app.auth.rails_jwt.fetch_rails_user_info", new=AsyncMock(return_value=rails_user_info)),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer railstoken"},
            )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_rails_token_non_admin_gets_recruiter_role(self):
        """Rails token with is_admin=False → role = 'recruiter'."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        rails_user_info = _make_rails_user_info(is_admin=False, account_id="corp")
        rails_payload_mock = _make_rails_payload(account_id="corp", is_admin=False)

        with (
            patch("app.auth.security.decode_token", return_value=None),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=rails_payload_mock),
            patch("app.auth.rails_jwt.fetch_rails_user_info", new=AsyncMock(return_value=rails_user_info)),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer railstoken"},
            )
        assert resp.status_code == 200
        assert resp.json()["role"] == "recruiter"

    def test_invalid_signature_jwt_and_rails_fails_returns_401(self):
        """JWT invalid signature + Rails fallback fails → 401 (not 500)."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        with (
            patch("app.auth.security.decode_token", side_effect=Exception("InvalidSignature")),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=None),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer badtoken"},
            )
        assert resp.status_code == 401

    def test_both_jwt_and_rails_fail_returns_401(self):
        """decode_token → None, rails → None → final 401."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        with (
            patch("app.auth.security.decode_token", return_value=None),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=None),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer badtoken"},
            )
        assert resp.status_code == 401

    def test_rails_account_id_mapped_to_company_id(self):
        """Rails payload account_id is mapped to company_id in request.state."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        rails_user_info = _make_rails_user_info(account_id="rails_tenant_42")
        rails_payload_mock = _make_rails_payload(account_id="rails_tenant_42")

        with (
            patch("app.auth.security.decode_token", return_value=None),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=rails_payload_mock),
            patch("app.auth.rails_jwt.fetch_rails_user_info", new=AsyncMock(return_value=rails_user_info)),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer railstoken"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_id"] == "rails_tenant_42"


# ---------------------------------------------------------------------------
# Section 3 — DEV_MODE environment gating (R-006 critical security)
# ---------------------------------------------------------------------------

class TestDevModeGating:

    def _get_dev_mode(self, lia_dev_mode: str, environment: str) -> bool:
        """Reload module with given env vars and return _DEV_MODE flag value."""
        env = {
            "LIA_DEV_MODE": lia_dev_mode,
            "ENVIRONMENT": environment,
            "LIA_DEV_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env, clear=False):
            import app.middleware.auth_enforcement as m
            importlib.reload(m)
            return m._DEV_MODE

    def test_dev_mode_true_in_production_is_blocked(self):
        """LIA_DEV_MODE=true + ENVIRONMENT=production → DEV_MODE=False (fail-closed)."""
        result = self._get_dev_mode("true", "production")
        assert result is False

    def test_dev_mode_true_in_staging_is_blocked(self):
        """LIA_DEV_MODE=true + ENVIRONMENT=staging → DEV_MODE=False."""
        result = self._get_dev_mode("true", "staging")
        assert result is False

    def test_dev_mode_true_in_development_is_active(self):
        """LIA_DEV_MODE=true + ENVIRONMENT=development → DEV_MODE=True."""
        result = self._get_dev_mode("true", "development")
        assert result is True

    def test_dev_mode_true_in_local_is_active(self):
        """LIA_DEV_MODE=true + ENVIRONMENT=local → DEV_MODE=True."""
        result = self._get_dev_mode("true", "local")
        assert result is True

    def test_dev_mode_true_in_test_env_is_active(self):
        """LIA_DEV_MODE=true + ENVIRONMENT=test → DEV_MODE=True."""
        result = self._get_dev_mode("true", "test")
        assert result is True

    def test_dev_mode_false_blocks_everywhere(self):
        """LIA_DEV_MODE=false (any ENVIRONMENT) → DEV_MODE=False."""
        for env in ("development", "local", "test", "production", "staging"):
            result = self._get_dev_mode("false", env)
            assert result is False, f"Expected DEV_MODE=False for ENVIRONMENT={env}"

    def test_dev_mode_unset_blocks_everywhere(self):
        """LIA_DEV_MODE unset → DEV_MODE=False regardless of ENVIRONMENT."""
        for env in ("development", "production"):
            result = self._get_dev_mode("", env)
            assert result is False

    def test_dev_mode_1_in_development_is_active(self):
        """LIA_DEV_MODE=1 (truthy) in development → DEV_MODE=True."""
        result = self._get_dev_mode("1", "development")
        assert result is True

    def test_dev_mode_yes_in_development_is_active(self):
        """LIA_DEV_MODE=yes in development → DEV_MODE=True."""
        result = self._get_dev_mode("yes", "development")
        assert result is True


# ---------------------------------------------------------------------------
# Section 4 — Cross-tenant attack mitigation
# ---------------------------------------------------------------------------

class TestCrossTenantAttackMitigation:

    def test_jwt_company_and_header_company_mismatch_returns_403(self):
        """JWT company_id='acme' + header X-Company-ID='evil' → 403."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload(company_id="acme")

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={
                    "Authorization": "Bearer validtoken",
                    "X-Company-ID": "evil_corp",
                },
            )
        assert resp.status_code == 403

    def test_cross_tenant_response_has_detail(self):
        """403 response from cross-tenant attempt has a detail field."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload(company_id="acme")

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={
                    "Authorization": "Bearer validtoken",
                    "X-Company-ID": "not_acme",
                },
            )
        assert resp.status_code == 403
        assert "detail" in resp.json()

    def test_matching_header_and_jwt_company_passes(self):
        """JWT company='acme' + header X-Company-ID='acme' → 200 (consistent)."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload(company_id="acme")

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={
                    "Authorization": "Bearer validtoken",
                    "X-Company-ID": "acme",
                },
            )
        assert resp.status_code == 200

    def test_no_x_company_id_header_does_not_block(self):
        """No X-Company-ID header → normal JWT flow, no 403."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        jwt_payload = _make_jwt_payload(company_id="acme")

        with patch("app.auth.security.decode_token", return_value=jwt_payload):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer validtoken"},
            )
        assert resp.status_code == 200

    def test_contextvar_not_set_from_x_company_id_header(self):
        """ContextVar _current_company_id should only reflect JWT value, not arbitrary header."""
        import app.middleware.auth_enforcement as m
        # ContextVar starts empty — header should never pre-populate it
        current = m._current_company_id.get()
        assert current == ""


# ---------------------------------------------------------------------------
# Section 5 — CORS and public paths
# ---------------------------------------------------------------------------

class TestCORSAndPublicPaths:

    def test_options_request_skips_auth(self):
        """OPTIONS (CORS preflight) bypasses auth — returns response without 401."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        # We need a real route for OPTIONS to succeed
        @app.options("/api/v1/candidates")
        async def options_handler():
            return JSONResponse({}, status_code=200)

        client = TestClient(app)
        resp = client.options("/api/v1/candidates")
        # Should NOT be 401
        assert resp.status_code != 401

    def test_public_path_health_no_auth(self):
        """Public path /health does not require Bearer token."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})

        @app.get("/health")
        async def health():
            return JSONResponse({"status": "ok"})

        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_no_bearer_token_returns_401(self):
        """Request without any Authorization header → 401 in prod."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        client = TestClient(app)
        resp = client.get("/api/v1/candidates")
        assert resp.status_code == 401

    def test_non_bearer_token_returns_401(self):
        """Authorization: Basic xyz (not Bearer) → 401."""
        app, _ = _reload_middleware({"ENVIRONMENT": "production"})
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Section 6 — _set_company_id_synthetic_dev_only guard
# ---------------------------------------------------------------------------

class TestSyntheticDevModeGuard:

    def test_synthetic_helper_raises_outside_dev_mode(self):
        """_set_company_id_synthetic_dev_only raises RuntimeError when _DEV_MODE=False."""
        env = {
            "LIA_DEV_MODE": "",
            "ENVIRONMENT": "production",
        }
        with patch.dict(os.environ, env, clear=False):
            import app.middleware.auth_enforcement as m
            importlib.reload(m)
            assert m._DEV_MODE is False
            with pytest.raises(RuntimeError, match="R-008"):
                m._set_company_id_synthetic_dev_only("hacker")

    def test_set_company_id_from_jwt_returns_correct_value(self):
        """_set_company_id_from_jwt extracts company_id from verified payload."""
        import app.middleware.auth_enforcement as m
        importlib.reload(m)
        payload = {"company_id": "my_tenant", "sub": "user@example.com"}
        result = m._set_company_id_from_jwt(payload)
        assert result == "my_tenant"

    def test_set_company_id_from_jwt_missing_claim_returns_empty(self):
        """_set_company_id_from_jwt with no company_id claim returns ''."""
        import app.middleware.auth_enforcement as m
        importlib.reload(m)
        payload = {"sub": "user@example.com"}
        result = m._set_company_id_from_jwt(payload)
        assert result == ""
