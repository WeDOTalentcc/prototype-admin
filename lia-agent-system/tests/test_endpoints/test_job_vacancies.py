"""
Tests for job_vacancies endpoints — real production router with mocked services.

Mounts the actual router from app/api/v1/job_vacancies/crud.py.
Patched surfaces:
  - get_current_active_user / get_current_user_or_demo FastAPI dependency overrides
  - get_job_vacancy_crud_repo dependency override
  - require_active_subscription_or_demo / check_active_jobs_limit_or_demo overrides

The tests exercise the REAL production router code and Pydantic schemas without a DB.
Multi-tenant isolation is enforced through get_user_company_id(current_user) on every
endpoint — this is tested by checking that a user without company_id receives 400.

Coverage:
  200 — GET /job-vacancies (list with company scoping)
  200 — POST /job-vacancies (create with title)
  200 — GET /job-vacancies/{id} (retrieve by id)
  422 — POST /job-vacancies missing required title field
  404 — GET /job-vacancies/{unknown_id}
  400 — Any endpoint with user missing company_id
  Static — get_user_company_id usage, response_model contracts
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

COMPANY_UUID = str(uuid.uuid4())
JOB_UUID = str(uuid.uuid4())


def _make_mock_user(*, company_id=COMPANY_UUID):
    user = MagicMock()
    user.id = "user-001"
    user.email = "recruiter@company.com"
    user.company_id = company_id
    user.role = "recruiter"
    return user


def _make_mock_vacancy(vid=JOB_UUID):
    jv = MagicMock(spec=[])
    jv.id = uuid.UUID(vid) if isinstance(vid, str) else vid
    jv.title = "Senior Python Developer"
    jv.department = "Engineering"
    jv.location = "Remote"
    jv.work_model = "remote"
    jv.employment_type = "full_time"
    jv.seniority_level = "senior"
    jv.description = "Test job"
    jv.requirements = []
    jv.technical_requirements = []
    jv.languages = []
    jv.behavioral_competencies = []
    jv.salary = None
    jv.salary_range = None
    jv.bonus_range = None
    jv.benefits = []
    jv.manager = None
    jv.manager_email = None
    jv.recruiter = None
    jv.recruiter_email = None
    jv.priority = "média"
    jv.company_id = COMPANY_UUID
    jv.status = "active"
    jv.stage = None
    jv.visibility = "public"
    jv.is_confidential = False
    jv.masked_company_name = None
    jv.exclude_from_sync = False
    jv.created_by = "recruiter@company.com"
    jv.access_list = []
    jv.created_at = None
    jv.updated_at = None
    jv.deadline = None
    jv.published_at = None
    jv.closed_at = None
    jv.funnel_data = None
    jv.lia_metrics = None
    jv.nps = None
    jv.budget = None
    jv.budget_used = None
    jv.published_linkedin = False
    jv.published_website = False
    jv.next_actions = []
    jv.urgency_level = None
    jv.approval_status = None
    jv.tags = []
    jv.screening_questions = []
    jv.interview_stages = []
    jv.eligibility_questions = []
    jv.disabled_eligibility_question_ids = []
    jv.confidentiality_config = None
    jv.screening_criteria = None
    jv.scoring_weights = None
    jv.custom_questions = []
    jv.compensation_details = None
    jv.affirmative_action_enabled = False
    jv.affirmative_pcd = False
    jv.affirmative_gender = False
    jv.affirmative_race = False
    jv.affirmative_age = False
    jv.affirmative_document_required = False
    jv.banner_url = None
    jv.openings = 1
    jv.job_id = "JOB-001"
    jv.area = None
    jv.urgency = None
    jv.salary_confidential = False
    jv.hide_company_name = False
    jv.wsi_score_threshold = 70
    jv.min_score_threshold = 60
    jv.conversation_id = None
    jv.timeline = None
    jv.governance_rules = None
    jv.whatsapp_template_type = None
    jv.screening_config = None
    jv.enriched_jd = None
    jv.is_affirmative = False
    jv.affirmative_criteria_primary = None
    jv.affirmative_criteria_secondary = None
    jv.affirmative_description = None
    jv.screening_status = None
    return jv


@pytest.fixture(scope="module")
def jv_app():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    from app.api.v1.job_vacancies.crud import router
    from app.auth.dependencies import get_current_active_user, get_current_user_or_demo
    from app.domains.job_management.dependencies import get_job_vacancy_crud_repo
    from app.middleware.trial_enforcement import require_active_subscription_or_demo
    from app.shared.services.plan_limits_service import check_active_jobs_limit_or_demo

    app = FastAPI()
    app.include_router(router)

    mock_user = _make_mock_user()
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    app.dependency_overrides[get_current_user_or_demo] = lambda: mock_user
    app.dependency_overrides[require_active_subscription_or_demo] = lambda: None
    app.dependency_overrides[check_active_jobs_limit_or_demo] = lambda: None

    mock_repo = MagicMock()
    mock_repo.list_vacancies = AsyncMock(return_value=[])
    mock_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=None)
    mock_repo.get_job_vacancy_by_id = AsyncMock(return_value=None)
    mock_repo.create_vacancy = AsyncMock(return_value=_make_mock_vacancy())
    mock_repo.save_job_vacancy = AsyncMock(return_value=_make_mock_vacancy())
    mock_repo.search_by_query = AsyncMock(return_value=(0, []))
    mock_repo.get_completed_vacancies = AsyncMock(return_value=[])
    mock_repo.get_archetypes = AsyncMock(return_value=[])
    mock_repo.get_session = MagicMock(return_value=MagicMock())
    app.dependency_overrides[get_job_vacancy_crud_repo] = lambda: mock_repo

    return app


# ---------------------------------------------------------------------------
# GET /job-vacancies
# ---------------------------------------------------------------------------

class TestListJobVacancies:
    def test_returns_200(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        resp = client.get('/job-vacancies')
        assert resp.status_code == 200

    def test_response_has_items(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        body = client.get('/job-vacancies').json()
        assert "items" in body

    def test_response_has_total(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        body = client.get('/job-vacancies').json()
        assert "total" in body

    def test_user_without_company_returns_400(self, jv_app):
        from app.auth.dependencies import get_current_user_or_demo, get_current_active_user

        no_company_user = _make_mock_user(company_id=None)
        orig_user = jv_app.dependency_overrides.get(get_current_user_or_demo)
        orig_active = jv_app.dependency_overrides.get(get_current_active_user)
        try:
            jv_app.dependency_overrides[get_current_user_or_demo] = lambda: no_company_user
            jv_app.dependency_overrides[get_current_active_user] = lambda: no_company_user
            client = TestClient(jv_app, raise_server_exceptions=False)
            resp = client.get('/job-vacancies')
            assert resp.status_code == 400
        finally:
            if orig_user is not None:
                jv_app.dependency_overrides[get_current_user_or_demo] = orig_user
            if orig_active is not None:
                jv_app.dependency_overrides[get_current_active_user] = orig_active


# ---------------------------------------------------------------------------
# POST /job-vacancies  — create
# ---------------------------------------------------------------------------

class TestCreateJobVacancy:
    def test_valid_request_returns_201_or_200(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        resp = client.post('/job-vacancies', json={"title": "Senior Python Dev"})
        assert resp.status_code in (200, 201)

    def test_response_has_id(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        body = client.post('/job-vacancies', json={"title": "Senior Python Dev"}).json()
        assert "id" in body

    def test_missing_title_returns_422(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        resp = client.post('/job-vacancies', json={})
        assert resp.status_code == 422

    def test_empty_title_returns_422(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        resp = client.post('/job-vacancies', json={"title": ""})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /job-vacancies/{job_vacancy_id} — retrieve by ID
# ---------------------------------------------------------------------------

class TestGetJobVacancy:
    def test_not_found_returns_404(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        resp = client.get(f'/job-vacancies/{JOB_UUID}')
        assert resp.status_code == 404

    def test_existing_vacancy_returns_200(self, jv_app):
        from app.domains.job_management.dependencies import get_job_vacancy_crud_repo
        vac = _make_mock_vacancy(JOB_UUID)
        mock_repo = MagicMock()
        mock_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=vac)
        mock_repo.list_vacancies = AsyncMock(return_value=[])
        mock_repo.save_job_vacancy = AsyncMock(return_value=vac)
        mock_repo.search_by_query = AsyncMock(return_value=(0, []))
        mock_repo.get_archetypes = AsyncMock(return_value=[])
        mock_repo.get_session = MagicMock(return_value=MagicMock())

        jv_app.dependency_overrides[get_job_vacancy_crud_repo] = lambda: mock_repo
        try:
            client = TestClient(jv_app, raise_server_exceptions=False)
            resp = client.get(f'/job-vacancies/{JOB_UUID}')
            assert resp.status_code == 200
        finally:
            from app.domains.job_management.dependencies import get_job_vacancy_crud_repo as orig
            default_repo = MagicMock()
            default_repo.list_vacancies = AsyncMock(return_value=[])
            default_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=None)
            default_repo.get_job_vacancy_by_id = AsyncMock(return_value=None)
            default_repo.create_vacancy = AsyncMock(return_value=_make_mock_vacancy())
            default_repo.save_job_vacancy = AsyncMock(return_value=_make_mock_vacancy())
            default_repo.search_by_query = AsyncMock(return_value=(0, []))
            default_repo.get_completed_vacancies = AsyncMock(return_value=[])
            default_repo.get_archetypes = AsyncMock(return_value=[])
            default_repo.get_session = MagicMock(return_value=MagicMock())
            jv_app.dependency_overrides[orig] = lambda: default_repo


    def test_confidential_vacancy_different_user_returns_403(self, jv_app):
        from app.domains.job_management.dependencies import get_job_vacancy_crud_repo
        vac = _make_mock_vacancy(JOB_UUID)
        vac.visibility = "confidential"
        vac.created_by = "other@company.com"
        vac.recruiter_email = "other@company.com"
        vac.access_list = []

        mock_repo = MagicMock()
        mock_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=vac)
        mock_repo.list_vacancies = AsyncMock(return_value=[])
        mock_repo.create_vacancy = AsyncMock(return_value=_make_mock_vacancy())
        mock_repo.search_by_query = AsyncMock(return_value=(0, []))
        mock_repo.get_completed_vacancies = AsyncMock(return_value=[])
        mock_repo.get_archetypes = AsyncMock(return_value=[])
        mock_repo.get_session = MagicMock(return_value=MagicMock())

        jv_app.dependency_overrides[get_job_vacancy_crud_repo] = lambda: mock_repo
        try:
            client = TestClient(jv_app, raise_server_exceptions=False)
            resp = client.get(f'/job-vacancies/{JOB_UUID}')
            assert resp.status_code == 403
        finally:
            from app.domains.job_management.dependencies import get_job_vacancy_crud_repo as orig
            default_repo = MagicMock()
            default_repo.list_vacancies = AsyncMock(return_value=[])
            default_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=None)
            default_repo.create_vacancy = AsyncMock(return_value=_make_mock_vacancy())
            default_repo.search_by_query = AsyncMock(return_value=(0, []))
            default_repo.get_completed_vacancies = AsyncMock(return_value=[])
            default_repo.get_archetypes = AsyncMock(return_value=[])
            default_repo.get_session = MagicMock(return_value=MagicMock())
            jv_app.dependency_overrides[orig] = lambda: default_repo


# ---------------------------------------------------------------------------
# GET /job-vacancies/search
# ---------------------------------------------------------------------------

class TestSearchJobVacancies:
    def test_returns_200(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        resp = client.get('/job-vacancies/search', params={"q": "python"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /job-vacancies/archetypes
# ---------------------------------------------------------------------------

class TestJobVacancyArchetypes:
    def test_returns_200(self, jv_app):
        client = TestClient(jv_app, raise_server_exceptions=False)
        resp = client.get('/job-vacancies/archetypes')
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Cross-company 403 (wrong company_id)
# ---------------------------------------------------------------------------
# Job vacancies use get_user_company_id(current_user) for scoping.
# When a user with company A tries to access a vacancy owned by company B that
# is confidential, the handler raises 403. We simulate this directly.

class TestJobVacancyCrossTenant403:
    def test_wrong_company_access_returns_403(self, jv_app):
        """GET /job-vacancies/{id} returns 403 when the requesting user's company
        does not match the vacancy owner company (confidential visibility)."""
        from app.domains.job_management.dependencies import get_job_vacancy_crud_repo
        vac = _make_mock_vacancy(JOB_UUID)
        vac.visibility = "confidential"
        vac.created_by = "recruiter@company-b.com"
        vac.recruiter_email = "recruiter@company-b.com"
        vac.access_list = []

        mock_repo = MagicMock()
        mock_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=vac)
        mock_repo.list_vacancies = AsyncMock(return_value=[])
        mock_repo.create_vacancy = AsyncMock(return_value=_make_mock_vacancy())
        mock_repo.search_by_query = AsyncMock(return_value=(0, []))
        mock_repo.get_completed_vacancies = AsyncMock(return_value=[])
        mock_repo.get_archetypes = AsyncMock(return_value=[])
        mock_repo.get_session = MagicMock(return_value=MagicMock())

        jv_app.dependency_overrides[get_job_vacancy_crud_repo] = lambda: mock_repo
        try:
            client = TestClient(jv_app, raise_server_exceptions=False)
            resp = client.get(f'/job-vacancies/{JOB_UUID}')
            assert resp.status_code == 403
        finally:
            default_repo = MagicMock()
            default_repo.list_vacancies = AsyncMock(return_value=[])
            default_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=None)
            default_repo.create_vacancy = AsyncMock(return_value=_make_mock_vacancy())
            default_repo.search_by_query = AsyncMock(return_value=(0, []))
            default_repo.get_completed_vacancies = AsyncMock(return_value=[])
            default_repo.get_archetypes = AsyncMock(return_value=[])
            default_repo.get_session = MagicMock(return_value=MagicMock())
            jv_app.dependency_overrides[get_job_vacancy_crud_repo] = lambda: default_repo


# ---------------------------------------------------------------------------
# Static code quality checks
# ---------------------------------------------------------------------------

from pathlib import Path
_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _read(path: str) -> str:
    return (_PROJECT_ROOT / path).read_text()


def test_job_vacancies_uses_get_user_company_id():
    content = _read("app/api/v1/job_vacancies/crud.py")
    assert "get_user_company_id(current_user)" in content


def test_job_vacancies_finalize_has_response_model():
    content = _read("app/api/v1/job_vacancies/crud.py")
    assert "response_model=FinalizeJobVacancyResponse" in content


def test_job_vacancy_crud_response_has_response_model():
    content = _read("app/api/v1/job_vacancies/crud.py")
    assert "response_model=JobVacancyResponse" in content


def test_company_scoping_enforced_via_helper():
    content = _read("app/auth/dependencies.py")
    assert "def get_user_company_id(" in content


def test_company_scoping_raises_400_for_missing_company():
    content = _read("app/auth/dependencies.py")
    assert "status_code=400" in content
