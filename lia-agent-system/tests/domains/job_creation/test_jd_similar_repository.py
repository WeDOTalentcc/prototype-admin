"""Unit tests for JdSimilarHistoryRepository — Sprint B Phase 1.

TDD red phase: tests fail until repo + model are implemented.

Scope: input validation, multi-tenancy enforcement, query construction.
Persistência real é validada em tests/integration/test_jd_similar_integration.py
(separado, requer DB real com pgvector).
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


# ── Fixtures locais ───────────────────────────────────────────────────────────


@pytest.fixture
def fake_company_a() -> str:
    return f"company-a-{uuid4()}"


@pytest.fixture
def fake_embedding_1536() -> list[float]:
    """Fake 1536-dim embedding."""
    import random
    rng = random.Random(42)
    return [rng.uniform(-1, 1) for _ in range(1536)]


@pytest.fixture
def sample_jd_payload() -> dict[str, Any]:
    return {
        "title": "Engenheiro Backend Pleno",
        "responsibilities": ["API design", "Code review"],
        "requirements": ["Python", "PostgreSQL"],
    }


# ── Multi-tenancy enforcement ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_jd_requires_company_id(db_session, fake_embedding_1536, sample_jd_payload):
    """ADR + LGPD: missing company_id raises ValueError (fail-closed)."""
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )

    repo = JdSimilarHistoryRepository(db_session)

    with pytest.raises(ValueError, match="company_id"):
        await repo.record_jd(
            company_id="",  # empty
            job_id="job-x",
            title_normalized="test",
            jd_enriched=sample_jd_payload,
            embedding=fake_embedding_1536,
        )


@pytest.mark.asyncio
async def test_record_jd_requires_embedding_dim(db_session, fake_company_a, sample_jd_payload):
    """Embedding must have 1536 dims (OpenAI text-embedding-3-small)."""
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )

    repo = JdSimilarHistoryRepository(db_session)
    bad_embedding = [0.1] * 768  # wrong dim (Gemini default)

    with pytest.raises(ValueError, match="1536"):
        await repo.record_jd(
            company_id=fake_company_a,
            job_id="job-x",
            title_normalized="test",
            jd_enriched=sample_jd_payload,
            embedding=bad_embedding,
        )


@pytest.mark.asyncio
async def test_find_similar_requires_company_id(db_session, fake_embedding_1536):
    """find_similar_jds rejects empty company_id."""
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )

    repo = JdSimilarHistoryRepository(db_session)

    with pytest.raises(ValueError, match="company_id"):
        await repo.find_similar_jds(
            company_id="",
            embedding=fake_embedding_1536,
            min_similarity=0.7,
            limit=3,
        )


# ── Query construction ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_jd_calls_add_and_commit(
    db_session, fake_company_a, fake_embedding_1536, sample_jd_payload
):
    """record_jd appends entity to session and commits."""
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )

    repo = JdSimilarHistoryRepository(db_session)

    await repo.record_jd(
        company_id=fake_company_a,
        job_id="job-1",
        title_normalized="vaga teste",
        jd_enriched=sample_jd_payload,
        embedding=fake_embedding_1536,
        seniority_level="pleno",
        department="engenharia",
    )

    assert len(db_session.added) == 1
    record = db_session.added[0]
    assert record.company_id == fake_company_a
    assert record.job_id == "job-1"
    assert record.title_normalized == "vaga teste"
    assert record.was_filled is False
    assert record.candidates_count == 0
    assert db_session.commits == 1


@pytest.mark.asyncio
async def test_count_for_company_filters_by_tenant(db_session, fake_company_a):
    """count_for_company executes SELECT filtered by company_id."""
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )

    # Mock execute to return scalar 7
    mock_result = MagicMock()
    mock_result.scalar = MagicMock(return_value=7)
    db_session.execute = AsyncMock(return_value=mock_result)

    repo = JdSimilarHistoryRepository(db_session)
    count = await repo.count_for_company(fake_company_a)

    assert count == 7
    db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_find_similar_below_threshold_returns_empty(
    db_session, fake_company_a, fake_embedding_1536
):
    """When count_for_company < 10, find_similar_jds returns [] without similarity query."""
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )

    # First execute returns count, second would return rows (should NOT be called)
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=5)
    db_session.execute = AsyncMock(return_value=count_result)

    repo = JdSimilarHistoryRepository(db_session)
    similar = await repo.find_similar_jds(
        company_id=fake_company_a,
        embedding=fake_embedding_1536,
        min_similarity=0.7,
        limit=3,
    )
    assert similar == []
    # Only count query, not similarity query
    assert db_session.execute.await_count == 1


@pytest.mark.asyncio
async def test_find_similar_above_threshold_runs_similarity_query(
    db_session, fake_company_a, fake_embedding_1536
):
    """When count >= 10, find_similar_jds runs the pgvector similarity query."""
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )

    # Two execute calls: count, then similarity query
    count_result = MagicMock()
    count_result.scalar = MagicMock(return_value=15)

    sim_row = MagicMock()
    sim_row.id = uuid4()
    sim_row.title_normalized = "Vaga similar"
    sim_row.department = "engenharia"
    sim_row.seniority_level = "pleno"
    sim_row.was_filled = True
    sim_row.time_to_fill_days = 18
    sim_row.candidates_count = 47
    sim_row.jd_enriched_json = {"title": "x"}

    sim_result = MagicMock()
    sim_result.all = MagicMock(return_value=[(sim_row, 0.95)])

    db_session.execute = AsyncMock(side_effect=[count_result, sim_result])

    repo = JdSimilarHistoryRepository(db_session)
    similar = await repo.find_similar_jds(
        company_id=fake_company_a,
        embedding=fake_embedding_1536,
        min_similarity=0.7,
        limit=3,
    )

    assert len(similar) == 1
    assert similar[0]["title"] == "Vaga similar"
    assert similar[0]["was_filled"] is True
    assert similar[0]["time_to_fill_days"] == 18
    assert db_session.execute.await_count == 2


@pytest.mark.asyncio
async def test_mark_filled_executes_update(db_session, fake_uuid_str, fake_company_a):
    """mark_filled runs ownership SELECT + UPDATE and commits.

    Sprint B Phase 1 gap C5: mark_filled now requires company_id and
    performs an ownership SELECT before the UPDATE (multi-tenancy fail-closed).
    Two execute calls expected.
    """
    from app.domains.job_creation.repositories.jd_similar_history_repository import (
        JdSimilarHistoryRepository,
    )
    from uuid import UUID

    # First execute returns ownership SELECT (record belongs to fake_company_a),
    # second execute is the UPDATE.
    ownership_result = MagicMock()
    ownership_result.scalar_one_or_none = MagicMock(return_value=fake_company_a)
    update_result = MagicMock()
    db_session.execute = AsyncMock(side_effect=[ownership_result, update_result])

    repo = JdSimilarHistoryRepository(db_session)
    await repo.mark_filled(
        record_id=UUID(fake_uuid_str),
        company_id=fake_company_a,
        time_to_fill_days=18,
        candidates_count=47,
    )

    assert db_session.execute.await_count == 2
    assert db_session.commits == 1
