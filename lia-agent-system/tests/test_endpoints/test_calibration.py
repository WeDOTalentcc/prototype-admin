"""
Tests for calibration endpoints — real production router with mocked services.

Mounts the actual router from app/api/v1/calibration.py.
The database session and CalibrationService are replaced with mocks so tests
run without a real PostgreSQL instance while still exercising the real endpoint
logic, Pydantic validation, HTTP routing, and status codes.

Coverage:
  200 — happy path for every route
  422 — missing required request fields (validated by real Pydantic schemas)
  404 — approve/reject for non-existent suggestion_id
  Static — response_model contracts defined in the production file
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared test app (module scope — created once for all tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def calib_app():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    from app.api.v1.calibration import router
    from app.core.database import get_db

    app = FastAPI()
    app.include_router(router)

    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    mock_session.query.return_value = mock_query
    app.dependency_overrides[get_db] = lambda: mock_session

    return app


# ---------------------------------------------------------------------------
# Service mock helpers
# ---------------------------------------------------------------------------

def _make_feedback_event():
    evt = MagicMock()
    evt.to_dict.return_value = {"id": "fb-001", "type": "explicit", "candidate_id": "cand-001"}
    return evt


def _make_suggestion(sid="suggestion-001"):
    sug = MagicMock()
    sug.id = sid
    sug.to_dict.return_value = {"id": sid, "status": "approved", "type": "weight_adjustment"}
    return sug


def _setup_mock_service(mock_cls, *, suggestion_id="suggestion-001"):
    """Configure a CalibrationService mock for all endpoints."""
    instance = mock_cls.return_value
    evt = _make_feedback_event()
    sug = _make_suggestion(suggestion_id)

    instance.record_explicit_feedback = AsyncMock(return_value=evt)
    instance.record_implicit_feedback = AsyncMock(return_value=evt)
    instance.record_post_hire_feedback = AsyncMock(return_value=evt)
    instance.get_divergences = AsyncMock(return_value=[])
    instance.get_calibration_stats = AsyncMock(return_value={"accuracy_rate": 0.82, "total": 42})
    instance.get_pending_suggestions = AsyncMock(return_value=[])
    instance.generate_suggestions = AsyncMock(return_value=[sug])
    instance.get_recent_events = AsyncMock(return_value=[])
    instance.get_weights = AsyncMock(return_value=[])

    async def approve(sid, user_id="system"):
        return _make_suggestion(sid) if sid == suggestion_id else None

    async def reject(sid, user_id="system", reason=None):
        return _make_suggestion(sid) if sid == suggestion_id else None

    instance.approve_suggestion = approve
    instance.reject_suggestion = reject
    return instance


# ---------------------------------------------------------------------------
# Calibration start
# ---------------------------------------------------------------------------

class TestCalibrationStart:
    def test_valid_request_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/start', json={
                "job_vacancy_id": "vac-001",
                "job_description": "Python developer"
            })
        assert resp.status_code == 200

    def test_response_has_session_id(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            body = client.post('/calibration/start', json={
                "job_vacancy_id": "vac-001",
                "job_description": "Python developer"
            }).json()
        assert "session_id" in body

    def test_missing_job_vacancy_id_returns_422(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/start', json={
                "job_description": "Python developer"
            })
        assert resp.status_code == 422

    def test_missing_job_description_returns_422(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/start', json={
                "job_vacancy_id": "vac-001"
            })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Explicit feedback
# ---------------------------------------------------------------------------

class TestExplicitFeedback:
    def test_valid_request_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/explicit', json={
                "candidate_id": "cand-001",
                "agrees_with_lia": True
            })
        assert resp.status_code == 200

    def test_response_success_is_true(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            body = client.post('/calibration/feedback/explicit', json={
                "candidate_id": "cand-001",
                "agrees_with_lia": True
            }).json()
        assert body.get("success") is True

    def test_missing_candidate_id_returns_422(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/explicit', json={
                "agrees_with_lia": True
            })
        assert resp.status_code == 422

    def test_missing_agrees_with_lia_returns_422(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/explicit', json={
                "candidate_id": "cand-001"
            })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Implicit feedback
# ---------------------------------------------------------------------------

class TestImplicitFeedback:
    def test_valid_request_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/implicit', json={
                "candidate_id": "cand-001",
                "job_id": "job-001",
                "action": "advance_stage"
            })
        assert resp.status_code == 200

    def test_missing_candidate_id_returns_422(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/implicit', json={
                "job_id": "job-001",
                "action": "advance_stage"
            })
        assert resp.status_code == 422

    def test_missing_action_returns_422(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/implicit', json={
                "candidate_id": "cand-001",
                "job_id": "job-001"
            })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Post-hire feedback
# ---------------------------------------------------------------------------

class TestPostHireFeedback:
    def test_valid_request_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/post-hire', json={
                "candidate_id": "cand-001",
                "job_id": "job-001",
                "success": True
            })
        assert resp.status_code == 200

    def test_missing_candidate_id_returns_422(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/post-hire', json={
                "job_id": "job-001",
                "success": True
            })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Divergences
# ---------------------------------------------------------------------------

class TestDivergences:
    def test_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.get('/calibration/divergences')
        assert resp.status_code == 200

    def test_response_has_success(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            body = client.get('/calibration/divergences').json()
        assert body.get("success") is True


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.get('/calibration/stats')
        assert resp.status_code == 200

    def test_response_has_success(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            body = client.get('/calibration/stats').json()
        assert body.get("success") is True


# ---------------------------------------------------------------------------
# Suggestions: list, generate, approve/reject
# ---------------------------------------------------------------------------

class TestSuggestions:
    def test_list_suggestions_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.get('/calibration/suggestions')
        assert resp.status_code == 200

    def test_generate_suggestions_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/suggestions/generate')
        assert resp.status_code == 200

    def test_approve_known_suggestion_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc, suggestion_id="suggestion-001")
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/suggestions/suggestion-001/approve')
        assert resp.status_code == 200

    def test_approve_unknown_suggestion_returns_404(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc, suggestion_id="suggestion-001")
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/suggestions/nonexistent-id/approve')
        assert resp.status_code == 404

    def test_reject_known_suggestion_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc, suggestion_id="suggestion-001")
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/suggestions/suggestion-001/reject',
                               json={"reason": "not relevant"})
        assert resp.status_code == 200

    def test_reject_unknown_suggestion_returns_404(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc, suggestion_id="suggestion-001")
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/suggestions/no-such/reject',
                               json={"reason": "n/a"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class TestEvents:
    def test_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.get('/calibration/events')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

class TestWeights:
    def test_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.get('/calibration/weights')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_returns_200(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.get('/calibration/dashboard')
        assert resp.status_code == 200

    def test_response_has_success(self, calib_app):
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            _setup_mock_service(MockSvc)
            client = TestClient(calib_app, raise_server_exceptions=False)
            body = client.get('/calibration/dashboard').json()
        assert body.get("success") is True


# ---------------------------------------------------------------------------
# Static code quality checks (no network, no DB)
# ---------------------------------------------------------------------------

from pathlib import Path
_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _read(path: str) -> str:
    return (_PROJECT_ROOT / path).read_text()


# ---------------------------------------------------------------------------
# Multi-tenant 403 coverage
# ---------------------------------------------------------------------------
# Calibration endpoints use service-layer company_id filtering (not HTTP middleware).
# When CalibrationService raises HTTPException(403) (e.g., cross-company access),
# the endpoint correctly propagates it — tested here via mock injection.

class TestCalibration403:
    def test_explicit_feedback_returns_403_when_service_raises(self, calib_app):
        from fastapi import HTTPException as FastAPIHTTPException
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            svc = MockSvc.return_value
            svc.record_explicit_feedback = AsyncMock(
                side_effect=FastAPIHTTPException(status_code=403, detail="Forbidden: wrong company")
            )
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.post('/calibration/feedback/explicit', json={
                "candidate_id": "cand-001", "job_id": "job-001",
                "recommendation": "hire", "agrees_with_lia": True
            })
        assert resp.status_code == 403

    def test_stats_returns_403_when_service_raises(self, calib_app):
        from fastapi import HTTPException as FastAPIHTTPException
        with patch('app.api.v1.calibration.CalibrationService') as MockSvc:
            svc = MockSvc.return_value
            svc.get_calibration_stats = AsyncMock(
                side_effect=FastAPIHTTPException(status_code=403, detail="Forbidden: wrong company")
            )
            client = TestClient(calib_app, raise_server_exceptions=False)
            resp = client.get('/calibration/stats')
        assert resp.status_code == 403


def test_calibration_no_response_model_none():
    assert "response_model=None" not in _read("app/api/v1/calibration.py")


def test_all_calibration_routes_have_response_model():
    content = _read("app/api/v1/calibration.py")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "@router." in line and "response_model" not in line:
            assert False, f"Line {i + 1} missing response_model: {line.strip()}"


def test_feedback_response_schema_defined():
    assert "class FeedbackResponse(BaseModel)" in _read("app/api/v1/calibration.py")


def test_calibration_stats_response_schema_defined():
    assert "class CalibrationStatsResponse(BaseModel)" in _read("app/api/v1/calibration.py")


def test_suggestion_action_response_schema_defined():
    assert "class SuggestionActionResponse(BaseModel)" in _read("app/api/v1/calibration.py")
