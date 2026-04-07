"""
Tests for automation/triggers endpoints — real production router with mocked services.

Mounts the actual router from app/api/v1/automation/triggers.py.
Patched surfaces:
  - app.api.v1.automation.triggers.automation_trigger_service (module-level global)
  - get_automation_service FastAPI dependency override
  - get_activity_service FastAPI dependency override
  - get_cv_scoring_service (called inside handlers, patched via module namespace)

Coverage:
  200 — GET /triggers, GET /status, GET /stage-suggestions (required query params)
  200 — POST /triggers/{trigger_id}, POST /check, POST /screen-candidate, POST /trigger-event
  422 — missing required body fields (Pydantic schema validation)
  404 — POST /triggers/{trigger_id} for non-existent trigger_id
  Static — response_model contracts, no response_model=None
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared test app
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def automation_app():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    from app.api.v1.automation.triggers import router
    from app.core.database import get_db
    from app.api.v1.automation._shared import get_automation_service, get_activity_service

    app = FastAPI()
    app.include_router(router)

    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_auto_svc = MagicMock()
    mock_auto_svc.get_stage_suggestions = AsyncMock(return_value={
        "suggestions": [],
        "to_stage": "interview",
        "company_id": "company-001"
    })
    app.dependency_overrides[get_automation_service] = lambda: mock_auto_svc

    mock_activity_svc = AsyncMock()
    app.dependency_overrides[get_activity_service] = lambda: mock_activity_svc

    return app


def _mock_trigger_service(*, trigger_exists=True, check_result=None):
    """Build a mock automation_trigger_service."""
    svc = MagicMock()
    svc.get_triggers_config.return_value = [
        {"id": "trigger-001", "name": "Auto Screen", "enabled": True},
        {"id": "trigger-002", "name": "Auto Interview", "enabled": False},
    ]
    svc.update_trigger_status.return_value = trigger_exists
    svc.check_and_execute_triggers = AsyncMock(return_value=check_result or {
        "checked": 2, "executed": 1, "errors": []
    })
    return svc


# ---------------------------------------------------------------------------
# GET /triggers
# ---------------------------------------------------------------------------

class TestGetTriggers:
    def test_returns_200(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.get('/triggers')
        assert resp.status_code == 200

    def test_response_has_success(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            body = client.get('/triggers').json()
        assert body.get("success") is True

    def test_data_contains_triggers(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            body = client.get('/triggers').json()
        assert "data" in body
        assert "triggers" in body["data"]


# ---------------------------------------------------------------------------
# POST /triggers/{trigger_id}  — enable/disable
# ---------------------------------------------------------------------------

class TestUpdateTrigger:
    def test_enable_known_trigger_returns_200(self, automation_app):
        mock_svc = _mock_trigger_service(trigger_exists=True)
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/triggers/trigger-001', json={"enabled": True})
        assert resp.status_code == 200

    def test_unknown_trigger_returns_404(self, automation_app):
        mock_svc = _mock_trigger_service(trigger_exists=False)
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/triggers/no-such-trigger', json={"enabled": True})
        assert resp.status_code == 404

    def test_missing_enabled_field_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/triggers/trigger-001', json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /check
# ---------------------------------------------------------------------------

class TestCheckTriggers:
    def test_returns_200(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/check')
        assert resp.status_code == 200

    def test_response_has_success(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            body = client.post('/check').json()
        assert body.get("success") is True


# ---------------------------------------------------------------------------
# GET /status
# ---------------------------------------------------------------------------

class TestAutomationStatus:
    def test_returns_200(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.get('/status')
        assert resp.status_code == 200

    def test_response_has_status_field(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            body = client.get('/status').json()
        assert "status" in body.get("data", {})


# ---------------------------------------------------------------------------
# GET /stage-suggestions
# ---------------------------------------------------------------------------

class TestStageSuggestions:
    def test_valid_query_returns_200(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.get('/stage-suggestions', params={
                "to_stage": "interview",
                "company_id": "company-001"
            })
        assert resp.status_code == 200

    def test_missing_to_stage_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.get('/stage-suggestions', params={"company_id": "company-001"})
        assert resp.status_code == 422

    def test_missing_company_id_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.get('/stage-suggestions', params={"to_stage": "interview"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /screen-candidate
# ---------------------------------------------------------------------------

class TestScreenCandidate:
    def test_valid_request_returns_200(self, automation_app):
        mock_svc = _mock_trigger_service()
        cv_mock = MagicMock()
        cv_mock.screen_candidate = AsyncMock(return_value={
            "success": True,
            "rubric_score": 78.5,
            "recommendation": "Recomendado",
            "candidate_id": "cand-001"
        })
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc), \
             patch('app.api.v1.automation.triggers.get_cv_scoring_service', return_value=cv_mock):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/screen-candidate', json={
                "candidate_id": "cand-001",
                "vacancy_id": "vac-001",
                "company_id": "company-001"
            })
        assert resp.status_code == 200

    def test_missing_candidate_id_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/screen-candidate', json={
                "vacancy_id": "vac-001",
                "company_id": "company-001"
            })
        assert resp.status_code == 422

    def test_missing_vacancy_id_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/screen-candidate', json={
                "candidate_id": "cand-001",
                "company_id": "company-001"
            })
        assert resp.status_code == 422

    def test_missing_company_id_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/screen-candidate', json={
                "candidate_id": "cand-001",
                "vacancy_id": "vac-001"
            })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /trigger-event
# ---------------------------------------------------------------------------

class TestTriggerEvent:
    def test_valid_request_returns_200(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/trigger-event', json={
                "event_type": "job_created",
                "entity_id": "job-001",
                "company_id": "company-001"
            })
        assert resp.status_code == 200

    def test_missing_event_type_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/trigger-event', json={
                "entity_id": "job-001",
                "company_id": "company-001"
            })
        assert resp.status_code == 422

    def test_missing_entity_id_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/trigger-event', json={
                "event_type": "job_created",
                "company_id": "company-001"
            })
        assert resp.status_code == 422

    def test_missing_company_id_returns_422(self, automation_app):
        mock_svc = _mock_trigger_service()
        with patch('app.api.v1.automation.triggers.automation_trigger_service', mock_svc):
            client = TestClient(automation_app, raise_server_exceptions=False)
            resp = client.post('/trigger-event', json={
                "event_type": "job_created",
                "entity_id": "job-001"
            })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Static code quality checks
# ---------------------------------------------------------------------------

from pathlib import Path
_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _read(path: str) -> str:
    return (_PROJECT_ROOT / path).read_text()


def test_triggers_no_response_model_none():
    assert "response_model=None" not in _read("app/api/v1/automation/triggers.py")


def test_all_triggers_routes_have_response_model():
    content = _read("app/api/v1/automation/triggers.py")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "@router." in line and "response_model" not in line:
            assert False, f"Line {i + 1} missing response_model: {line.strip()}"


def test_triggers_list_response_schema_defined():
    assert "class TriggersListResponse(BaseModel)" in _read("app/api/v1/automation/triggers.py")


def test_screen_candidate_response_schema_defined():
    assert "class ScreenCandidateResponse(BaseModel)" in _read("app/api/v1/automation/triggers.py")


def test_trigger_event_response_schema_defined():
    assert "class TriggerEventResponse(BaseModel)" in _read("app/api/v1/automation/triggers.py")


def test_normalize_weights_empty_analyses_returns_empty_dict():
    """Guard for division-by-zero in _normalize_weights when no responses are analyzed."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from app.api.v1.automation.event_handlers import _normalize_weights

    result = _normalize_weights({}, [])
    assert result == {}, f"Expected empty dict, got {result}"


