"""
Integration Tests — Tenant scope for v1 API endpoints.

Verifica que os endpoints rejeitam:
- Acesso sem autenticação → 401
- Acesso cross-tenant (company_id de outro tenant) → 403
- Acesso same-tenant → 200 (funciona normalmente)
- Falta de company_id obrigatório → 422
- company_id mal formatado → 422 ou 403

Endpoints cobertos:
  pipeline_prediction:
    GET  /pipeline-prediction
    GET  /pipeline-prediction/company-overview
  user_agent_preferences:
    GET  /user-preferences/agent
    POST /user-preferences/agent
    GET  /user-preferences/agent/check
  interview_analysis:
    POST /interview-analysis/analyze/{interview_id}
    POST /interview-analysis/analyze-transcript
    GET  /interview-analysis/status/{interview_id}        (lookup-then-check)
    GET  /interview-analysis/results/{interview_id}       (lookup-then-check)
  company_culture_config:
    GET  /company/culture-values
    POST /company/culture-values
    PUT  /company/culture-values/{value_id}                (lookup-then-check)
    GET  /company/ideal-profiles
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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


VALID_UUID_A = "11111111-1111-1111-1111-111111111111"
VALID_UUID_B = "22222222-2222-2222-2222-222222222222"


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


@pytest.fixture
def interview_app():
    """FastAPI app with only the interview_analysis router."""
    from app.api.v1.interview_analysis import router
    from app.core.database import get_db
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    return app


@pytest.fixture
def culture_app():
    """FastAPI app with only the company_culture_config router."""
    from app.api.v1.company_culture_config import router
    from app.domains.company.dependencies import (
        get_culture_value_repo,
        get_ideal_profile_repo,
    )
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_culture_value_repo] = lambda: MagicMock()
    app.dependency_overrides[get_ideal_profile_repo] = lambda: MagicMock()
    return app


# ---------------------------------------------------------------------------
# Section 1 — pipeline_prediction: GET /pipeline-prediction
# ---------------------------------------------------------------------------

class TestPipelinePredictionVacancy:
    """Tests for GET /api/v1/pipeline-prediction (get_vacancy_prediction)."""

    def test_no_auth_returns_401(self, pipeline_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(pipeline_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/pipeline-prediction",
                params={"vacancy_id": "vac-1", "company_id": "company-A"},
            )
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, pipeline_app):
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/pipeline-prediction",
            params={"vacancy_id": "vac-1"},
        )
        assert response.status_code == 422
        pipeline_app.dependency_overrides.clear()

    def test_invalid_company_id_format_returns_422_or_403(self, pipeline_app):
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/pipeline-prediction",
            params={"vacancy_id": "vac-1", "company_id": "not-a-uuid"},
        )
        assert response.status_code in (403, 422)
        pipeline_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, pipeline_app):
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/pipeline-prediction",
            params={"vacancy_id": "vac-1", "company_id": "company-B"},
        )
        assert response.status_code == 403
        pipeline_app.dependency_overrides.clear()

    def test_same_tenant_calls_service(self, pipeline_app):
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
        assert response.status_code == 200
        assert response.json()["closure_probability"] == 75
        pipeline_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 2 — pipeline_prediction: GET /pipeline-prediction/company-overview
# ---------------------------------------------------------------------------

class TestPipelinePredictionCompanyOverview:
    """Tests for GET /api/v1/pipeline-prediction/company-overview."""

    def test_no_auth_returns_401(self, pipeline_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(pipeline_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/pipeline-prediction/company-overview",
                params={"company_id": "company-A"},
            )
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, pipeline_app):
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get("/api/v1/pipeline-prediction/company-overview")
        assert response.status_code == 422
        pipeline_app.dependency_overrides.clear()

    def test_invalid_company_id_format_returns_422_or_403(self, pipeline_app):
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/pipeline-prediction/company-overview",
            params={"company_id": "not-a-uuid"},
        )
        assert response.status_code in (403, 422)
        pipeline_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, pipeline_app):
        user_a = _user("company-A")
        pipeline_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(pipeline_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/pipeline-prediction/company-overview",
            params={"company_id": "company-B"},
        )
        assert response.status_code == 403
        pipeline_app.dependency_overrides.clear()

    def test_same_tenant_calls_service(self, pipeline_app):
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
        assert response.status_code == 200
        pipeline_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 3 — user_agent_preferences: GET /user-preferences/agent
# ---------------------------------------------------------------------------

class TestUserPreferencesListEndpoint:
    """Tests for GET /api/v1/user-preferences/agent."""

    def test_no_auth_returns_401(self, prefs_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(prefs_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/user-preferences/agent",
                params={"user_id": "user-1", "company_id": "company-A"},
            )
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, prefs_app):
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/user-preferences/agent",
            params={"user_id": "user-1"},
        )
        assert response.status_code == 422
        prefs_app.dependency_overrides.clear()

    def test_invalid_company_id_format_returns_422_or_403(self, prefs_app):
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/user-preferences/agent",
            params={"user_id": "user-1", "company_id": "not-a-uuid"},
        )
        assert response.status_code in (403, 422)
        prefs_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, prefs_app):
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/user-preferences/agent",
            params={"user_id": "user-1", "company_id": "company-B"},
        )
        assert response.status_code == 403
        prefs_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, prefs_app):
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
        assert response.status_code == 200
        assert response.json() == []
        prefs_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 4 — user_agent_preferences: POST /user-preferences/agent
# ---------------------------------------------------------------------------

class TestUserPreferencesUpsertEndpoint:
    """Tests for POST /api/v1/user-preferences/agent."""

    def test_no_auth_returns_401(self, prefs_app):
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
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, prefs_app):
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/user-preferences/agent",
            json={
                "user_id": "user-1",
                "domain": "interview",
                "action_type": "schedule",
                "auto_confirm": True,
            },
        )
        assert response.status_code == 422
        prefs_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, prefs_app):
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/user-preferences/agent",
            json={
                "user_id": "user-1",
                "company_id": "company-B",
                "domain": "interview",
                "action_type": "schedule",
                "auto_confirm": True,
            },
        )
        assert response.status_code == 403
        prefs_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, prefs_app):
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
        assert response.status_code == 200
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
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, prefs_app):
        user_a = _user("company-A")
        prefs_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(prefs_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/user-preferences/agent/check",
            params={
                "user_id": "user-1",
                "domain": "interview",
                "action_type": "schedule",
            },
        )
        assert response.status_code == 422
        prefs_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, prefs_app):
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
        assert response.status_code == 403
        prefs_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, prefs_app):
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
        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == "company-A"
        assert data["auto_confirm"] is False
        prefs_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 6 — interview_analysis
# ---------------------------------------------------------------------------

def _patch_interview_repo(interview_obj=None):
    """Factory: patches InterviewAnalysisRepository class to return a controlled instance."""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_interview_by_id = AsyncMock(return_value=interview_obj)
    mock_repo_instance.update_interview_feedback = AsyncMock(return_value=None)
    mock_repo_instance.deactivate_current_opinions = AsyncMock(return_value=None)
    return patch(
        "app.api.v1.interview_analysis.InterviewAnalysisRepository",
        return_value=mock_repo_instance,
    )


class TestInterviewAnalysisAnalyze:
    """Tests for POST /api/v1/interview-analysis/analyze/{interview_id}."""

    def test_no_auth_returns_401(self, interview_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.post(
                "/api/v1/interview-analysis/analyze/1",
                params={"company_id": "company-A"},
            )
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(interview_app, raise_server_exceptions=False)
        response = client.post("/api/v1/interview-analysis/analyze/1")
        assert response.status_code == 422
        interview_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(interview_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/interview-analysis/analyze/1",
            params={"company_id": "company-B"},
        )
        assert response.status_code == 403
        interview_app.dependency_overrides.clear()


class TestInterviewAnalysisAnalyzeTranscript:
    """Tests for POST /api/v1/interview-analysis/analyze-transcript."""

    def test_no_auth_returns_401(self, interview_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.post(
                "/api/v1/interview-analysis/analyze-transcript",
                params={"company_id": "company-A"},
                json={
                    "transcript_text": "x" * 200,
                    "candidate_id": "cand-1",
                    "interview_type": "technical",
                },
            )
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(interview_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/interview-analysis/analyze-transcript",
            json={
                "transcript_text": "x" * 200,
                "candidate_id": "cand-1",
                "interview_type": "technical",
            },
        )
        assert response.status_code == 422
        interview_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(interview_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/interview-analysis/analyze-transcript",
            params={"company_id": "company-B"},
            json={
                "transcript_text": "x" * 200,
                "candidate_id": "cand-1",
                "interview_type": "technical",
            },
        )
        assert response.status_code == 403
        interview_app.dependency_overrides.clear()


class TestInterviewAnalysisStatus:
    """Tests for GET /api/v1/interview-analysis/status/{interview_id} (lookup-then-check)."""

    def test_no_auth_returns_401(self, interview_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.get("/api/v1/interview-analysis/status/1")
        assert response.status_code == 401

    def test_resource_not_found_returns_404(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        with _patch_interview_repo(interview_obj=None):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.get("/api/v1/interview-analysis/status/1")
        assert response.status_code == 404
        interview_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, interview_app):
        """Repo returns interview belonging to company-B; user from company-A → 403."""
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        mock_interview = MagicMock()
        mock_interview.company_id = "company-B"
        mock_interview.feedback = {}
        mock_interview.status = "completed"
        with _patch_interview_repo(interview_obj=mock_interview):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.get("/api/v1/interview-analysis/status/1")
        assert response.status_code == 403
        interview_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        mock_interview = MagicMock()
        mock_interview.company_id = "company-A"
        mock_interview.feedback = {}
        mock_interview.status = "scheduled"
        with _patch_interview_repo(interview_obj=mock_interview):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.get("/api/v1/interview-analysis/status/1")
        assert response.status_code == 200
        data = response.json()
        assert data["interview_id"] == "1"
        interview_app.dependency_overrides.clear()


class TestInterviewAnalysisResults:
    """Tests for GET /api/v1/interview-analysis/results/{interview_id} (lookup-then-check)."""

    def test_no_auth_returns_401(self, interview_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.get("/api/v1/interview-analysis/results/1")
        assert response.status_code == 401

    def test_resource_not_found_returns_404(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        with _patch_interview_repo(interview_obj=None):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.get("/api/v1/interview-analysis/results/1")
        assert response.status_code == 404
        interview_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, interview_app):
        user_a = _user("company-A")
        interview_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        mock_interview = MagicMock()
        mock_interview.company_id = "company-B"
        mock_interview.feedback = {"wsi_analysis": {"overall": 8}}
        with _patch_interview_repo(interview_obj=mock_interview):
            client = TestClient(interview_app, raise_server_exceptions=False)
            response = client.get("/api/v1/interview-analysis/results/1")
        assert response.status_code == 403
        interview_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 8 — company_culture_config
# ---------------------------------------------------------------------------

class TestCultureValuesList:
    """Tests for GET /api/v1/company/culture-values."""

    def test_no_auth_returns_401(self, culture_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(culture_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/company/culture-values",
                params={"company_id": VALID_UUID_A},
            )
        assert response.status_code == 401

    def test_invalid_company_id_format_returns_422_or_403(self, culture_app):
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/company/culture-values",
            params={"company_id": "not-a-uuid"},
        )
        assert response.status_code in (403, 422)
        culture_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, culture_app):
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/company/culture-values",
            params={"company_id": VALID_UUID_B},
        )
        assert response.status_code == 403
        culture_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, culture_app):
        from app.domains.company.dependencies import get_culture_value_repo
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        cv_repo = MagicMock()
        cv_repo.list_for_company = AsyncMock(return_value=[])
        culture_app.dependency_overrides[get_culture_value_repo] = lambda: cv_repo
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/company/culture-values",
            params={"company_id": VALID_UUID_A},
        )
        assert response.status_code == 200
        culture_app.dependency_overrides.clear()


class TestCultureValuesCreate:
    """Tests for POST /api/v1/company/culture-values (company_id is Query, not body)."""

    def test_no_auth_returns_401(self, culture_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(culture_app, raise_server_exceptions=False)
            response = client.post(
                "/api/v1/company/culture-values",
                params={"company_id": VALID_UUID_A},
                json={"name": "Innovation"},
            )
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, culture_app):
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/company/culture-values",
            json={"name": "Innovation"},
        )
        assert response.status_code == 422
        culture_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, culture_app):
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/company/culture-values",
            params={"company_id": VALID_UUID_B},
            json={"name": "Innovation"},
        )
        assert response.status_code == 403
        culture_app.dependency_overrides.clear()


class TestCultureValuesUpdate:
    """Tests for PUT /api/v1/company/culture-values/{value_id} (lookup-then-check)."""

    def test_no_auth_returns_401(self, culture_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(culture_app, raise_server_exceptions=False)
            response = client.put(
                f"/api/v1/company/culture-values/{VALID_UUID_A}",
                json={"name": "Updated"},
            )
        assert response.status_code == 401

    def test_resource_not_found_returns_404(self, culture_app):
        from app.domains.company.dependencies import get_culture_value_repo
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        cv_repo = MagicMock()
        cv_repo.get_by_id = AsyncMock(return_value=None)
        culture_app.dependency_overrides[get_culture_value_repo] = lambda: cv_repo
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.put(
            f"/api/v1/company/culture-values/{VALID_UUID_A}",
            json={"name": "Updated"},
        )
        assert response.status_code == 404
        culture_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, culture_app):
        from app.domains.company.dependencies import get_culture_value_repo
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        existing = MagicMock()
        existing.company_id = VALID_UUID_B
        cv_repo = MagicMock()
        cv_repo.get_by_id = AsyncMock(return_value=existing)
        culture_app.dependency_overrides[get_culture_value_repo] = lambda: cv_repo
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.put(
            f"/api/v1/company/culture-values/{VALID_UUID_A}",
            json={"name": "Updated"},
        )
        assert response.status_code == 403
        culture_app.dependency_overrides.clear()


class TestIdealProfilesList:
    """Tests for GET /api/v1/company/ideal-profiles."""

    def test_no_auth_returns_401(self, culture_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(culture_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/company/ideal-profiles",
                params={"company_id": VALID_UUID_A},
            )
        assert response.status_code == 401

    def test_invalid_company_id_format_returns_422_or_403(self, culture_app):
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/company/ideal-profiles",
            params={"company_id": "not-a-uuid"},
        )
        assert response.status_code in (403, 422)
        culture_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, culture_app):
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/company/ideal-profiles",
            params={"company_id": VALID_UUID_B},
        )
        assert response.status_code == 403
        culture_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, culture_app):
        from app.domains.company.dependencies import get_ideal_profile_repo
        user_a = _user(VALID_UUID_A)
        culture_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        ip_repo = MagicMock()
        ip_repo.list_for_company = AsyncMock(return_value=[])
        culture_app.dependency_overrides[get_ideal_profile_repo] = lambda: ip_repo
        client = TestClient(culture_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/company/ideal-profiles",
            params={"company_id": VALID_UUID_A},
        )
        assert response.status_code == 200
        culture_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 9 — settings_progress (Onda 36 P0 fix)
# ---------------------------------------------------------------------------

@pytest.fixture
def settings_progress_app():
    """FastAPI app with only the settings_progress router."""
    from app.api.v1.settings_progress import router
    from app.core.database import get_db
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    return app


class TestSettingsProgressTenantScope:
    """
    Onda 36 fix — settings_progress.py was ignoring `company_id` query param
    and always loading default company (tenant bypass). Now uses current_user.company_id.
    """

    def test_no_auth_returns_401(self, settings_progress_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(settings_progress_app, raise_server_exceptions=False)
            response = client.get("/api/v1/settings/progress")
        assert response.status_code == 401

    def test_no_query_param_uses_user_company(self, settings_progress_app):
        """Sem query param: usa current_user.company_id (canonical)."""
        user_a = _user(VALID_UUID_A)
        settings_progress_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        mock_repo = MagicMock()
        mock_repo.get_company_by_id = AsyncMock(return_value=None)
        mock_repo.get_default_company = AsyncMock(return_value=None)

        with patch(
            "app.api.v1.settings_progress.SettingsProgressRepository",
            return_value=mock_repo,
        ):
            client = TestClient(settings_progress_app, raise_server_exceptions=False)
            response = client.get("/api/v1/settings/progress")

        assert response.status_code == 200
        # Critical: must have called get_company_by_id with user's company, NOT get_default_company
        mock_repo.get_company_by_id.assert_called_once_with(VALID_UUID_A)
        mock_repo.get_default_company.assert_not_called()
        settings_progress_app.dependency_overrides.clear()

    def test_cross_tenant_query_returns_403(self, settings_progress_app):
        """Passar company_id de outro tenant na query → 403."""
        user_a = _user(VALID_UUID_A)
        settings_progress_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(settings_progress_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/settings/progress",
            params={"company_id": VALID_UUID_B},
        )
        assert response.status_code == 403
        settings_progress_app.dependency_overrides.clear()

    def test_same_tenant_query_uses_provided_id(self, settings_progress_app):
        """Query company_id == user.company_id: usa o id provido."""
        user_a = _user(VALID_UUID_A)
        settings_progress_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        mock_repo = MagicMock()
        mock_repo.get_company_by_id = AsyncMock(return_value=None)

        with patch(
            "app.api.v1.settings_progress.SettingsProgressRepository",
            return_value=mock_repo,
        ):
            client = TestClient(settings_progress_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/settings/progress",
                params={"company_id": VALID_UUID_A},
            )
        assert response.status_code == 200
        mock_repo.get_company_by_id.assert_called_once_with(VALID_UUID_A)
        settings_progress_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 10 — integrations_hub (Onda 36 P0 fix)
# ---------------------------------------------------------------------------

@pytest.fixture
def integrations_hub_app():
    """FastAPI app with only the integrations_hub router."""
    from app.api.v1.integrations_hub import router
    from app.domains.integrations_hub.dependencies import get_integrations_hub_repo
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_integrations_hub_repo] = lambda: MagicMock()
    return app


class TestIntegrationsHubListConnections:
    """GET /api/v1/integrations/connections — Onda 36 fix."""

    def test_no_auth_returns_401(self, integrations_hub_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(integrations_hub_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/integrations/connections",
                params={"company_id": VALID_UUID_A},
            )
        assert response.status_code == 401

    def test_no_company_id_returns_422(self, integrations_hub_app):
        user_a = _user(VALID_UUID_A)
        integrations_hub_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(integrations_hub_app, raise_server_exceptions=False)
        response = client.get("/api/v1/integrations/connections")
        assert response.status_code == 422
        integrations_hub_app.dependency_overrides.clear()

    def test_cross_tenant_returns_403(self, integrations_hub_app):
        user_a = _user(VALID_UUID_A)
        integrations_hub_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(integrations_hub_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/integrations/connections",
            params={"company_id": VALID_UUID_B},
        )
        assert response.status_code == 403
        integrations_hub_app.dependency_overrides.clear()

    def test_same_tenant_returns_200(self, integrations_hub_app):
        user_a = _user(VALID_UUID_A)
        integrations_hub_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a

        mock_repo = MagicMock()
        mock_repo.list_connections = AsyncMock(return_value=[])
        integrations_hub_app.dependency_overrides[
            __import__("app.domains.integrations_hub.dependencies", fromlist=["get_integrations_hub_repo"]).get_integrations_hub_repo
        ] = lambda: mock_repo

        client = TestClient(integrations_hub_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/integrations/connections",
            params={"company_id": VALID_UUID_A},
        )
        assert response.status_code == 200
        assert response.json() == []
        integrations_hub_app.dependency_overrides.clear()


class TestIntegrationsHubCreateConnection:
    """POST /api/v1/integrations/connections — Onda 36 fix (body company_id)."""

    def test_no_auth_returns_401(self, integrations_hub_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(integrations_hub_app, raise_server_exceptions=False)
            response = client.post(
                "/api/v1/integrations/connections",
                json={
                    "provider_id": "prov-1",
                    "company_id": VALID_UUID_A,
                    "auth_type": "api_key",
                },
            )
        assert response.status_code == 401

    def test_cross_tenant_body_returns_403(self, integrations_hub_app):
        """Body com company_id de outro tenant → 403."""
        user_a = _user(VALID_UUID_A)
        integrations_hub_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(integrations_hub_app, raise_server_exceptions=False)
        response = client.post(
            "/api/v1/integrations/connections",
            json={
                "provider_id": "prov-1",
                "company_id": VALID_UUID_B,
                "auth_type": "api_key",
            },
        )
        assert response.status_code == 403
        integrations_hub_app.dependency_overrides.clear()


class TestIntegrationsHubHealth:
    """GET /api/v1/integrations/health — Onda 36 fix."""

    def test_no_auth_returns_401(self, integrations_hub_app):
        with patch("app.auth.dependencies._is_dev_environment", return_value=False):
            client = TestClient(integrations_hub_app, raise_server_exceptions=False)
            response = client.get(
                "/api/v1/integrations/health",
                params={"company_id": VALID_UUID_A},
            )
        assert response.status_code == 401

    def test_cross_tenant_returns_403(self, integrations_hub_app):
        user_a = _user(VALID_UUID_A)
        integrations_hub_app.dependency_overrides[get_current_user_or_demo] = lambda: user_a
        client = TestClient(integrations_hub_app, raise_server_exceptions=False)
        response = client.get(
            "/api/v1/integrations/health",
            params={"company_id": VALID_UUID_B},
        )
        assert response.status_code == 403
        integrations_hub_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Section 11 — Unit contract: validate_company_access
# ---------------------------------------------------------------------------

class TestValidateCompanyAccessContract:
    """Unit tests ensuring the auth guard contract holds for all modules."""

    def test_cross_tenant_raises_403(self):
        user = _user("company-A")
        with pytest.raises(HTTPException) as exc_info:
            validate_company_access(user, "company-B")
        assert exc_info.value.status_code == 403

    def test_same_tenant_does_not_raise(self):
        user = _user("company-A")
        validate_company_access(user, "company-A")

    def test_cross_tenant_isolation_matrix(self):
        companies = ["tenant-X", "tenant-Y", "tenant-Z"]
        for my_company in companies:
            user = _user(my_company)
            for other in companies:
                if other == my_company:
                    validate_company_access(user, other)
                else:
                    with pytest.raises(HTTPException) as exc_info:
                        validate_company_access(user, other)
                    assert exc_info.value.status_code == 403, (
                        f"{my_company} → {other} should be 403, "
                        f"got {exc_info.value.status_code}"
                    )
