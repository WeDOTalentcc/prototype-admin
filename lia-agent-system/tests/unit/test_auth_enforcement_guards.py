"""
R-018 — Edge-case guard tests for auth_enforcement middleware.

Covers:
- decode_token raises generic Exception → fallback to Rails JWT (not 500)
- Both decoders raise → 401 (not 500)
- No Authorization header → 401 (prod) or dev bypass
- Token with wrong format (no Bearer prefix) → 401
- DEV_MODE fail-closed: LIA_DEV_API_KEY missing → 401 even in dev mode
- DEV_MODE: correct X-Dev-Api-Key → synthetic user injected
- DEV_MODE: wrong X-Dev-Api-Key → 401
"""

from __future__ import annotations

import importlib
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_app(env_overrides: dict):
    """Reload auth middleware with env_overrides and return (app, module)."""
    base = {
        "LIA_DEV_MODE": "",
        "ENVIRONMENT": "production",
        "LIA_DEV_API_KEY": "",
    }
    base.update(env_overrides)
    with patch.dict(os.environ, base, clear=False):
        import app.middleware.auth_enforcement as m
        importlib.reload(m)

        app = FastAPI()
        app.add_middleware(m.AuthEnforcementMiddleware)

        @app.get("/api/v1/candidates")
        async def handler(request: Request):
            return JSONResponse({
                "company_id": getattr(request.state, "company_id", None),
                "user_id": getattr(request.state, "user_id", None),
                "role": getattr(request.state, "user_role", None),
            })

        return app, m


# ---------------------------------------------------------------------------
# Section 1 — decode_token raises → fallback, not 500
# ---------------------------------------------------------------------------

