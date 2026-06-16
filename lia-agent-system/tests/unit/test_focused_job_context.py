"""
TDD — Vaga em Foco: focused_job_id context injection into LIA system prompt.

Tests for build_focused_job_context in lia_agent_context_builder:
1. Returns empty string when focused_job_id is None.
2. Returns empty string when company_id is empty.
3. Returns empty string when job is not found (None from repo).
4. Returns the expected "## Vaga em foco" block when job is found.
5. Validates multi-tenancy: repo is called with company_id from caller (JWT context).
6. Returns empty string (fail-open) when repo raises an unexpected exception.
7. Returns empty string for malformed UUID (non-UUID focused_job_id).

All imports are lazy to avoid triggering heavy app.__init__ chains at collection time.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# -- Helpers ------------------------------------------------------------------

JOB_ID = uuid.UUID("11111111-1111-4111-a111-111111111111")
COMPANY_ID = "22222222-2222-4222-a222-222222222222"


def _make_job(title: str = "Engenheiro de Software Sênior") -> SimpleNamespace:
    return SimpleNamespace(id=JOB_ID, title=title)


async def _build(focused_job_id, company_id, db):
    """Helper that imports and calls the function under test."""
    from app.shared.services.lia_agent_context_builder import build_focused_job_context
    return await build_focused_job_context(focused_job_id, company_id, db)


# -- Tests --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_empty_when_focused_job_id_is_none():
    """No focused job → no context injection."""
    db = MagicMock()
    result = await _build(None, COMPANY_ID, db)
    assert result == ""


@pytest.mark.asyncio
async def test_returns_empty_when_company_id_is_empty():
    """Empty company_id → no context injection (multi-tenancy guard)."""
    db = MagicMock()
    result = await _build(str(JOB_ID), "", db)
    assert result == ""


@pytest.mark.asyncio
async def test_returns_empty_when_job_not_found():
    """Job not found in the company → empty string, no error raised."""
    db = MagicMock()
    mock_repo = AsyncMock()
    mock_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=None)

    with patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCrudRepository",
        return_value=mock_repo,
    ):
        result = await _build(str(JOB_ID), COMPANY_ID, db)

    assert result == ""


@pytest.mark.asyncio
async def test_returns_focused_job_context_block_when_found():
    """Happy path: job found → returns the expected "## Vaga em foco" block."""
    db = MagicMock()
    job = _make_job("Engenheiro de Software Sênior")
    mock_repo = AsyncMock()
    mock_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=job)

    with patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCrudRepository",
        return_value=mock_repo,
    ):
        result = await _build(str(JOB_ID), COMPANY_ID, db)

    assert "## Vaga em foco" in result
    assert "Engenheiro de Software Sênior" in result
    assert str(JOB_ID) in result
    assert "Priorize" in result


@pytest.mark.asyncio
async def test_multi_tenancy_company_id_passed_to_repo():
    """Repo is called with the company_id from the caller (JWT context), not from job."""
    db = MagicMock()
    job = _make_job()
    mock_repo = AsyncMock()
    mock_repo.get_vacancy_by_id_and_company = AsyncMock(return_value=job)

    with patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCrudRepository",
        return_value=mock_repo,
    ):
        await _build(str(JOB_ID), COMPANY_ID, db)

    mock_repo.get_vacancy_by_id_and_company.assert_called_once_with(
        JOB_ID, COMPANY_ID
    )


@pytest.mark.asyncio
async def test_fail_open_on_repo_exception():
    """If repo raises, function returns empty string — never propagates exception."""
    db = MagicMock()
    mock_repo = AsyncMock()
    mock_repo.get_vacancy_by_id_and_company = AsyncMock(
        side_effect=RuntimeError("DB connection lost")
    )

    with patch(
        "app.domains.job_management.repositories.job_vacancy_crud_repository.JobVacancyCrudRepository",
        return_value=mock_repo,
    ):
        result = await _build(str(JOB_ID), COMPANY_ID, db)

    assert result == ""


@pytest.mark.asyncio
async def test_returns_empty_for_malformed_uuid():
    """Non-UUID focused_job_id (e.g. 'not-a-uuid') → fail-open, returns empty."""
    db = MagicMock()
    result = await _build("not-a-valid-uuid", COMPANY_ID, db)
    assert result == ""
