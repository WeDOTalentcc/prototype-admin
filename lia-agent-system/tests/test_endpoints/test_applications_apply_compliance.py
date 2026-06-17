"""
Task #310 — Auditoria Auth/FairnessGuard/audit em applications.apply.

Cobre 3 cenarios:
  (a) request sem auth -> 401
  (b) texto discriminatorio -> 422 (FairnessGuard bloqueia)
  (c) sucesso -> 1 audit row registrada com inputs_hash e score
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


COMPANY_UUID = str(uuid.uuid4())
VACANCY_UUID = str(uuid.uuid4())


def _make_user(company_id=COMPANY_UUID):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "recruiter@company.com"
    user.company_id = company_id
    user.role = MagicMock(value="recruiter")
    user.is_active = True
    return user


def _make_vacancy():
    v = MagicMock()
    v.id = VACANCY_UUID
    v.title = "Senior Python Developer"
    v.company_id = COMPANY_UUID
    v.company_name = "ACME"
    v.status = "open"
    v.required_skills = ["python"]
    v.min_experience_years = 3
    v.seniority_level = "senior"
    v.location_city = "Remote"
    v.governance_rules = {}
    return v


def _make_score_result(score=80.0):
    breakdown = MagicMock()
    breakdown.skills_match = 85.0
    sr = MagicMock()
    sr.score = score
    sr.matched_skills = ["python"]
    sr.missing_skills = []
    sr.breakdown = breakdown
    sr.to_dict = lambda: {"score": score}
    return sr


def _make_repo(vacancy=None, candidate=None):
    repo = MagicMock()
    repo.get_vacancy_by_id = AsyncMock(return_value=vacancy or _make_vacancy())
    cand = candidate or MagicMock(id=uuid.uuid4())
    repo.get_candidate_by_email = AsyncMock(return_value=None)
    repo.create_candidate = AsyncMock(return_value=cand)
    repo.flush = AsyncMock()
    repo.get_vacancy_candidate = AsyncMock(return_value=None)
    repo.get_company_threshold = AsyncMock(return_value=20)
    repo.count_organic_candidates = AsyncMock(return_value=0)
    repo.create_vacancy_candidate = AsyncMock()
    repo.get_job_requirements = AsyncMock(return_value=[])
    repo.rollback = AsyncMock()
    repo.db = MagicMock()
    return repo


def _make_app():
    """Mount only the applications router with overridable dependencies."""
    from app.api.v1.applications import router
    from app.auth.dependencies import get_current_user
    from app.domains.recruitment.dependencies import get_application_repo
    from app.domains.cv_screening.services.cv_parser import get_cv_parser_service
    from app.domains.cv_screening.services.rubric_evaluation_service import get_rubric_evaluation_service

    app = FastAPI()
    app.include_router(router)
    return app, {
        "auth": get_current_user,
        "repo": get_application_repo,
        "cv": get_cv_parser_service,
        "rubric": get_rubric_evaluation_service,
    }


# ---------------------------------------------------------------------------
# (a) sem auth -> 401
# ---------------------------------------------------------------------------
def test_apply_without_auth_returns_401():
    app, _ = _make_app()
    client = TestClient(app)
    resp = client.post(
        f"/applications/apply/{VACANCY_UUID}",
        data={"application": '{"name":"X","email":"x@y.z"}'},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# (b) texto discriminatorio -> 422
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_apply_with_discriminatory_cover_letter_returns_422():
    from app.api.v1.applications import apply_to_vacancy, CandidateApplicationRequest

    repo = _make_repo()
    rubric_svc = MagicMock()
    cv_parser = MagicMock()

    request = CandidateApplicationRequest(
        name="John Doe",
        email="john@example.com",
        cover_letter="Apenas homens podem se candidatar a esta vaga.",
    )

    with patch("app.api.v1.applications.audit_service") as audit:
        audit.log_decision = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await apply_to_vacancy(
                vacancy_id=VACANCY_UUID,
                application=request,
                cv_file=None,
                repo=repo,
                cv_parser_svc=cv_parser,
                rubric_svc=rubric_svc,
                current_user=_make_user(),
            )

        assert exc.value.status_code == 422
        detail = exc.value.detail
        assert isinstance(detail, dict)
        assert detail.get("error") == "fairness_block"
        # audit row recorded for fairness block
        audit.log_decision.assert_awaited()
        kw = audit.log_decision.call_args.kwargs
        assert kw["company_id"] == COMPANY_UUID
        assert kw["decision_type"] == "application_apply"
        assert kw["action"] == "fairness_block"


# ---------------------------------------------------------------------------
# (c) sucesso -> 1 audit row com inputs_hash e score
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_apply_success_logs_audit_decision():
    from app.api.v1.applications import apply_to_vacancy, CandidateApplicationRequest

    repo = _make_repo()
    cv_parser = MagicMock()
    rubric_svc = MagicMock()
    rubric_svc.evaluate_and_create_activity = AsyncMock()

    request = CandidateApplicationRequest(
        name="Jane Doe",
        email="jane@example.com",
        years_of_experience=5,
        technical_skills=["python", "fastapi"],
        location="Remote",
        cover_letter="Profissional com experiencia em desenvolvimento backend.",
    )

    with patch("app.api.v1.applications.lia_score_service") as score_svc, \
         patch("app.api.v1.applications.notification_service") as notif, \
         patch("app.api.v1.applications.candidate_feedback_service") as feedback, \
         patch("app.api.v1.applications.audit_service") as audit:
        score_svc.calculate_score = MagicMock(return_value=_make_score_result(score=80.0))
        feedback.ADHERENCE_THRESHOLD = 50.0
        feedback.check_and_send_feedback = AsyncMock()
        notif.create_notification = AsyncMock()
        audit.log_decision = AsyncMock()

        result = await apply_to_vacancy(
            vacancy_id=VACANCY_UUID,
            application=request,
            cv_file=None,
            repo=repo,
            cv_parser_svc=cv_parser,
            rubric_svc=rubric_svc,
            current_user=_make_user(),
        )

        assert result.status == "accepted"
        assert result.adherence_score == 80.0

        # Exactly one audit_service.log_decision call (the scoring decision)
        assert audit.log_decision.await_count == 1
        kw = audit.log_decision.call_args.kwargs
        assert kw["company_id"] == COMPANY_UUID
        assert kw["agent_name"] == "applications_api"
        assert kw["decision_type"] == "application_apply"
        assert kw["action"] == "adherence_score_calculated"
        assert kw["score"] == 80.0
        assert kw["job_vacancy_id"] == VACANCY_UUID
        assert any("inputs_hash=" in r for r in kw["reasoning"])
