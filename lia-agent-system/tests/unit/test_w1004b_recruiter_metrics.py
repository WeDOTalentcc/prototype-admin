"""W1-004-B · TDD tests · RecruiterMetricsRepository canonical piloto."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest


def _get_async_database_url():
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "+asyncpg" not in url:
        return None
    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    new_qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment)
    )
    return url


def test_repository_importable():
    """W1-004-B · RecruiterMetricsRepository canonical importável."""
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )
    assert RecruiterMetricsRepository is not None


def test_require_company_id_fail_closed():
    """W1-004-B · _require_company_id raise ValueError quando empty."""
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )
    with pytest.raises(ValueError, match="company_id is required"):
        RecruiterMetricsRepository._require_company_id("")
    with pytest.raises(ValueError, match="company_id is required"):
        RecruiterMetricsRepository._require_company_id(None)


def test_require_company_id_passes_valid():
    """W1-004-B · _require_company_id retorna str canonical."""
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )
    assert RecruiterMetricsRepository._require_company_id("abc-123") == "abc-123"
    assert RecruiterMetricsRepository._require_company_id(uuid.uuid4()) is not None


def test_kanban_tool_uses_repo():
    """W1-004-B · kanban_tool_registry deve importar RecruiterMetricsRepository."""
    from pathlib import Path
    src = (
        Path(__file__).resolve().parents[2]
        / "app/domains/recruiter_assistant/agents/kanban_tool_registry.py"
    ).read_text()
    assert "from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import" in src
    assert "RecruiterMetricsRepository" in src
    # SQL inline old block deve ter sido removido (não há mais "FROM vacancy_candidates WHERE vacancy_id = :vid"
    # do tool function que migramos — outras SQL inlines do mesmo arquivo continuam por design piloto)
    assert "AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) AS avg_days" not in src, (
        "SQL inline migrated should be removed from kanban_tool_registry "
        "(piloto W1-004-B: get_pipeline_benchmarks → RecruiterMetricsRepository)"
    )


def test_repository_methods_canonical_signature():
    """W1-004-B · interface canonical de RecruiterMetricsRepository."""
    import inspect
    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    # avg_days_per_stage_for_vacancy
    sig = inspect.signature(RecruiterMetricsRepository.avg_days_per_stage_for_vacancy)
    params = set(sig.parameters.keys())
    assert "vacancy_id" in params
    assert "company_id" in params

    # avg_days_per_stage_for_company
    sig = inspect.signature(RecruiterMetricsRepository.avg_days_per_stage_for_company)
    params = set(sig.parameters.keys())
    assert "company_id" in params


@pytest.mark.asyncio
async def test_avg_days_per_stage_for_vacancy_integration():
    """W1-004-B · integration test contra Postgres real (skip se sem DB)."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available")

    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    async with sm() as session:
        repo = RecruiterMetricsRepository(session)
        # Test with valid UUID format but nonexistent record (returns empty)
        result = await repo.avg_days_per_stage_for_vacancy(
            vacancy_id=str(uuid.uuid4()),
            company_id=str(uuid.uuid4()),
        )
        assert isinstance(result, dict)
        # Nonexistent vacancy has no candidates → empty dict
        assert result == {}

    await engine.dispose()


@pytest.mark.asyncio
async def test_avg_days_per_stage_for_company_integration():
    """W1-004-B · integration test company aggregate (skip se sem DB)."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available")

    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    async with sm() as session:
        repo = RecruiterMetricsRepository(session)
        result = await repo.avg_days_per_stage_for_company(
            company_id=f"nonexistent-{uuid.uuid4().hex}",
        )
        assert isinstance(result, dict)
        assert result == {}

    await engine.dispose()


@pytest.mark.asyncio
async def test_fail_closed_in_integration():
    """W1-004-B · fail-closed em método público mesmo via DB session."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available")

    from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
        RecruiterMetricsRepository,
    )

    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    async with sm() as session:
        repo = RecruiterMetricsRepository(session)
        with pytest.raises(ValueError, match="company_id is required"):
            await repo.avg_days_per_stage_for_company(company_id="")
        with pytest.raises(ValueError, match="company_id is required"):
            await repo.avg_days_per_stage_for_vacancy(
                vacancy_id="some-id", company_id=""
            )
        with pytest.raises(ValueError, match="vacancy_id is required"):
            await repo.avg_days_per_stage_for_vacancy(
                vacancy_id="", company_id="cid-1"
            )

    await engine.dispose()
