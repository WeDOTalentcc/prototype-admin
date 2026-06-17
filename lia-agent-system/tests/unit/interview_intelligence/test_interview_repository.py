"""TDD: InterviewRepository (Sprint 5.8 — ADR-001 example for interview_intelligence)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.interview_intelligence.repositories.interview_repository import (
    InterviewRepository,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    return db


def test_require_company_id_raises_on_empty():
    with pytest.raises(ValueError, match="Multi-tenancy invariant"):
        InterviewRepository._require_company_id("")


def test_require_company_id_raises_on_none():
    with pytest.raises(ValueError, match="Multi-tenancy invariant"):
        InterviewRepository._require_company_id(None)  # type: ignore


def test_require_company_id_passes_on_valid():
    InterviewRepository._require_company_id("tenant-A")


@pytest.mark.asyncio
async def test_get_fail_closed_without_company_id(mock_db):
    repo = InterviewRepository(mock_db)
    with pytest.raises(ValueError, match="Multi-tenancy invariant"):
        await repo.get_for_company(interview_id="i-1", company_id="")
    mock_db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_calls_db_with_company_filter(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    repo = InterviewRepository(mock_db)
    result = await repo.get_for_company(
        interview_id="i-1",
        company_id="tenant-A",
    )

    assert result is None
    mock_db.execute.assert_awaited_once()
