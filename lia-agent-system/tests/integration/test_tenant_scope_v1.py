"""
Integration Tests — Tenant scope for pipeline_prediction and user_agent_preferences.

Verifica que os endpoints adicionados em P0 rejeitam:
- Acesso sem autenticação → 401
- Acesso cross-tenant (company_id de outro tenant) → 403
- Acesso same-tenant → 200 (funciona normalmente)

Endpoints cobertos:
  GET /pipeline-prediction                  (get_vacancy_prediction)
  GET /pipeline-prediction/company-overview (get_company_overview)
  GET /user-preferences/agent               (list_user_preferences)
  POST /user-preferences/agent              (upsert_preference)
  GET /user-preferences/agent/check         (check_auto_confirm)
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.auth.dependencies import (
    get_current_user_or_demo,
    validate_company_access,
)
from app.auth.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(company_id: str, role: str = "user") -> MagicMock:
    """Create a User-like mock for dependency injection."""
    u = MagicMock(spec=User)
    u.id = f"user-{company_id}"
    u.email = f"user@{company_id}.test"
    u.company_id = company_id
    u.role = role
    u.is_active = True
    u.can_access_company = lambda cid: cid == company_id
    return u


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline_app():
    """FastAPI app with only the pipeline_prediction router."""
    from app.api.v1.pipeline_prediction import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def prefs_app():
    """FastAPI app with only the user_agent_preferences router."""
    from app.api.v1.user_agent_preferences import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


# ---------------------------------------------------------------------------
# Section 1 — pipeline_prediction: GET /pipeline-prediction
# ---------------------------------------------------------------------------

class TestPipelinePredictionVacancy:
    """Tests for GET /api/v1/pipeline-prediction (get_vacancy_prediction)."""

    def test_no_auth_returns_401(self, pipeline_app):
        """Request without Authorization header must return 401 (production mode)."""
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(pipeline_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/pipeline-prediction",
                params={"vacancy_id": "vac-1", "company_id": "company-A"},
            )
        assert response.status_code == 401, (
            f"Expected 401 without auth, got {response.status_code}: {response.text}"
        )

    def test_cross_tenant_returns_403(self, pipeline_app):
        """Token for company-A must not access data for company-B."""
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/pipeline-prediction",
            params={"vacancy_id": "vac-1", "company_id": "company-B"},
        )
        assert response.status_code == 403, (
            f"Expected 403 for cross-tenant access, got {response.status_code}: {response.text}"
        )
        pipeline_app.dependency_overrides.clear()

    def test_same_tenant_calls_service(self, pipeline_app):
        """Same-tenant request must reach the service and return 200."""
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        mock_result = {
            "closure_probability": 75,
            "estimated_days_to_close": 14,
            "confidence_level": "high",
        }

        with patch(
            "app.api.v1.pipeline_prediction.pipeline_prediction_service"
                ".get_vacancy_prediction",
            new=AsyncMock(return_value=mock_result),
        ):
            client = TestClient(pipeline_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/pipeline-prediction",
                params={"vacancy_id": "vac-1", "company_id": "company-A"},
            )

        assert response.status_code == 200, (
            f"Expected 200 for same-tenant, got {response.status_code}: {response.text}"
        )
        assert response.json()["closure_probability"] == 75
        pipeline_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 2 — pipeline_prediction: GET /pipeline-prediction/company-overview
# ---------------------------------------------------------------------------

class TestPipelinePredictionCompanyOverview:
    """Tests for GET /api/v1/pipeline-prediction/company-overview."""

    def test_no_auth_returns_401(self, pipeline_app):
        """Request without Authorization header must return 401 (production mode)."""
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(pipeline_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/pipeline-prediction/company-overview",
                params={"company_id": "company-A"},
            )
        assert response.status_code == 401, (
            f"Expected 401 without auth, got {response.status_code}: {response.text}"
        )

    def test_cross_tenant_returns_403(self, pipeline_app):
        """Token for company-A must not access overview of company-B."""
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/pipeline-prediction/company-overview",
            params={"company_id": "company-B"},
        )
        assert response.status_code == 403, (
            f"Expected 403 for cross-tenant, got {response.status_code}: {response.text}"
        )
        pipeline_app.dependency_overrides.clear()

    def test_same_tenant_calls_service(self, pipeline_app):
        """Same-tenant request must reach the service and return 200."""
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        mock_result = {
            "vacancies": [],
            "summary": {
                "total_active_vacancies": 0,
                "at_risk_count": 0,
                "near_closure_count": 0,
                "avg_closure_probability": 0,
            },
        }

        with patch(
            "app.api.v1.pipeline_prediction.pipeline_prediction_service"
                ".get_company_overview",
            new=AsyncMock(return_value=mock_result),
        ):
            client = TestClient(pipeline_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/pipeline-prediction/company-overview",
                params={"company_id": "company-A"},
            )

        assert response.status_code == 200, (
            f"Expected 200 for same-tenant, got {response.status_code}: {response.text}"
        )
        pipeline_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 3 — user_agent_preferences: GET /user-preferences/agent
# ---------------------------------------------------------------------------

class TestUserPreferencesListEndpoint:
    """Tests for GET /api/v1/user-preferences/agent."""

    def test_no_auth_returns_401(self, prefs_app):
        """Request without auth must return 401 (production mode)."""
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(prefs_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/user-preferences/agent",
                params={"user_id": "user-1", "company_id": "company-A"},
            )
        assert response.status_code == 401, (
            f"Expected 401 without auth, got {response.status_code}: {response.text}"
        )

    def test_cross_tenant_returns_403(self, prefs_app):
        """Token for company-A must not list preferences for company-B."""
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/user-preferences/agent",
            params={"user_id": "user-1", "company_id": "company-B"},
        )
        assert response.status_code == 403, (
            f"Expected 403 for cross-tenant, got {response.status_code}: {response.text}"
        )
        prefs_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, prefs_app):
        """Same-tenant request must call service and return 200."""
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        with patch(
            "app.api.v1.user_agent_preferences.UserAgentPreferenceService"
                ".list_user_preferences",
            new=AsyncMock(return_value=[]),
        ):
            client = TestClient(prefs_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/user-preferences/agent",
                params={"user_id": "user-1", "company_id": "company-A"},
            )

        assert response.status_code == 200, (
            f"Expected 200 for same-tenant, got {response.status_code}: {response.text}"
        )
        assert response.json() == []
        prefs_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 4 — user_agent_preferences: POST /user-preferences/agent
# ---------------------------------------------------------------------------

class TestUserPreferencesUpsertEndpoint:
    """Tests for POST /api/v1/user-preferences/agent."""

    def test_no_auth_returns_401(self, prefs_app):
        """Request without auth must return 401 (production mode)."""
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(prefs_app, raise_server_exceptions=False)
            response = client.post(
                "/api/v1/user-preferences/agent",
                json={
                    "user_id": "user-1",
                    "company_id": "company-A",
                    "domain": "interview",
                    "action_type": "schedule",
                    "auto_confirm": True,
                },
            )
        assert response.status_code == 401, (
            f"Expected 401 without auth, got {response.status_code}: {response.text}"
        )

    def test_cross_tenant_returns_403(self, prefs_app):
        """Body company_id from other tenant must return 403."""
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/user-preferences/agent",
            json={
                "user_id": "user-1",
                "company_id": "company-B",  # cross-tenant
                "domain": "interview",
                "action_type": "schedule",
                "auto_confirm": True,
            },
        )
        assert response.status_code == 403, (
            f"Expected 403 for cross-tenant body, got {response.status_code}: {response.text}"
        )
        prefs_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, prefs_app):
        """Same-tenant POST must call service and return 200."""
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        mock_pref = MagicMock()
        mock_pref.id = "pref-uuid-1"
        mock_pref.user_id = "user-1"
        mock_pref.company_id = "company-A"
        mock_pref.domain = "interview"
        mock_pref.action_type = "schedule"
        mock_pref.auto_confirm = True
        mock_pref.updated_at = None

        with patch(
            "app.api.v1.user_agent_preferences.UserAgentPreferenceService.upsert",
            new=AsyncMock(return_value=mock_pref),
        ):
            client = TestClient(prefs_app, raise_server_exceptions=False)
            response = client.post(
                "/api/v1/user-preferences/agent",
                json={
                    "user_id": "user-1",
                    "company_id": "company-A",
                    "domain": "interview",
                    "action_type": "schedule",
                    "auto_confirm": True,
                },
            )

        assert response.status_code == 200, (
            f"Expected 200 for same-tenant, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert data["company_id"] == "company-A"
        assert data["auto_confirm"] is True
        prefs_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 5 — user_agent_preferences: GET /user-preferences/agent/check
# ---------------------------------------------------------------------------

class TestUserPreferencesCheckEndpoint:
    """Tests for GET /api/v1/user-preferences/agent/check."""

    def test_no_auth_returns_401(self, prefs_app):
        """Request without auth must return 401 (production mode)."""
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(prefs_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/user-preferences/agent/check",
                params={
                    "user_id": "user-1",
                    "company_id": "company-A",
                    "domain": "interview",
                    "action_type": "schedule",
                },
            )
        assert response.status_code == 401, (
            f"Expected 401 without auth, got {response.status_code}: {response.text}"
        )

    def test_cross_tenant_returns_403(self, prefs_app):
        """Token for company-A must not check preferences for company-B."""
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/user-preferences/agent/check",
            params={
                "user_id": "user-1",
                "company_id": "company-B",
                "domain": "interview",
                "action_type": "schedule",
            },
        )
        assert response.status_code == 403, (
            f"Expected 403 for cross-tenant, got {response.status_code}: {response.text}"
        )
        prefs_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, prefs_app):
        """Same-tenant check must call service and return 200."""
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        with patch(
            "app.api.v1.user_agent_preferences.UserAgentPreferenceService"
                ".check_auto_confirm",
            new=AsyncMock(return_value=False),
        ):
            client = TestClient(prefs_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/user-preferences/agent/check",
                params={
                    "user_id": "user-1",
                    "company_id": "company-A",
                    "domain": "interview",
                    "action_type": "schedule",
                },
            )

        assert response.status_code == 200, (
            f"Expected 200 for same-tenant, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert data["company_id"] == "company-A"
        assert data["auto_confirm"] is False
        prefs_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 6 — Unit contract: validate_company_access raises 403 cross-tenant
# ---------------------------------------------------------------------------

class TestValidateCompanyAccessContract:
    """Unit tests ensuring the auth guard contract holds for both modules."""

    def test_cross_tenant_raises_403(self):
        """validate_company_access must raise HTTP 403 for mismatched company."""
        user = _user("company-A")
        with pytest.raises(HTTPException) as exc_info:
            validate_company_access(user, "company-B")
        assert exc_info.value.status_code == 403

    def test_same_tenant_does_not_raise(self):
        """validate_company_access must not raise for matching company."""
        user = _user("company-A")
        # Should complete without raising
        validate_company_access(user, "company-A")

    def test_cross_tenant_isolation_matrix(self):
        """Full 3×3 matrix: every cross-tenant combination raises 403."""
        companies = ["tenant-X", "tenant-Y", "tenant-Z"]
        for my_company in companies:
            user = _user(my_company)
            for other in companies:
                if other == my_company:
                    validate_company_access(user, other)  # must not raise
                else:
                    with pytest.raises(HTTPException) as exc_info:
                        validate_company_access(user, other)
                    assert exc_info.value.status_code == 403, (
                        f"{my_company} → {other} should be 403, "
                        f"got {exc_info.value.status_code}"
                    )