def test_normalize_weights_empty_analyses_with_provided_weights():
    """Provided weights must still return empty dict when no analyses exist."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from app.api.v1.automation.event_handlers import _normalize_weights

    result = _normalize_weights({"Python": 0.5}, [])
    assert result == {}, f"Expected empty dict, got {result}"


def test_event_handlers_no_response_model_none():
    assert "response_model=None" not in _read("app/api/v1/automation/event_handlers.py")


def test_event_handlers_explicit_response_models():
    content = _read("app/api/v1/automation/event_handlers.py")
    assert "ScreeningCompletedResponse" in content
    assert "InterviewScheduledResponse" in content
    assert "ATSSyncResponse" in content
    assert "CandidateNoShowResponse" in content
    assert "CandidateHiredResponse" in content
    assert "CandidateRejectedResponse" in content


def test_response_schemas_no_bare_dict_fields():
    """Enforce that all *Response schemas in _shared.py use typed Pydantic models,
    not bare dict / dict[str, Any] / dict[str, str] as field types."""
    import re
    content = _read("app/api/v1/automation/_shared.py")

    # Extract each Response class body and scan for bare-dict fields
    class_blocks = re.findall(
        r'class \w+Response\(BaseModel\)(.*?)(?=^class |\Z)',
        content,
        re.MULTILINE | re.DOTALL,
    )
    violations = []
    bare_dict_pattern = re.compile(
        r'(\w+):\s*(?:dict\s*\[|dict\s*\||\bdict\b\s*=)'
    )
    for block in class_blocks:
        for m in bare_dict_pattern.finditer(block):
            violations.append(m.group(0).strip())

    assert not violations, (
        f"Response schemas must not use bare dict fields. Found: {violations}"
    )


# ---------------------------------------------------------------------------
# 403 — multi-tenant isolation via validate_multi_tenancy in event_handlers
# ---------------------------------------------------------------------------

class TestAutomationTenantIsolation403:
    """Tests for 403 Forbidden when validate_multi_tenancy returns False.

    event_handlers.py calls validate_multi_tenancy(db, candidate_id, vacancy_id, company_id)
    and raises HTTPException(403) when the check fails. This is the enforcement mechanism
    for cross-company isolation in the automation trigger pipeline.
    """

    def test_screening_completed_wrong_company_returns_403(self):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

        from app.api.v1.automation.event_handlers import router as eh_router
        from app.core.database import get_db

        app = FastAPI()
        app.include_router(eh_router)
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        payload = {
            "candidate_id": "cand-001",
            "vacancy_id": "vac-001",
            "company_id": "wrong-company",
            "screening_type": "chat",
            "responses": []
        }
        with patch(
            'app.api.v1.automation.event_handlers.validate_multi_tenancy',
            new=AsyncMock(return_value=(False, "Vacancy belongs to different company"))
        ):
            resp = client.post('/handle-trigger/screening-completed', json=payload)
        assert resp.status_code == 403

    def test_interview_scheduled_wrong_company_returns_403(self):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

        from app.api.v1.automation.event_handlers import router as eh_router
        from app.core.database import get_db
        from app.domains.analytics.services.activity_service import ActivityService

        app = FastAPI()
        app.include_router(eh_router)
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        payload = {
            "candidate_id": "cand-001",
            "vacancy_id": "vac-001",
            "company_id": "wrong-company",
            "interview_datetime": "2026-06-01T10:00:00",
            "interview_type": "technical"
        }
        with patch(
            'app.api.v1.automation.event_handlers.validate_multi_tenancy',
            new=AsyncMock(return_value=(False, "Vacancy belongs to different company"))
        ):
            resp = client.post('/handle-trigger/interview-scheduled', json=payload)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Parametrized 403 tests — all remaining event_handlers.py endpoints
# ---------------------------------------------------------------------------

_EH_BASE_PAYLOAD = {
    "candidate_id": "cand-001",
    "vacancy_id": "vac-001",
    "company_id": "wrong-company",
}

_EH_403_CASES = [
    (
        "/handle-trigger/interview-completed",
        {**_EH_BASE_PAYLOAD, "interview_id": "iv-001"},
    ),
    (
        "/handle-trigger/candidate-inactive",
        _EH_BASE_PAYLOAD,
    ),
    (
        "/handle-trigger/candidate-no-show",
        {**_EH_BASE_PAYLOAD, "interview_id": "iv-001", "interview_datetime": "2026-06-01T10:00:00"},
    ),
    (
        "/handle-trigger/ats-sync",
        {**_EH_BASE_PAYLOAD, "new_stage": "screening"},
    ),
    (
        "/handle-trigger/offer-sent",
        _EH_BASE_PAYLOAD,
    ),
    (
        "/handle-trigger/candidate-hired",
        _EH_BASE_PAYLOAD,
    ),
    (
        "/handle-trigger/candidate-rejected",
        {**_EH_BASE_PAYLOAD, "reviewer_id": "reviewer-001"},
    ),
]


@pytest.mark.parametrize("endpoint,payload", _EH_403_CASES)
def test_event_handler_wrong_company_returns_403(endpoint, payload):
    """All 9 event_handlers.py endpoints must return 403 when validate_multi_tenancy fails."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    from app.api.v1.automation.event_handlers import router as eh_router
    from app.core.database import get_db

    app = FastAPI()
    app.include_router(eh_router)
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app, raise_server_exceptions=False)
    with patch(
        'app.api.v1.automation.event_handlers.validate_multi_tenancy',
        new=AsyncMock(return_value=(False, "Vacancy belongs to different company"))
    ):
        resp = client.post(endpoint, json=payload)
    assert resp.status_code == 403, (
        f"{endpoint} returned {resp.status_code}, expected 403. Body: {resp.text[:200]}"
    )
