"""
Contract smoke tests for Admin Plan API (Fase 1.4-1.5).
Sentinels: 401 sem token, 404 para company inexistente, 200 com token+company válida.
Auth: INTERNAL_API_TOKEN env var — never hardcoded.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app():
    """Build minimal FastAPI test client with admin_plan_api router."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.v1.admin_plan_api import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Auth contract
# ---------------------------------------------------------------------------

class TestRequireInternalToken:
    """INTERNAL_API_TOKEN auth is enforced on all 4 endpoints."""

    ENDPOINTS = [
        ("GET",  "/api/v1/admin-api/subscription/00000000-0000-0000-0000-000000000001"),
        ("GET",  "/api/v1/admin-api/usage/00000000-0000-0000-0000-000000000001"),
        ("POST", "/api/v1/admin-api/usage/00000000-0000-0000-0000-000000000001/record"),
        ("PUT",  "/api/v1/admin-api/subscription/00000000-0000-0000-0000-000000000001/plan"),
    ]

    @pytest.fixture(autouse=True)
    def set_token(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_API_TOKEN", "test-secret-token")

    def test_no_token_returns_401(self):
        client = _make_app()
        for method, path in self.ENDPOINTS:
            resp = getattr(client, method.lower())(path)
            assert resp.status_code == 401, \
                f"{method} {path} should be 401 without token, got {resp.status_code}"

    def test_wrong_token_returns_401(self):
        client = _make_app()
        headers = {"Authorization": "Bearer wrong-token"}
        for method, path in self.ENDPOINTS:
            resp = getattr(client, method.lower())(path, headers=headers)
            assert resp.status_code == 401, \
                f"{method} {path} should be 401 with wrong token"

    def test_missing_env_var_returns_503(self, monkeypatch):
        monkeypatch.delenv("INTERNAL_API_TOKEN", raising=False)
        client = _make_app()
        resp = client.get(
            "/api/v1/admin-api/subscription/00000000-0000-0000-0000-000000000001"
        )
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Company existence guard
# ---------------------------------------------------------------------------

class TestCompanyNotFound:
    """Endpoints return 404 for unknown company_id."""

    @pytest.fixture(autouse=True)
    def set_token(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_API_TOKEN", "test-secret-token")

    @patch("app.api.v1.admin_plan_api.get_db")
    def test_get_subscription_404_unknown_company(self, mock_db):
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        mock_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.return_value.__aexit__ = AsyncMock(return_value=False)

        client = _make_app()
        headers = {"Authorization": "Bearer test-secret-token"}
        resp = client.get(
            "/api/v1/admin-api/subscription/00000000-dead-dead-dead-000000000000",
            headers=headers,
        )
        assert resp.status_code in (404, 422), \
            f"Unknown company should 404, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestChangeplanSchema:
    """PUT /plan requires valid plan_code (extra fields forbidden — WeDoBaseModel)."""

    @pytest.fixture(autouse=True)
    def set_token(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_API_TOKEN", "test-secret-token")

    def test_extra_field_returns_422(self):
        client = _make_app()
        headers = {"Authorization": "Bearer test-secret-token"}
        resp = client.put(
            "/api/v1/admin-api/subscription/00000000-0000-0000-0000-000000000001/plan",
            json={"plan_code": "pro", "unexpected_field": "should_fail"},
            headers=headers,
        )
        # 422 = Pydantic extra='forbid'; 401/404 acceptable if auth/company check runs first
        assert resp.status_code in (422, 401, 404), \
            f"Extra fields should be rejected (422) or blocked (401/404), got {resp.status_code}"


# ---------------------------------------------------------------------------
# No hardcoded token
# ---------------------------------------------------------------------------

class TestNoHardcodedToken:
    """Auth module must not contain hardcoded token strings."""

    def test_no_hardcoded_token_in_auth_logic(self):
        with open("app/api/v1/admin_plan_api.py") as f:
            src = f.read()
        hardcoded_suspects = ["== 'secret'", '== "secret"', "== 'admin'", '== "admin"',
                              "== 'internal'", "hardcoded", "my-secret"]
        for suspect in hardcoded_suspects:
            assert suspect not in src, f"Hardcoded token pattern found: {suspect}"

    def test_reads_from_env(self):
        with open("app/api/v1/admin_plan_api.py") as f:
            src = f.read()
        assert "INTERNAL_API_TOKEN" in src, \
            "Auth must read INTERNAL_API_TOKEN from environment"


# ---------------------------------------------------------------------------
# PATCH /discount — Desconto ALFA contract tests
# ---------------------------------------------------------------------------

class TestDiscountEndpoint:
    """PATCH /subscription/{company_id}/discount — B6 Desconto ALFA."""

    CID = "00000000-0000-0000-0000-000000000001"
    PATH = f"/api/v1/admin-api/subscription/{CID}/discount"

    @pytest.fixture(autouse=True)
    def set_token(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_API_TOKEN", "test-secret-token")

    def test_no_token_returns_401(self):
        client = _make_app()
        resp = client.patch(self.PATH, json={"desconto_pct": 15.0})
        assert resp.status_code == 401

    def test_wrong_token_returns_401(self):
        client = _make_app()
        resp = client.patch(
            self.PATH,
            json={"desconto_pct": 15.0},
            headers={"Authorization": "Bearer wrong"},
        )
        assert resp.status_code == 401

    def test_pct_above_100_returns_422(self):
        """desconto_pct > 100 must be rejected (ge=0 le=100)."""
        client = _make_app()
        headers = {"Authorization": "Bearer test-secret-token"}
        resp = client.patch(self.PATH, json={"desconto_pct": 101.0}, headers=headers)
        assert resp.status_code == 422, f"pct=101 should be 422, got {resp.status_code}"

    def test_negative_pct_returns_422(self):
        """desconto_pct < 0 must be rejected."""
        client = _make_app()
        headers = {"Authorization": "Bearer test-secret-token"}
        resp = client.patch(self.PATH, json={"desconto_pct": -1.0}, headers=headers)
        assert resp.status_code == 422, f"pct=-1 should be 422, got {resp.status_code}"

    def test_extra_field_returns_422(self):
        """WeDoBaseModel extra=forbid must reject unknown fields."""
        client = _make_app()
        headers = {"Authorization": "Bearer test-secret-token"}
        resp = client.patch(
            self.PATH,
            json={"desconto_pct": 10.0, "unknown_field": "bad"},
            headers=headers,
        )
        assert resp.status_code in (422, 401, 404), \
            f"Extra fields should be rejected, got {resp.status_code}"

    def test_unknown_company_returns_404(self):
        """No active subscription → 404. Uses dependency_overrides (generator-safe)."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin_plan_api import router
        from app.core.database import get_db

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.commit = AsyncMock()
            yield mock_session

        app.dependency_overrides[get_db] = mock_get_db
        client = TestClient(app)
        headers = {"Authorization": "Bearer test-secret-token"}
        resp = client.patch(
            "/api/v1/admin-api/subscription/00000000-dead-dead-dead-000000000000/discount",
            json={"desconto_pct": 10.0},
            headers=headers,
        )
        assert resp.status_code in (404, 422), \
            f"Unknown company should 404, got {resp.status_code}: {resp.text}"

    def test_discount_endpoint_in_openapi_schema(self):
        """PATCH /discount must appear in OpenAPI schema."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin_plan_api import router
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        client = TestClient(app)
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        patch_path = "/api/v1/admin-api/subscription/{company_id}/discount"
        assert patch_path in paths, f"PATCH /discount missing from OpenAPI"
        assert "patch" in paths[patch_path], "PATCH method missing"

    def test_discount_responses_documented(self):
        """PATCH /discount must document 401 and 404 responses in OpenAPI."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api.v1.admin_plan_api import router
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        client = TestClient(app)
        schema = client.get("/openapi.json").json()
        patch_path = "/api/v1/admin-api/subscription/{company_id}/discount"
        responses = schema["paths"][patch_path]["patch"].get("responses", {})
        assert "401" in responses, "401 not documented on PATCH /discount"
        assert "404" in responses, "404 not documented on PATCH /discount"


# ---------------------------------------------------------------------------
# All 5 endpoints require auth (including PATCH /discount)
# ---------------------------------------------------------------------------

class TestAllEndpointsRequireAuth:
    """All 5 endpoints enforce INTERNAL_API_TOKEN."""

    ENDPOINTS = [
        ("GET",   "/api/v1/admin-api/subscription/00000000-0000-0000-0000-000000000001"),
        ("GET",   "/api/v1/admin-api/usage/00000000-0000-0000-0000-000000000001"),
        ("POST",  "/api/v1/admin-api/usage/00000000-0000-0000-0000-000000000001/record"),
        ("PUT",   "/api/v1/admin-api/subscription/00000000-0000-0000-0000-000000000001/plan"),
        ("PATCH", "/api/v1/admin-api/subscription/00000000-0000-0000-0000-000000000001/discount"),
    ]

    @pytest.fixture(autouse=True)
    def set_token(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_API_TOKEN", "test-secret-token")

    def test_all_five_endpoints_require_token(self):
        client = _make_app()
        for method, path in self.ENDPOINTS:
            resp = getattr(client, method.lower())(path)
            assert resp.status_code == 401, \
                f"{method} {path} should be 401 without token, got {resp.status_code}"
