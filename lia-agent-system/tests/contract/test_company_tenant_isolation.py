"""company — cross-tenant repository isolation contract tests.

Sensor permanente para os fixes do sprint 2026-05-22 que adicionaram
multi-tenancy defense-in-depth em company repositories.

Pattern canonical: testes pure-unit que inspecionam o `select(...)` SQL
montado, verificando WHERE clause com company_id filter ANTES de execute().

Cobertura:
1. ApproverRepository.get_by_id com company_id filter.
2. BenefitRepository.get_by_id com company_id filter.
3. CompanyBenefitRepository.get_by_id com company_id filter.
4. CompensationPolicyRepository.get_by_id com company_id filter.
5. CultureValueRepository.get_by_id com company_id filter.
6. DepartmentRepository.get_by_id com company_id filter.
7. IdealProfileRepository.get_by_id com company_id filter.

Referência: ADR-001 + REGRA ZERO + HARDENING_PLAN B.1.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


TENANT_A_ID = uuid.UUID("11111111-1111-4111-a111-111111111111")
RESOURCE_ID = uuid.UUID("33333333-3333-4333-a333-333333333333")


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


@pytest.mark.asyncio
async def test_approver_get_by_id_with_company_filters() -> None:
    from app.domains.company.repositories.approver_repository import (
        ApproverRepository,
    )
    session = _make_async_session_returning([])
    repo = ApproverRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_benefit_get_by_id_with_company_filters() -> None:
    from app.domains.company.repositories.benefit_repository import (
        BenefitRepository,
    )
    session = _make_async_session_returning([])
    repo = BenefitRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_company_benefit_get_by_id_with_company_filters() -> None:
    from app.domains.company.repositories.company_benefit_repository import (
        CompanyBenefitRepository,
    )
    session = _make_async_session_returning([])
    repo = CompanyBenefitRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=str(TENANT_A_ID))
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_compensation_policy_get_by_id_with_company_filters() -> None:
    from app.domains.company.repositories.compensation_policy_repository import (
        CompensationPolicyRepository,
    )
    session = _make_async_session_returning([])
    repo = CompensationPolicyRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=str(TENANT_A_ID))
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_culture_value_get_by_id_with_company_filters() -> None:
    from app.domains.company.repositories.culture_value_repository import (
        CultureValueRepository,
    )
    session = _make_async_session_returning([])
    repo = CultureValueRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_department_get_by_id_with_company_filters() -> None:
    from app.domains.company.repositories.department_repository import (
        DepartmentRepository,
    )
    session = _make_async_session_returning([])
    repo = DepartmentRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


@pytest.mark.asyncio
async def test_ideal_profile_get_by_id_with_company_filters() -> None:
    from app.domains.company.repositories.ideal_profile_repository import (
        IdealProfileRepository,
    )
    session = _make_async_session_returning([])
    repo = IdealProfileRepository(session)
    await repo.get_by_id(RESOURCE_ID, company_id=TENANT_A_ID)
    stmt = session.execute.await_args.args[0]
    assert "company_id" in _where_clause(stmt)


# ── Backwards-compat (without company_id) ────────────────────────────────────


@pytest.mark.asyncio
async def test_approver_get_by_id_without_company_omits_filter() -> None:
    """Backwards-compat — Postgres RLS guards via get_tenant_db."""
    from app.domains.company.repositories.approver_repository import (
        ApproverRepository,
    )
    session = _make_async_session_returning([])
    repo = ApproverRepository(session)
    await repo.get_by_id(RESOURCE_ID)  # no company_id
    stmt = session.execute.await_args.args[0]
    assert "company_id" not in _where_clause(stmt)
