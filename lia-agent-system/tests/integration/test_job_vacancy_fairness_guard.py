"""
Task #358 — Stop discriminatory job descriptions before they get saved.

FairnessGuard now runs at the moment a JobVacancy is created/updated so the
offending text never lands in the database. These tests cover both the
helper module and the create/update endpoint coroutines (called directly,
without standing up a FastAPI test client — TestClient lifespan is too slow
in this codebase to be reliable in CI).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.job_vacancies._shared import (
    JobVacancyCreate,
    JobVacancyUpdate,
    _build_jd_fairness_text,
    run_fairness_guard_on_jd,
)
from app.api.v1.job_vacancies.crud import (
    create_job_vacancy,
    update_job_vacancy,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper-level unit tests
# ─────────────────────────────────────────────────────────────────────────────

CLEAN_TITLE = "Engenheiro Backend Sênior"
CLEAN_DESCRIPTION = (
    "Responsável por desenvolvimento de APIs REST em Python e FastAPI."
)
CLEAN_REQUIREMENTS = ["Python", "FastAPI", "PostgreSQL"]

DISCRIMINATORY_DESCRIPTION = (
    "Vaga apenas para homens com idade máxima 30 anos. "
    "Excluir candidatos com deficiência."
)


def test_build_jd_fairness_text_concatenates_string_and_dict_entries():
    text = _build_jd_fairness_text(
        title="Backend Engineer",
        description="Build APIs.",
        requirements=["Python"],
        technical_requirements=[
            {"technology": "FastAPI", "level": "Sênior"},
            {"name": "AWS"},
        ],
        behavioral_competencies=[{"competency": "Comunicação"}],
        languages=[{"language": "English"}],
    )
    assert "Backend Engineer" in text
    assert "Build APIs." in text
    assert "Python" in text
    assert "FastAPI" in text
    assert "AWS" in text
    assert "Comunicação" in text
    assert "English" in text


def test_run_fairness_guard_on_jd_returns_empty_for_clean_jd():
    warnings = run_fairness_guard_on_jd(
        title=CLEAN_TITLE,
        description=CLEAN_DESCRIPTION,
        requirements=CLEAN_REQUIREMENTS,
    )
    assert warnings == []


def test_run_fairness_guard_on_jd_blocks_explicit_discrimination():
    with pytest.raises(HTTPException) as exc_info:
        run_fairness_guard_on_jd(
            title="Atendente",
            description=DISCRIMINATORY_DESCRIPTION,
            requirements=["comunicação"],
        )

    err = exc_info.value
    assert err.status_code == 422
    assert isinstance(err.detail, dict)
    assert err.detail["code"] == "fairness_blocked"
    # FairnessGuard reports the first matching category — gender or age,
    # both are present. We only require *some* protected category and that
    # the educational message + offending terms made it onto the response.
    assert err.detail["category"] in {
        "genero", "idade", "deficiencia",
    }
    assert err.detail["message"]
    assert err.detail["blocked_terms"]


SOFT_WARNING_DESCRIPTION = (
    "Procuramos profissional com perfil adequado para atender clientes "
    "de bairros nobres e que tenham frequentado universidades de primeira "
    "linha."
)


def test_run_fairness_guard_on_jd_returns_soft_warnings_without_blocking():
    """Implicit-bias terms must NOT block the save, but should be returned."""
    warnings = run_fairness_guard_on_jd(
        title="Vendedor",
        description=SOFT_WARNING_DESCRIPTION,
        requirements=["vendas"],
    )
    assert isinstance(warnings, list)
    assert len(warnings) >= 1


def test_run_fairness_guard_on_jd_swallows_internal_errors():
    """A FairnessGuard regression must never break the JD save endpoint."""
    with patch(
        "app.shared.compliance.fairness_guard.FairnessGuard.check",
        side_effect=RuntimeError("boom"),
    ):
        warnings = run_fairness_guard_on_jd(
            title=CLEAN_TITLE,
            description=CLEAN_DESCRIPTION,
        )
    assert warnings == []


def test_run_fairness_guard_on_jd_picks_up_bias_in_requirements_dict():
    """Requirement dicts (e.g. behavioral_competencies) are scanned too."""
    with pytest.raises(HTTPException) as exc_info:
        run_fairness_guard_on_jd(
            title=CLEAN_TITLE,
            description=CLEAN_DESCRIPTION,
            behavioral_competencies=[
                {"competency": "Apenas mulheres para esta posição"},
            ],
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "fairness_blocked"


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint-level tests — call the FastAPI handler coroutines directly so we
# don't pay the TestClient lifespan cost on this codebase.
# ─────────────────────────────────────────────────────────────────────────────


def _mock_user():
    user = MagicMock()
    user.id = "user-1"
    user.company_id = "test-company"
    user.role = "admin"
    user.is_active = True
    user.email = "admin@test.com"
    return user


def _mock_repo():
    repo = MagicMock()
    repo.get_session = MagicMock(return_value=MagicMock())

    async def _create_vacancy(jv):
        return jv

    async def _flush_and_refresh(obj):
        return obj

    repo.create_vacancy = AsyncMock(side_effect=_create_vacancy)
    repo.flush_and_refresh = AsyncMock(side_effect=_flush_and_refresh)
    return repo


def _existing_vacancy(jv_id="123e4567-e89b-12d3-a456-426614174000"):
    existing = MagicMock()
    existing.id = jv_id
    existing.title = "Original"
    existing.department = None
    existing.location = None
    existing.work_model = None
    existing.employment_type = None
    existing.seniority_level = None
    existing.description = "Original description"
    existing.requirements = ["Python"]
    existing.technical_requirements = []
    existing.languages = []
    existing.behavioral_competencies = []
    existing.salary = None
    existing.salary_range = None
    existing.benefits = []
    existing.manager = None
    existing.manager_email = None
    existing.recruiter = None
    existing.recruiter_email = None
    existing.is_confidential = False
    existing.status = "Rascunho"
    existing.priority = "média"
    existing.created_at = None
    existing.updated_at = None
    existing.screening_questions = []
    existing.interview_stages = []
    existing.disabled_eligibility_question_ids = []
    existing.conversation_id = None
    existing.enriched_jd = None
    return existing


# ─── POST /job-vacancies ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_endpoint_blocks_discriminatory_jd_with_422():
    repo = _mock_repo()
    payload = JobVacancyCreate(
        title="Atendente",
        description=DISCRIMINATORY_DESCRIPTION,
        requirements=["comunicação"],
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_job_vacancy(
            job_data=payload,
            repo=repo,
            current_user=_mock_user(),
            _trial_check=None,
            _plan_check=None,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "fairness_blocked"
    # The repo must NEVER be asked to persist a discriminatory JD.
    repo.create_vacancy.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_endpoint_surfaces_soft_warnings_without_blocking():
    repo = _mock_repo()
    payload = JobVacancyCreate(
        title="Vendedor",
        description=SOFT_WARNING_DESCRIPTION,
        requirements=["vendas"],
    )

    response = await create_job_vacancy(
        job_data=payload,
        repo=repo,
        current_user=_mock_user(),
        _trial_check=None,
        _plan_check=None,
    )

    repo.create_vacancy.assert_awaited_once()
    assert response.fairness_warnings, (
        "Soft warnings must surface to the recruiter on a non-blocked save"
    )


@pytest.mark.asyncio
async def test_create_endpoint_passes_clean_jd_with_no_warnings():
    repo = _mock_repo()
    payload = JobVacancyCreate(
        title=CLEAN_TITLE,
        description=CLEAN_DESCRIPTION,
        requirements=CLEAN_REQUIREMENTS,
    )

    response = await create_job_vacancy(
        job_data=payload,
        repo=repo,
        current_user=_mock_user(),
        _trial_check=None,
        _plan_check=None,
    )

    repo.create_vacancy.assert_awaited_once()
    assert not response.fairness_warnings


# ─── PUT /job-vacancies/{id} ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_endpoint_blocks_discriminatory_description():
    from uuid import UUID

    repo = _mock_repo()
    existing = _existing_vacancy()
    repo.get_vacancy_by_id_and_company = AsyncMock(return_value=existing)

    payload = JobVacancyUpdate(description=DISCRIMINATORY_DESCRIPTION)

    with pytest.raises(HTTPException) as exc_info:
        await update_job_vacancy(
            job_vacancy_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            job_data=payload,
            repo=repo,
            current_user=_mock_user(),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "fairness_blocked"
    repo.flush_and_refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_endpoint_skips_fairness_check_when_no_jd_fields_change():
    """A non-JD update (e.g. priority) must not re-run the guard."""
    from uuid import UUID

    repo = _mock_repo()
    existing = _existing_vacancy()
    repo.get_vacancy_by_id_and_company = AsyncMock(return_value=existing)

    payload = JobVacancyUpdate(priority="alta")

    with patch(
        "app.api.v1.job_vacancies.crud.run_fairness_guard_on_jd"
    ) as mock_guard:
        with patch(
            "app.domains.job_management.services.job_audit_service.job_audit_service.log_update",
            new_callable=AsyncMock,
        ):
            await update_job_vacancy(
                job_vacancy_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
                job_data=payload,
                repo=repo,
                current_user=_mock_user(),
            )

    mock_guard.assert_not_called()


# ─── POST /job-vacancies/finalize (wizard / conversational flow) ────────────


def _mock_state(description: str, title: str = CLEAN_TITLE):
    """Lightweight stand-in for `JobVacancyState` for finalize tests."""
    state = MagicMock()
    state.job_title = title
    state.description = description
    state.job_description_generated = description
    state.required_skills = ["Python"]
    state.technical_requirements = []
    state.is_ready_for_publication = MagicMock(return_value=True)
    state.pipeline_template_id = None
    return state


def _finalize_request(state):
    req = MagicMock()
    req.job_vacancy_state = state
    req.conversation_id = "conv-1"
    req.created_by = "user-1"
    return req


@pytest.mark.asyncio
async def test_finalize_endpoint_blocks_discriminatory_jd_with_422():
    from app.api.v1.job_vacancies.crud import finalize_job_vacancy

    repo = _mock_repo()
    state = _mock_state(DISCRIMINATORY_DESCRIPTION, title="Atendente")

    fake_service = MagicMock()
    fake_service.finalize_job_vacancy = AsyncMock()
    with patch(
        "app.api.v1.job_vacancies.crud.job_vacancy_service",
        fake_service,
        create=True,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await finalize_job_vacancy(
                request=_finalize_request(state),
                repo=repo,
                current_user=_mock_user(),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "fairness_blocked"
    # The wizard must not call into the service that performs the DB write.
    fake_service.finalize_job_vacancy.assert_not_awaited()


@pytest.mark.asyncio
async def test_finalize_endpoint_surfaces_soft_warnings_in_response():
    from app.api.v1.job_vacancies.crud import finalize_job_vacancy

    repo = _mock_repo()
    state = _mock_state(SOFT_WARNING_DESCRIPTION, title="Vendedor")

    persisted = MagicMock()
    persisted.id = "jv-1"
    persisted.title = "Vendedor"
    persisted.status = "Rascunho"

    fake_service = MagicMock()
    fake_service.finalize_job_vacancy = AsyncMock(return_value=persisted)
    with patch(
        "app.api.v1.job_vacancies.crud.job_vacancy_service",
        fake_service,
        create=True,
    ):
        with patch(
            "app.domains.job_management.services.job_audit_service.job_audit_service.log_creation",
            new_callable=AsyncMock,
        ):
            response = await finalize_job_vacancy(
                request=_finalize_request(state),
                repo=repo,
                current_user=_mock_user(),
            )

    assert response.success is True
    assert response.fairness_warnings, (
        "Soft warnings must surface in FinalizeJobVacancyResponse"
    )
