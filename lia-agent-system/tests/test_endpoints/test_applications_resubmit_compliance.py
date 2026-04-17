"""
Task #331 — Auditoria Auth/FairnessGuard/audit em applications.resubmit.

Cobre 3 cenarios:
  (a) request sem auth -> 401
  (b) CV com texto discriminatorio -> 422 (FairnessGuard bloqueia)
  (c) sucesso -> audit row registrada com inputs_hash e score
"""
import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


COMPANY_UUID = str(uuid.uuid4())
VACANCY_UUID = str(uuid.uuid4())
CANDIDATE_UUID = str(uuid.uuid4())


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
    return v


def _make_candidate():
    c = MagicMock()
    c.id = CANDIDATE_UUID
    c.name = "Jane Doe"
    c.technical_skills = ["python"]
    c.years_of_experience = 4
    c.current_title = "Backend Dev"
    c.location_city = "Remote"
    c.seniority_level = "senior"
    return c


def _make_feedback(score=30.0):
    fb = MagicMock()
    fb.id = uuid.uuid4()
    fb.adherence_score = score
    return fb


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


def _make_repo():
    repo = MagicMock()
    repo.get_feedback_by_token = AsyncMock(return_value=_make_feedback())
    repo.get_candidate_by_id = AsyncMock(return_value=_make_candidate())
    repo.get_vacancy_by_id = AsyncMock(return_value=_make_vacancy())
    repo.get_vacancy_candidate = AsyncMock(return_value=None)
    repo.create_vacancy_candidate = AsyncMock()
    repo.rollback = AsyncMock()
    repo.db = MagicMock()
    return repo


def _make_upload(content=b"PDF-bytes", filename="cv.pdf"):
    uf = MagicMock()
    uf.filename = filename
    uf.read = AsyncMock(return_value=content)
    return uf


# ---------------------------------------------------------------------------
# (a) sem auth -> 401
# ---------------------------------------------------------------------------
def test_resubmit_without_auth_returns_401():
    from app.api.v1.applications import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    resp = client.post(
        f"/applications/resubmit/{VACANCY_UUID}",
        params={"candidate_id": CANDIDATE_UUID, "token": "abc"},
        files={"cv_file": ("cv.pdf", b"PDF", "application/pdf")},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# (b) CV discriminatorio -> 422
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resubmit_with_discriminatory_cv_returns_422():
    from app.api.v1.applications import resubmit_cv

    repo = _make_repo()
    cv_parser = MagicMock()
    cv_parser.parse_cv = AsyncMock(return_value={
        "raw_text": "Apenas homens podem se candidatar a esta vaga.",
        "skills": [],
    })

    with patch("app.api.v1.applications.audit_service") as audit:
        audit.log_decision = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await resubmit_cv(
                vacancy_id=VACANCY_UUID,
                candidate_id=CANDIDATE_UUID,
                token="valid-token",
                cv_file=_make_upload(),
                repo=repo,
                cv_parser_svc=cv_parser,
                current_user=_make_user(),
            )

        assert exc.value.status_code == 422
        detail = exc.value.detail
        assert isinstance(detail, dict)
        assert detail.get("error") == "fairness_block"
        audit.log_decision.assert_awaited()
        kw = audit.log_decision.call_args.kwargs
        assert kw["company_id"] == COMPANY_UUID
        assert kw["decision_type"] == "application_resubmit"
        assert kw["action"] == "fairness_block"


# ---------------------------------------------------------------------------
# (c) sucesso -> audit row com inputs_hash e score
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resubmit_success_logs_audit_decision():
    from app.api.v1.applications import resubmit_cv

    repo = _make_repo()
    cv_parser = MagicMock()
    cv_parser.parse_cv = AsyncMock(return_value={
        "raw_text": "Profissional com experiencia em desenvolvimento backend Python.",
        "skills": ["python", "fastapi"],
        "experience_years": 5,
        "current_title": "Senior Backend Engineer",
    })

    with patch("app.api.v1.applications.lia_score_service") as score_svc, \
         patch("app.api.v1.applications.notification_service") as notif, \
         patch("app.api.v1.applications.candidate_feedback_service") as feedback_svc, \
         patch("app.api.v1.applications.audit_service") as audit:
        score_svc.calculate_score = MagicMock(return_value=_make_score_result(score=80.0))
        feedback_svc.ADHERENCE_THRESHOLD = 50.0
        feedback_svc.mark_resubmit_completed = AsyncMock()
        notif.create_notification = AsyncMock()
        audit.log_decision = AsyncMock()

        result = await resubmit_cv(
            vacancy_id=VACANCY_UUID,
            candidate_id=CANDIDATE_UUID,
            token="valid-token",
            cv_file=_make_upload(),
            repo=repo,
            cv_parser_svc=cv_parser,
            current_user=_make_user(),
        )

        assert result.status == "resubmitted"
        assert result.new_adherence_score == 80.0
        assert result.qualified is True

        # The success path should log exactly one audit decision (no fairness block)
        assert audit.log_decision.await_count == 1
        kw = audit.log_decision.call_args.kwargs
        assert kw["company_id"] == COMPANY_UUID
        assert kw["agent_name"] == "applications_api"
        assert kw["decision_type"] == "application_resubmit"
        assert kw["action"] == "adherence_score_recalculated"
        assert kw["score"] == 80.0
        assert kw["job_vacancy_id"] == VACANCY_UUID
        assert kw["candidate_id"] == CANDIDATE_UUID
        assert any("inputs_hash=" in r for r in kw["reasoning"])


# ---------------------------------------------------------------------------
# (d) FairnessGuard indisponivel -> 503 (fail-closed)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resubmit_fairness_unavailable_returns_503():
    from app.api.v1.applications import resubmit_cv

    repo = _make_repo()
    cv_parser = MagicMock()
    cv_parser.parse_cv = AsyncMock(return_value={
        "raw_text": "Profissional com experiencia tecnica.",
        "skills": [],
    })

    class _BoomGuard:
        def check(self, _payload):
            raise RuntimeError("guard exploded")

    with patch("app.api.v1.applications.FairnessGuard", _BoomGuard), \
         patch("app.api.v1.applications.audit_service") as audit:
        audit.log_decision = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await resubmit_cv(
                vacancy_id=VACANCY_UUID,
                candidate_id=CANDIDATE_UUID,
                token="valid-token",
                cv_file=_make_upload(),
                repo=repo,
                cv_parser_svc=cv_parser,
                current_user=_make_user(),
            )

        assert exc.value.status_code == 503
        detail = exc.value.detail
        assert isinstance(detail, dict)
        assert detail.get("error") == "fairness_unavailable"
        audit.log_decision.assert_awaited()
        kw = audit.log_decision.call_args.kwargs
        assert kw["decision_type"] == "application_resubmit"
        assert kw["action"] == "fairness_unavailable"
        assert kw["decision"] == "blocked"


# ---------------------------------------------------------------------------
# (e) cross-tenant -> 403
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resubmit_cross_tenant_returns_403():
    from app.api.v1.applications import resubmit_cv

    repo = _make_repo()
    cv_parser = MagicMock()
    cv_parser.parse_cv = AsyncMock(return_value={"raw_text": "", "skills": []})

    other_company = str(uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        await resubmit_cv(
            vacancy_id=VACANCY_UUID,
            candidate_id=CANDIDATE_UUID,
            token="valid-token",
            cv_file=_make_upload(),
            repo=repo,
            cv_parser_svc=cv_parser,
            current_user=_make_user(company_id=other_company),
        )

    assert exc.value.status_code == 403
