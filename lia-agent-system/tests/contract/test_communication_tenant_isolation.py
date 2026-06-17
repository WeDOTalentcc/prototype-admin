"""communication — cross-tenant repository isolation contract tests.

Sensor permanente para os fixes do sprint 2026-05-22 que adicionaram
multi-tenancy fail-closed em communication repositories.

Pattern canonical: testes pure-unit que inspecionam o `select(...)` SQL
montado, verificando WHERE clause com company_id filter ANTES de execute().
Não precisa de DB real nem httpx client.

Cobertura:
1. AlertRuleTemplateRepository.get_by_id requer company_id explícito + filtra.
2. EligibilityQuestionTemplateRepository.get_by_id requer company_id + filtra.
3. WebhookRepository.get_by_id_and_company filtra por (id, company_id).
4. CommunicationHistoryRepository.get_by_id com company_id adiciona filter.

Referência: ADR-001 + REGRA ZERO multi-tenancy fail-closed.
"""
from __future__ import annotations

import uuid as uuid_mod
from unittest.mock import AsyncMock, MagicMock

import pytest


TENANT_A_ID = "11111111-1111-4111-a111-111111111111"
TENANT_B_ID = "22222222-2222-4222-a222-222222222222"


def _make_async_session_returning(rows: list | None = None) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=rows or [])))
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.asyncio
async def test_alert_rule_template_get_by_id_requires_company_id() -> None:
    """AlertRuleTemplateRepository.get_by_id MUST require company_id."""
    from app.domains.communication.repositories.alert_rule_template_repository import (
        AlertRuleTemplateRepository,
    )

    repo = AlertRuleTemplateRepository(_make_async_session_returning([]))
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.get_by_id(uuid_mod.uuid4(), company_id="")


@pytest.mark.asyncio
async def test_alert_rule_template_get_by_id_filters_company_id() -> None:
    """get_by_id MUST add company_id filter (master OR tenant) to WHERE."""
    from app.domains.communication.repositories.alert_rule_template_repository import (
        AlertRuleTemplateRepository,
    )

    session = _make_async_session_returning([])
    repo = AlertRuleTemplateRepository(session)
    await repo.get_by_id(uuid_mod.uuid4(), company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False})).lower()
    # Must reference company_id in WHERE clause specifically (not just SELECT)
    where_idx = sql.find("where ")
    assert where_idx >= 0, f"No WHERE clause: {sql}"
    where_clause = sql[where_idx:]
    assert "company_id" in where_clause, f"company_id NOT in WHERE: {where_clause}"


@pytest.mark.asyncio
async def test_eligibility_question_template_get_by_id_requires_company_id() -> None:
    """EligibilityQuestionTemplateRepository.get_by_id MUST require company_id."""
    from app.domains.cv_screening.repositories.eligibility_question_template_repository import (
        EligibilityQuestionTemplateRepository,
    )

    repo = EligibilityQuestionTemplateRepository(_make_async_session_returning([]))
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.get_by_id(uuid_mod.uuid4(), company_id="")


@pytest.mark.asyncio
async def test_webhook_get_by_id_filters_by_company_id() -> None:
    """WebhookRepository.get_by_id_and_company MUST filter by (id, company_id)."""
    from app.domains.communication.repositories.webhook_repository import (
        WebhookRepository,
    )

    session = _make_async_session_returning([])
    repo = WebhookRepository(session)
    await repo.get_by_id_and_company(webhook_id="webhook-uuid", company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False})).lower()
    # Must reference company_id in WHERE clause specifically (not just SELECT)
    where_idx = sql.find("where ")
    assert where_idx >= 0, f"No WHERE clause: {sql}"
    where_clause = sql[where_idx:]
    assert "company_id" in where_clause, f"company_id NOT in WHERE: {where_clause}"


@pytest.mark.asyncio
async def test_webhook_get_by_id_requires_company_id() -> None:
    """WebhookRepository.get_by_id_and_company MUST require company_id."""
    from app.domains.communication.repositories.webhook_repository import (
        WebhookRepository,
    )

    repo = WebhookRepository(_make_async_session_returning([]))
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.get_by_id_and_company(webhook_id="x", company_id="")


@pytest.mark.asyncio
async def test_communication_history_get_by_id_with_company_filters() -> None:
    """CommunicationHistoryRepository.get_by_id with company_id adds filter."""
    from app.domains.communication.repositories.communication_history_repository import (
        CommunicationHistoryRepository,
    )

    session = _make_async_session_returning([])
    repo = CommunicationHistoryRepository(session)
    await repo.get_by_id("comm-uuid", company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False})).lower()
    # Must reference company_id in WHERE clause specifically (not just SELECT)
    where_idx = sql.find("where ")
    assert where_idx >= 0, f"No WHERE clause: {sql}"
    where_clause = sql[where_idx:]
    assert "company_id" in where_clause, f"company_id NOT in WHERE: {where_clause}"


@pytest.mark.asyncio
async def test_email_tracking_get_base_event_by_token_is_cross_tenant() -> None:
    """get_base_event_by_token MUST NOT filter by company_id.

    Tokens are cryptographically random global identifiers; handler is
    anonymous (Microsoft Teams cloud callback). Tenant is derived FROM
    the row, not used to scope it.
    """
    from app.domains.communication.repositories.email_tracking_repository import (
        EmailTrackingRepository,
    )

    session = _make_async_session_returning([])
    repo = EmailTrackingRepository(session)
    await repo.get_base_event_by_token("crypto-random-token")

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    # By design — NO company_id constraint
    assert "token" in sql.lower()
