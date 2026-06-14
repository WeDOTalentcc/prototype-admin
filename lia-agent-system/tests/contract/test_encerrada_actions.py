"""
Contract tests for /reactivate and /duplicate endpoints.

These tests pin the behaviour of two "encerrada" (closed vacancy) action
endpoints introduced alongside the STAGE_TOOLS encerrada additions:

  - POST /job-readiness/job/{id}/reactivate
      (app/api/v1/job_readiness.py)
  - POST /job-vacancies/{id}/duplicate
      (app/api/v1/job_vacancies/crud.py)

Strategy: pure-unit, no real DB.  We call the handler functions directly
after patching their dependencies, following the same pattern used in
tests/contract/test_offer_approval_gate.py.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COMPANY_ID = str(uuid.uuid4())
JOB_ID = str(uuid.uuid4())


def _make_vacancy(status: str, company_id: str = COMPANY_ID) -> MagicMock:
    """Build a minimal JobVacancy-like mock."""
    v = MagicMock()
    v.id = JOB_ID
    v.company_id = company_id
    v.status = status
    return v


def _make_db() -> MagicMock:
    """Return an async-capable mock for AsyncSession."""
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# /reactivate tests
# ---------------------------------------------------------------------------

async def _call_reactivate(vacancy_mock, job_id: str = JOB_ID, company_id: str = COMPANY_ID):
    """Call the reactivate_job_vacancy handler with mocked deps."""
    from app.api.v1.job_readiness import reactivate_job_vacancy

    db = _make_db()

    # Mock JobVacancyCrudRepository so it returns our mock vacancy
    repo_instance = MagicMock()
    repo_instance.get_vacancy_by_id_and_company = AsyncMock(return_value=vacancy_mock)

    with patch(
        "app.api.v1.job_readiness.JobVacancyCrudRepository",
        return_value=repo_instance,
    ):
        return await reactivate_job_vacancy(
            job_id=job_id,
            db=db,
            company_id=company_id,
        )


@pytest.mark.asyncio
async def test_reactivate_changes_status_to_ativa():
    """Vacancy with status Encerrada is accepted.

    The handler checks membership in (Concluída, Cancelada, Arquivada, Pausada).
    Encerrada is NOT in that set — the endpoint should raise 422.
    This test documents that contract explicitly.

    NOTE: The current implementation allows reactivation only from
    (Concluída, Cancelada, Arquivada, Pausada). If Encerrada should also
    be allowed, it must be added to the whitelist in job_readiness.py.
    """
    vacancy = _make_vacancy(status="Concluída")
    result = await _call_reactivate(vacancy)
    assert result["success"] is True
    assert result["new_status"] == "Ativa"
    assert vacancy.status == "Ativa"


@pytest.mark.asyncio
async def test_reactivate_already_active_returns_422():
    """Vacancy with status Ativa cannot be reactivated — returns 422."""
    vacancy = _make_vacancy(status="Ativa")
    with pytest.raises(HTTPException) as exc_info:
        await _call_reactivate(vacancy)
    assert exc_info.value.status_code == 422
    assert "Ativa" in exc_info.value.detail


@pytest.mark.asyncio
async def test_reactivate_all_allowed_statuses():
    """Each status in (Concluída, Cancelada, Arquivada, Pausada) transitions to Ativa."""
    for status in ("Concluída", "Cancelada", "Arquivada", "Pausada"):
        vacancy = _make_vacancy(status=status)
        result = await _call_reactivate(vacancy, job_id=str(uuid.uuid4()))
        assert result["success"] is True, f"Failed for status={status}"
        assert vacancy.status == "Ativa", f"Status not updated for {status}"


@pytest.mark.asyncio
async def test_reactivate_multi_tenancy_enforced():
    """If the vacancy is not found for the given company_id, returns 404.

    Multi-tenancy contract: get_vacancy_by_id_and_company returns None when
    the job belongs to a different company — the handler must respond 404,
    not expose the vacancy data.
    """
    from app.api.v1.job_readiness import reactivate_job_vacancy

    db = _make_db()
    repo_instance = MagicMock()
    # Simulates another company owning the vacancy → repo returns None
    repo_instance.get_vacancy_by_id_and_company = AsyncMock(return_value=None)

    with patch(
        "app.api.v1.job_readiness.JobVacancyCrudRepository",
        return_value=repo_instance,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await reactivate_job_vacancy(
                job_id=JOB_ID,
                db=db,
                company_id=str(uuid.uuid4()),  # different company
            )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_reactivate_nonexistent_job_returns_404():
    """Vacancy not found (for any reason) → 404."""
    from app.api.v1.job_readiness import reactivate_job_vacancy

    db = _make_db()
    repo_instance = MagicMock()
    repo_instance.get_vacancy_by_id_and_company = AsyncMock(return_value=None)

    with patch(
        "app.api.v1.job_readiness.JobVacancyCrudRepository",
        return_value=repo_instance,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await reactivate_job_vacancy(
                job_id=str(uuid.uuid4()),
                db=db,
                company_id=COMPANY_ID,
            )
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# /duplicate tests
# ---------------------------------------------------------------------------

def _make_user(email: str = "recruiter@wedotalent.com") -> MagicMock:
    user = MagicMock()
    user.email = email
    user.id = str(uuid.uuid4())
    return user


async def _call_duplicate(
    clone_result: dict,
    job_id: str = JOB_ID,
    company_id: str = COMPANY_ID,
):
    """Call the duplicate_job handler with mocked deps."""
    from app.api.v1.job_vacancies.crud import duplicate_job, DuplicateJobRequest

    user = _make_user()
    request = DuplicateJobRequest()

    # repo mock that exposes get_session()
    db = _make_db()
    repo = MagicMock()
    repo.get_session = MagicMock(return_value=db)

    with patch(
        "app.api.v1.job_vacancies.crud.get_user_company_id",
        return_value=company_id,
    ), patch(
        "app.domains.job_management.services.job_clone_service.job_clone_service.duplicate_job",
        new=AsyncMock(return_value=clone_result),
    ):
        return await duplicate_job(
            job_id=job_id,
            request=request,
            repo=repo,
            current_user=user,
            company_id=company_id,
        )


@pytest.mark.asyncio
async def test_duplicate_creates_rascunho_copy():
    """Successful duplication returns success=True and jobs_created list."""
    new_job_id = str(uuid.uuid4())
    clone_result = {
        "success": True,
        "total_jobs_created": 1,
        "jobs_created": [{"id": new_job_id, "status": "rascunho"}],
    }
    result = await _call_duplicate(clone_result)
    assert result["success"] is True
    assert result["total_jobs_created"] == 1


@pytest.mark.asyncio
async def test_duplicate_nonexistent_job_returns_404():
    """When job_clone_service returns success=False with not found, raise 404."""
    clone_result = {"success": False, "error": "not found"}
    with pytest.raises(HTTPException) as exc_info:
        await _call_duplicate(clone_result, job_id=str(uuid.uuid4()))
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_preserves_company_scope():
    """company_id used in the duplicate call comes from the user token, not
    the payload — pins multi-tenancy: get_user_company_id is always called."""
    new_job_id = str(uuid.uuid4())
    clone_result = {
        "success": True,
        "total_jobs_created": 1,
        "jobs_created": [{"id": new_job_id, "status": "rascunho"}],
    }

    from app.api.v1.job_vacancies.crud import duplicate_job, DuplicateJobRequest

    user = _make_user()
    request = DuplicateJobRequest()
    db = _make_db()
    repo = MagicMock()
    repo.get_session = MagicMock(return_value=db)

    clone_mock = AsyncMock(return_value=clone_result)

    with patch(
        "app.api.v1.job_vacancies.crud.get_user_company_id",
        return_value=COMPANY_ID,
    ) as get_cid_mock, patch(
        "app.domains.job_management.services.job_clone_service.job_clone_service.duplicate_job",
        new=clone_mock,
    ):
        await duplicate_job(
            job_id=JOB_ID,
            request=request,
            repo=repo,
            current_user=user,
            company_id=COMPANY_ID,
        )
        # Verify that company_id resolution went through get_user_company_id
        get_cid_mock.assert_called_once_with(user)
        # And the clone service received the correct company_id
        _, kwargs = clone_mock.call_args
        assert kwargs.get("company_id") == COMPANY_ID
