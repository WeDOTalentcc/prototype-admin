"""candidates — cross-tenant repository isolation contract tests.

Sensor permanente para os fixes do sprint 2026-05-22 que adicionaram
multi-tenancy defense-in-depth em candidates repositories.

Pattern canonical: testes pure-unit que inspecionam o `select(...)` SQL
montado, verificando WHERE clause com company_id filter ANTES de execute().
Não precisa de DB real nem httpx client.

Cobertura:
1. CandidateRepository.get_by_id adiciona company_id filter quando passado.
2. CandidateRepository.get_by_id sem company_id confia em RLS (backwards-compat).
3. CandidateRepository.list_by_ids adiciona company_id filter quando passado.
4. CandidateFavoritesRepository.get adiciona company_id filter quando passado.
5. CandidateHiddenRepository.list_for_user adiciona company_id filter quando passado.
6. VacancyCandidateRepository.get_by_vacancy_and_candidate adiciona filter.

Referência: ADR-001 + REGRA ZERO multi-tenancy fail-closed + HARDENING_PLAN B.1.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


TENANT_A_ID = "11111111-1111-4111-a111-111111111111"
TENANT_B_ID = "22222222-2222-4222-a222-222222222222"
CANDIDATE_ID = uuid.UUID("33333333-3333-4333-a333-333333333333")
VACANCY_ID = uuid.UUID("44444444-4444-4444-a444-444444444444")


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


# ── CandidateRepository ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_candidate_get_by_id_with_company_filters() -> None:
    """CandidateRepository.get_by_id MUST add company_id filter when passed."""
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateRepository(session)
    await repo.get_by_id(CANDIDATE_ID, company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE clause: {where_clause}"
    )


@pytest.mark.asyncio
async def test_candidate_get_by_id_without_company_omits_filter() -> None:
    """get_by_id without company_id — backwards-compat (Postgres RLS guards).

    Legacy callers depend on get_tenant_db RLS; harness B.1 tightening
    happens via gradual caller migration (não big-bang).
    """
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateRepository(session)
    await repo.get_by_id(CANDIDATE_ID)  # no company_id

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" not in where_clause, (
        f"company_id appeared unexpectedly: {where_clause}"
    )


@pytest.mark.asyncio
async def test_candidate_list_by_ids_with_company_filters() -> None:
    """list_by_ids MUST add company_id filter when passed."""
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateRepository(session)
    await repo.list_by_ids([CANDIDATE_ID], company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_candidate_count_with_company_filters() -> None:
    """count_candidates MUST add company_id filter when passed."""
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateRepository(session)
    await repo.count_candidates(company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


# ── CandidateFavoritesRepository ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_favorites_get_with_company_filters() -> None:
    """CandidateFavoritesRepository.get MUST add company_id filter when passed."""
    from app.domains.candidates.repositories.candidate_favorites_repository import (
        CandidateFavoritesRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateFavoritesRepository(session)
    await repo.get(
        candidate_id="cand-1", user_id="user-1", company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_favorites_list_with_company_filters() -> None:
    """CandidateFavoritesRepository.list_for_user MUST add company_id filter."""
    from app.domains.candidates.repositories.candidate_favorites_repository import (
        CandidateFavoritesRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateFavoritesRepository(session)
    await repo.list_for_user(user_id="user-1", company_id=TENANT_A_ID)

    # 2 selects: list query + count query
    assert session.execute.await_count >= 1
    for call in session.execute.await_args_list:
        stmt = call.args[0]
        where_clause = _where_clause(stmt)
        assert "company_id" in where_clause, (
            f"company_id NOT in WHERE: {where_clause}"
        )


# ── CandidateHiddenRepository ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hidden_get_with_company_filters() -> None:
    """CandidateHiddenRepository.get MUST add company_id filter when passed."""
    from app.domains.candidates.repositories.candidate_favorites_repository import (
        CandidateHiddenRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateHiddenRepository(session)
    await repo.get(
        candidate_id="cand-1", user_id="user-1", company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


# ── VacancyCandidateRepository ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vc_get_by_vacancy_candidate_with_company_filters() -> None:
    """VacancyCandidateRepository.get_by_vacancy_and_candidate MUST add filter."""
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = VacancyCandidateRepository(session)
    await repo.get_by_vacancy_and_candidate(
        VACANCY_ID, CANDIDATE_ID, company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_vc_get_most_recent_for_candidate_with_company_filters() -> None:
    """get_most_recent_for_candidate MUST add company_id filter when passed."""
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = VacancyCandidateRepository(session)
    await repo.get_most_recent_for_candidate(
        CANDIDATE_ID, company_id=TENANT_A_ID
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


# ── Empty-string bypass regression (ADR-001 multi-tenancy fail-closed) ───────
# RED tests — must fail until fix applied. These pin the vulnerability where
#  silently skips the tenant filter for empty-string company_id.


@pytest.mark.asyncio
async def test_vc_get_most_recent_for_candidate_empty_string_raises() -> None:
    """get_most_recent_for_candidate with company_id="" MUST raise, not cross-tenant query.

    Vulnerability:  skips filter for falsy values. company_id
    is the ONLY tenant guard here (no vacancy_id in query). Should be fail-closed.
    """
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = VacancyCandidateRepository(session)

    with pytest.raises(ValueError, match="company_id"):
        await repo.get_most_recent_for_candidate(CANDIDATE_ID, company_id="")


@pytest.mark.asyncio
async def test_vc_get_most_recent_for_candidate_none_raises() -> None:
    """get_most_recent_for_candidate with company_id=None MUST raise.

    No company_id = no tenant scope = cross-tenant read. Fail-closed.
    """
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = VacancyCandidateRepository(session)

    with pytest.raises((ValueError, TypeError), match="company_id"):
        await repo.get_most_recent_for_candidate(CANDIDATE_ID, company_id=None)


@pytest.mark.asyncio
async def test_vc_get_for_candidate_and_job_empty_string_raises() -> None:
    """get_for_candidate_and_job with company_id="" MUST raise (cascades to get_most_recent)."""
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = VacancyCandidateRepository(session)

    with pytest.raises(ValueError, match="company_id"):
        await repo.get_for_candidate_and_job(
            str(CANDIDATE_ID), job_vacancy_id=None, company_id=""
        )


@pytest.mark.asyncio
async def test_vc_get_by_vacancy_and_candidate_empty_string_applies_filter() -> None:
    """get_by_vacancy_and_candidate(company_id=) MUST apply company_id filter.

     is not None — the filter should be applied (returns 0 rows, not cross-tenant).
     wrongly skips it;  is correct.
    """
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = VacancyCandidateRepository(session)
    await repo.get_by_vacancy_and_candidate(
        VACANCY_ID, CANDIDATE_ID, company_id=""
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"Empty-string company_id bypassed filter (cross-tenant!): {where_clause}"
    )


@pytest.mark.asyncio
async def test_vc_list_awaiting_screening_empty_string_applies_filter() -> None:
    """list_awaiting_screening_for_vacancy(company_id=) MUST apply filter.

    Same fix as get_by_vacancy_and_candidate: .
    """
    from app.domains.candidates.repositories.vacancy_candidate_repository import (
        VacancyCandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = VacancyCandidateRepository(session)
    await repo.list_awaiting_screening_for_vacancy(
        str(VACANCY_ID), company_id=""
    )

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"Empty-string company_id bypassed filter (cross-tenant!): {where_clause}"
    )


@pytest.mark.asyncio
async def test_candidate_repo_get_by_id_empty_string_applies_filter() -> None:
    """CandidateRepository.get_by_id(company_id=) MUST apply company_id filter."""
    from app.domains.candidates.repositories.candidate_repository import (
        CandidateRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateRepository(session)
    await repo.get_by_id(CANDIDATE_ID, company_id="")

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"Empty-string company_id bypassed filter (cross-tenant!): {where_clause}"
    )


@pytest.mark.asyncio
async def test_favorites_repo_get_empty_string_applies_filter() -> None:
    """CandidateFavoritesRepository.get(company_id=) MUST apply company_id filter."""
    from app.domains.candidates.repositories.candidate_favorites_repository import (
        CandidateFavoritesRepository,
    )

    session = _make_async_session_returning([])
    repo = CandidateFavoritesRepository(session)
    await repo.get(candidate_id="cand-1", user_id="user-1", company_id="")

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"Empty-string company_id bypassed filter (cross-tenant!): {where_clause}"
    )
