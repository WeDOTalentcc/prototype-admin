"""TDD: ConversationMemoryRepository (Sprint 5.4 — ADR-001 canonical example).

Tests the multi-tenancy fail-closed gate. DB integration tested via
existing service-level tests (no separate DB fixture here).

Skill: tdd-workflow + canonical-fix.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.recruiter_assistant.repositories.conversation_memory_repository import (
    ConversationMemoryRepository,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    return db


def test_require_company_id_raises_on_empty():
    """Multi-tenancy fail-closed gate (CLAUDE.md REGRA 1)."""
    with pytest.raises(ValueError, match="Multi-tenancy invariant"):
        ConversationMemoryRepository._require_company_id("")


def test_require_company_id_raises_on_none():
    with pytest.raises(ValueError, match="Multi-tenancy invariant"):
        ConversationMemoryRepository._require_company_id(None)  # type: ignore


def test_require_company_id_passes_on_valid():
    # Should not raise
    ConversationMemoryRepository._require_company_id("tenant-A")
    ConversationMemoryRepository._require_company_id("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_get_recent_fail_closed_without_company_id(mock_db):
    """The repository must refuse to query without company_id."""
    repo = ConversationMemoryRepository(mock_db)
    with pytest.raises(ValueError, match="Multi-tenancy invariant"):
        await repo.get_recent_for_session(
            company_id="",
            session_id="sess-1",
        )
    # DB must NOT be touched when fail-closed gate triggers
    mock_db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_recent_calls_db_with_filter(mock_db):
    """When company_id present, repo issues a SELECT with company filter."""
    # Mock execute().scalars().all() chain
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    repo = ConversationMemoryRepository(mock_db)
    rows = await repo.get_recent_for_session(
        company_id="tenant-A",
        session_id="sess-1",
        limit=10,
    )

    assert rows == []
    mock_db.execute.assert_awaited_once()
