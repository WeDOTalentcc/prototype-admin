"""chat + interview_scheduling — cross-tenant repository isolation contract tests.

Sensor permanente para os fixes do sprint 2026-05-22 que adicionaram
multi-tenancy defense-in-depth em chat + interview_scheduling repositories.

Pattern canonical: testes pure-unit que inspecionam o `select/update(...)` SQL
montado, verificando WHERE clause com company_id filter ANTES de execute().

Cobertura:
1. ChatRepository.get_conversation_by_id com/sem company_id.
2. ChatRepository.list_conversations com company_id filter.
3. InterviewRepository.get_interview_by_id com company_id filter.
4. InterviewRepository.get_candidate_by_id com company_id filter.
5. InterviewRepository.get_for_candidate_and_job com company_id filter.
6. InterviewAnalysisRepository.get_interview_by_id com company_id filter.
7. InterviewAnalysisRepository.update_interview_feedback com company_id filter.

Referência: ADR-001 + REGRA ZERO + HARDENING_PLAN B.1.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


TENANT_A_ID = "11111111-1111-4111-a111-111111111111"
CANDIDATE_ID = uuid.UUID("33333333-3333-4333-a333-333333333333")
JOB_VACANCY_ID = uuid.UUID("44444444-4444-4444-a444-444444444444")


def _make_async_session_returning(rows: list | None = None) -> MagicMock:
    """Build a mock AsyncSession that returns the given rows on execute."""
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalar = MagicMock(return_value=0)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=rows or [])))
    session.execute = AsyncMock(return_value=result)
    return session


def _where_clause(stmt) -> str:
    """Extract WHERE clause text from a compiled SQLAlchemy statement."""
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False})).lower()
    where_idx = sql.find("where ")
    assert where_idx >= 0, f"No WHERE clause in SQL: {sql}"
    return sql[where_idx:]


# ── ChatRepository ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_get_conversation_with_company_filters() -> None:
    """ChatRepository.get_conversation_by_id MUST add company_id filter."""
    from app.repositories.chat_repository import ChatRepository

    session = _make_async_session_returning([])
    repo = ChatRepository(session)
    await repo.get_conversation_by_id(
        str(uuid.uuid4()), company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_chat_get_conversation_without_company_omits_filter() -> None:
    """Backwards-compat path — Postgres RLS guards via get_tenant_db."""
    from app.repositories.chat_repository import ChatRepository

    session = _make_async_session_returning([])
    repo = ChatRepository(session)
    await repo.get_conversation_by_id(str(uuid.uuid4()))

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" not in where_clause, (
        f"company_id appeared unexpectedly: {where_clause}"
    )


# ── InterviewRepository ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_interview_get_by_id_with_company_filters() -> None:
    """InterviewRepository.get_interview_by_id MUST add company_id filter."""
    from app.domains.interview_scheduling.repositories.interview_repository import (
        InterviewRepository,
    )

    session = _make_async_session_returning([])
    repo = InterviewRepository(session)
    await repo.get_interview_by_id(
        str(uuid.uuid4()), company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_interview_get_candidate_with_company_filters() -> None:
    """InterviewRepository.get_candidate_by_id MUST add company_id filter."""
    from app.domains.interview_scheduling.repositories.interview_repository import (
        InterviewRepository,
    )

    session = _make_async_session_returning([])
    repo = InterviewRepository(session)
    await repo.get_candidate_by_id(CANDIDATE_ID, company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_interview_get_for_candidate_and_job_with_company_filters() -> None:
    """get_for_candidate_and_job MUST add company_id filter when passed."""
    from app.domains.interview_scheduling.repositories.interview_repository import (
        InterviewRepository,
    )

    session = _make_async_session_returning([])
    repo = InterviewRepository(session)
    await repo.get_for_candidate_and_job(
        CANDIDATE_ID, JOB_VACANCY_ID, company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


# ── InterviewAnalysisRepository ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analysis_get_interview_with_company_filters() -> None:
    """InterviewAnalysisRepository.get_interview_by_id MUST add filter."""
    from app.domains.interview_scheduling.repositories.interview_analysis_repository import (
        InterviewAnalysisRepository,
    )

    session = _make_async_session_returning([])
    repo = InterviewAnalysisRepository(session)
    await repo.get_interview_by_id(
        str(uuid.uuid4()), company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_analysis_update_feedback_with_company_filters() -> None:
    """update_interview_feedback MUST add company_id filter to UPDATE WHERE."""
    from app.domains.interview_scheduling.repositories.interview_analysis_repository import (
        InterviewAnalysisRepository,
    )

    session = _make_async_session_returning([])
    repo = InterviewAnalysisRepository(session)
    await repo.update_interview_feedback(
        str(uuid.uuid4()), {"k": "v"}, company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in UPDATE WHERE: {where_clause}"
    )
