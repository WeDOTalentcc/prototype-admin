"""Tests for JdSimilarService — Sprint B Phase 1.

TDD red phase: tests fail until service is implemented.

Coverage:
- Toggle off → returns empty / no record
- Threshold check via repo
- Lifecycle: record → mark_filled
- PII minimization in embeddings
- Fail-open on EmbeddingService errors
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


@pytest.fixture
def fake_company_id() -> str:
    return f"company-{uuid4()}"


@pytest.fixture
def sample_jd_enriched() -> dict[str, Any]:
    return {
        "title": "Engenheiro Backend Pleno",
        "description": "API design + mentoria",
        "responsibilities": ["API", "Reviews"],
        "requirements": ["Python", "PostgreSQL"],
    }


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.find_similar_jds = AsyncMock(return_value=[])
    repo.record_jd = AsyncMock()
    repo.mark_filled = AsyncMock()
    repo.count_for_company = AsyncMock(return_value=0)
    repo.find_id_by_job = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    svc = MagicMock()
    svc.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    return svc


# ── Service contract tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_similar_returns_empty_when_toggle_off(
    fake_company_id, mock_repo, mock_embedding_service
):
    """Toggle off → returns [] without hitting repo."""
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    result = await svc.find_similar(
        company_id=fake_company_id,
        title="Engenheiro Backend",
        department="engenharia",
        toggle_enabled=False,
    )

    assert result == []
    mock_repo.find_similar_jds.assert_not_called()


@pytest.mark.asyncio
async def test_find_similar_calls_embedding_then_repo(
    fake_company_id, mock_repo, mock_embedding_service
):
    """Toggle on + above threshold → embedding + repo called."""
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    mock_repo.count_for_company = AsyncMock(return_value=15)
    mock_repo.find_similar_jds = AsyncMock(return_value=[
        {"id": "x", "title": "Backend Pleno", "department": "eng",
         "was_filled": True, "time_to_fill_days": 18, "candidates_count": 47},
    ])

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    result = await svc.find_similar(
        company_id=fake_company_id,
        title="Engenheiro Backend",
        department="engenharia",
        toggle_enabled=True,
    )

    mock_embedding_service.generate_embedding.assert_called_once()
    mock_repo.find_similar_jds.assert_called_once()
    assert len(result) == 1
    assert result[0]["title"] == "Backend Pleno"


@pytest.mark.asyncio
async def test_find_similar_below_threshold_skips_repo_query(
    fake_company_id, mock_repo, mock_embedding_service
):
    """When count < 10, skip find_similar_jds entirely."""
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    mock_repo.count_for_company = AsyncMock(return_value=5)

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    result = await svc.find_similar(
        company_id=fake_company_id,
        title="Backend",
        department="eng",
        toggle_enabled=True,
    )

    assert result == []
    mock_repo.find_similar_jds.assert_not_called()


@pytest.mark.asyncio
async def test_find_similar_fail_open_on_embedding_error(
    fake_company_id, mock_repo, mock_embedding_service
):
    """If EmbeddingService raises, return [] (fail-open) and log warning."""
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    mock_repo.count_for_company = AsyncMock(return_value=15)
    mock_embedding_service.generate_embedding = AsyncMock(
        side_effect=RuntimeError("provider timeout")
    )

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    result = await svc.find_similar(
        company_id=fake_company_id,
        title="Backend",
        department="eng",
        toggle_enabled=True,
    )

    assert result == []  # fail-open


@pytest.mark.asyncio
async def test_record_jd_calls_repo_with_embedding(
    fake_company_id, mock_repo, mock_embedding_service, sample_jd_enriched
):
    """record_jd computes embedding from title+responsibilities (no PII) and persists."""
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    await svc.record_jd(
        company_id=fake_company_id,
        job_id="job-123",
        title="Engenheiro Backend Pleno",
        jd_enriched=sample_jd_enriched,
        seniority_level="pleno",
        department="engenharia",
    )

    # Embedding computed from title + responsibilities ONLY
    embedding_call = mock_embedding_service.generate_embedding.call_args
    embedded_text = embedding_call.args[0] if embedding_call.args else embedding_call.kwargs.get("text", "")
    # PII guard: must NOT contain email/cpf-like patterns or names
    assert "@" not in embedded_text  # no emails
    assert "CPF" not in embedded_text.upper()
    # Should contain JD content
    assert "Engenheiro Backend Pleno" in embedded_text or "engenheiro" in embedded_text.lower()

    mock_repo.record_jd.assert_called_once()


@pytest.mark.asyncio
async def test_record_jd_requires_company_id(mock_repo, mock_embedding_service, sample_jd_enriched):
    """Service rejects empty company_id (multi-tenancy)."""
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    with pytest.raises(ValueError, match="company_id"):
        await svc.record_jd(
            company_id="",
            job_id="job-x",
            title="x",
            jd_enriched=sample_jd_enriched,
        )


@pytest.mark.asyncio
async def test_mark_filled_calls_repo(fake_company_id, mock_repo, mock_embedding_service):
    """mark_filled forwards to repo when record exists."""
    from uuid import uuid4
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    mock_repo.find_id_by_job = AsyncMock(return_value=uuid4())

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    await svc.mark_filled(
        company_id=fake_company_id,
        job_id="job-123",
        time_to_fill_days=18,
        candidates_count=47,
    )

    mock_repo.mark_filled.assert_called_once()


@pytest.mark.asyncio
async def test_record_jd_does_not_log_pii(
    fake_company_id, mock_repo, mock_embedding_service, sample_jd_enriched, caplog
):
    """ADR-006: no PII (email/cpf/name/phone) in any log call."""
    from app.domains.job_creation.services.jd_similar_service import JdSimilarService

    svc = JdSimilarService(repository=mock_repo, embedding_service=mock_embedding_service)

    await svc.record_jd(
        company_id=fake_company_id,
        job_id="job-pii-test",
        title="Test PII Vaga",
        jd_enriched=sample_jd_enriched,
    )

    # No PII patterns in log records
    for record in caplog.records:
        msg = record.getMessage()
        assert "@" not in msg, f"email-like in log: {msg}"
        assert "CPF" not in msg.upper(), f"CPF mention in log: {msg}"