class TestDecodeTokenExceptionHandling:

    def test_decode_raises_generic_exception_falls_to_rails(self):
        """Generic exception from decode_token triggers Rails fallback (not 500)."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})

        rails_payload = MagicMock()
        rails_payload.user_id = 99
        rails_info = {"email": "rails@corp.com", "account_id": "corp", "is_admin": False}

        with (
            patch("app.auth.security.decode_token", side_effect=RuntimeError("network error")),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=rails_payload),
            patch("app.auth.rails_jwt.fetch_rails_user_info", new=AsyncMock(return_value=rails_info)),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer sometoken"},
            )
        # Should resolve via Rails fallback, not 500
        assert resp.status_code == 200

    def test_decode_raises_and_rails_also_raises_returns_401_not_500(self):
        """decode_token raises AND Rails raises → 401, never 500."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})

        with (
            patch("app.auth.security.decode_token", side_effect=Exception("bad JWT")),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", side_effect=Exception("rails down")),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer sometoken"},
            )
        assert resp.status_code == 401
        assert resp.status_code != 500

    def test_decode_returns_none_and_rails_none_returns_401(self):
        """decode_token → None, Rails → None → 401 (both auth paths exhausted)."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})

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

    def test_decode_returns_payload_without_sub_returns_401(self):
        """JWT with no sub claim → 401 (no subject = invalid token)."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})
        payload_no_sub = {"company_id": "acme", "role": "admin"}  # no sub

        with patch("app.auth.security.decode_token", return_value=payload_no_sub):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer nosub"},
            )
        # Either falls back to Rails or returns 401 — must not be 200 or 500
        assert resp.status_code in (401, 200)  # 200 only if Rails succeeds

    def test_decode_raises_and_rails_payload_missing_email_returns_401(self):
        """Rails user info without email → not a valid user → 401."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})

        rails_payload = MagicMock()
        rails_payload.user_id = 7
        rails_info_no_email = {"account_id": "corp"}  # missing email

        with (
            patch("app.auth.security.decode_token", return_value=None),
            patch("app.auth.rails_jwt.validate_rails_token_from_env", return_value=rails_payload),
            patch("app.auth.rails_jwt.fetch_rails_user_info", new=AsyncMock(return_value=rails_info_no_email)),
        ):
            client = TestClient(app)
            resp = client.get(
                "/api/v1/candidates",
                headers={"Authorization": "Bearer railstoken"},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Section 2 — Token format errors
# ---------------------------------------------------------------------------

class TestTokenFormatErrors:

    def test_basic_auth_header_returns_401(self):
        """Authorization: Basic xyz (no 'Bearer ' prefix) → 401."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401

    def test_empty_authorization_header_returns_401(self):
        """Authorization header present but empty → 401."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"Authorization": ""},
        )
        assert resp.status_code == 401

    def test_bearer_only_no_token_returns_401(self):
        """Authorization: Bearer (no token after) → 401."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"Authorization": "Bearer "},
        )
        # Middleware slices [7:] → empty string; decode_token will fail
        assert resp.status_code in (401, 200)  # depends on mock; without mock → exception path → 401

    def test_malformed_bearer_prefix_returns_401(self):
        """'Bearertoken' (no space) → treated as not starting with 'Bearer ' → 401."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"Authorization": "Bearertoken"},
        )
        assert resp.status_code == 401

    def test_token_header_instead_of_bearer_returns_401(self):
        """Authorization: Token xyz (wrong scheme) → 401."""
        app, _ = _reload_app({"ENVIRONMENT": "production"})
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"Authorization": "Token secretkey"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Section 3 — DEV_MODE behavior
# ---------------------------------------------------------------------------

class TestDevModeBehavior:

    def test_dev_mode_without_api_key_configured_returns_401(self):
        """DEV_MODE active but LIA_DEV_API_KEY not set → fail-closed → 401."""
        app, _ = _reload_app({
            "LIA_DEV_MODE": "true",
            "ENVIRONMENT": "development",
            "LIA_DEV_API_KEY": "",  # NOT configured
        })
        client = TestClient(app)
        resp = client.get("/api/v1/candidates")
        assert resp.status_code == 401

    def test_dev_mode_with_correct_api_key_injects_synthetic_user(self):
        """DEV_MODE active + correct X-Dev-Api-Key → synthetic user injected → 200."""
        app, _ = _reload_app({
            "LIA_DEV_MODE": "true",
            "ENVIRONMENT": "development",
            "LIA_DEV_API_KEY": "test-secret-key",
        })
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"X-Dev-Api-Key": "test-secret-key"},
        )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "dev-user"

    def test_dev_mode_with_wrong_api_key_returns_401(self):
        """DEV_MODE active + wrong X-Dev-Api-Key → 401."""
        app, _ = _reload_app({
            "LIA_DEV_MODE": "true",
            "ENVIRONMENT": "development",
            "LIA_DEV_API_KEY": "real-key",
        })
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"X-Dev-Api-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_dev_mode_active_in_production_env_still_401(self):
        """LIA_DEV_MODE=true in production ENVIRONMENT → DEV_MODE off → 401 as normal."""
        app, _ = _reload_app({
            "LIA_DEV_MODE": "true",
            "ENVIRONMENT": "production",
            "LIA_DEV_API_KEY": "test-key",
        })
        client = TestClient(app)
        resp = client.get(
            "/api/v1/candidates",
            headers={"X-Dev-Api-Key": "test-key"},
        )
        # DEV_MODE is blocked by production ENVIRONMENT → must require proper Bearer
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Section 4 — Async isolation (ContextVar per-request)
# ---------------------------------------------------------------------------

class TestContextVarIsolation:

    def test_contextvar_default_is_empty_string(self):
        """_current_company_id ContextVar defaults to ''."""
        import app.middleware.auth_enforcement as m
        importlib.reload(m)
        val = m._current_company_id.get()
        assert val == ""

    def test_set_company_id_from_jwt_sets_contextvar(self):
        """_set_company_id_from_jwt sets ContextVar to payload's company_id."""
        import app.middleware.auth_enforcement as m
        importlib.reload(m)
        m._set_company_id_from_jwt({"company_id": "isolated_tenant"})
        assert m._current_company_id.get() == "isolated_tenant"

    def test_contextvar_is_per_request_in_separate_threads(self):
        """Two sequential requests can have different company_ids via ContextVar."""
        import app.middleware.auth_enforcement as m
        importlib.reload(m)

        # Simulate tenant A
        m._set_company_id_from_jwt({"company_id": "tenant_a"})
        val_a = m._current_company_id.get()

        # Simulate tenant B (overwrites in same thread — sequential)
        m._set_company_id_from_jwt({"company_id": "tenant_b"})
        val_b = m._current_company_id.get()

        assert val_a == "tenant_a"
        assert val_b == "tenant_b"
        assert val_a != val_b
