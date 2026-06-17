"""tail modules — cross-tenant repository isolation contract tests (Sprint B.1 tail).

Sensor permanente para os fixes do sprint 2026-05-22 (Wave B.1 tail) que adicionaram
multi-tenancy defense-in-depth em repositorios de modulos tail:
  - notifications/alert_repository (AlertConfig, AlertPreference)
  - ai/agent_template_repository (AgentTemplate marketplace pattern)
  - ai/ai_consumption_repository (AiConsumption)
  - integrations_hub/integrations_hub_repository (IntegrationConnection)
  - goals/goals_repository (Goal, GoalTemplate)
  - email_templates/email_templates_repository (EmailTemplate)
  - lgpd/data_incident_repository (DataIncident)
  - journey_mapping/journey_mapping_repository (JourneyBlueprint)

Pattern canonical: pure-unit tests que inspecionam o `select(...)` SQL
montado, verificando WHERE clause com company_id filter quando passado,
e ausencia (backwards-compat) quando omitido.

Referencia:
  - ADR-001 Repository Pattern
  - REGRA ZERO multi-tenancy fail-closed
  - HARDENING_PLAN B.1 sensor `scripts/check_query_has_tenant_filter.py`
  - CLAUDE.md "Multi-tenancy" non-negotiable rule
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


TENANT_A_ID = "11111111-1111-4111-a111-111111111111"
TENANT_B_ID = "22222222-2222-4222-a222-222222222222"
RECORD_ID = uuid.UUID("33333333-3333-4333-a333-333333333333")


def _make_async_session_returning(rows: list | None = None) -> MagicMock:
    """Build a mock AsyncSession that returns the given rows on execute."""
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalar = MagicMock(return_value=0)
    result.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=rows or []))
    )
    result.first = MagicMock(return_value=None)
    result.all = MagicMock(return_value=[])
    session.execute = AsyncMock(return_value=result)
    return session


def _where_clause(stmt) -> str:
    """Extract WHERE clause text from a compiled SQLAlchemy statement."""
    sql = str(stmt.compile(compile_kwargs={"literal_binds": False})).lower()
    where_idx = sql.find("where ")
    assert where_idx >= 0, f"No WHERE clause in SQL: {sql}"
    return sql[where_idx:]


# ── notifications/alert_repository ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_alert_get_config_by_id_with_company_filters() -> None:
    """AlertRepository.get_config_by_id MUST add company_id filter when passed."""
    from app.repositories.alert_repository import (
        AlertRepository,
    )

    session = _make_async_session_returning([])
    repo = AlertRepository(session)
    await repo.get_config_by_id(RECORD_ID, company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause, (
        f"company_id NOT in WHERE: {where_clause}"
    )


@pytest.mark.asyncio
async def test_alert_get_preference_with_company_filters() -> None:
    """AlertRepository.get_preference MUST add company_id filter when passed."""
    from app.repositories.alert_repository import (
        AlertRepository,
    )

    session = _make_async_session_returning([])
    repo = AlertRepository(session)
    await repo.get_preference(user_id="user-a", company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause


# ── ai/agent_template_repository ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_template_get_by_id_with_company_filters_marketplace() -> None:
    """AgentTemplateRepository.get_by_id with company_id filters OR(company, is_global)."""
    from app.domains.ai.repositories.agent_template_repository import (
        AgentTemplateRepository,
    )

    session = _make_async_session_returning([])
    repo = AgentTemplateRepository(session)
    await repo.get_by_id(RECORD_ID, company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    # Marketplace: filter must mention company_id with OR(IS NULL) marketplace pattern
    assert "company_id" in where_clause
    # Marketplace pattern: company_id == X OR company_id IS NULL (WeDO public)
    assert "is null" in where_clause or "is_(none)" in where_clause, (
        f"Marketplace OR company_id IS NULL pattern missing: {where_clause}"
    )


# ── ai/ai_consumption_repository ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_consumption_get_by_id_with_company_filters() -> None:
    """AiConsumptionRepository.get_by_id MUST add company_id filter when passed."""
    from app.domains.ai.repositories.ai_consumption_repository import (
        AiConsumptionRepository,
    )

    session = _make_async_session_returning([])
    repo = AiConsumptionRepository(session)
    await repo.get_by_id(RECORD_ID, company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause


# ── integrations_hub/integrations_hub_repository ────────────────────────────


@pytest.mark.asyncio
async def test_integrations_hub_get_connection_by_id_with_company_filters() -> None:
    """IntegrationsHubRepository.get_connection_by_id MUST add company_id filter when passed."""
    from app.domains.integrations_hub.repositories.integrations_hub_repository import (
        IntegrationsHubRepository,
    )

    session = _make_async_session_returning([])
    repo = IntegrationsHubRepository(session)
    await repo.get_connection_by_id(str(RECORD_ID), company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause


# ── goals/goals_repository ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_goals_get_by_id_with_company_filters() -> None:
    """GoalsRepository.get_by_id MUST add company_id filter when passed."""
    from app.repositories.goals_repository import (
        GoalsRepository,
    )

    session = _make_async_session_returning([])
    repo = GoalsRepository(session)
    await repo.get_by_id(RECORD_ID, company_id=uuid.UUID(TENANT_A_ID))

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause


@pytest.mark.asyncio
async def test_goals_list_goals_with_company_filters() -> None:
    """GoalsRepository.list_goals MUST add company_id filter when passed."""
    from app.repositories.goals_repository import (
        GoalsRepository,
    )

    session = _make_async_session_returning([])
    repo = GoalsRepository(session)
    await repo.list_goals(company_id=uuid.UUID(TENANT_A_ID))

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause


# ── email_templates/email_templates_repository ──────────────────────────────


@pytest.mark.asyncio
async def test_email_templates_get_by_id_with_company_filters() -> None:
    """EmailTemplatesRepository.get_by_id MUST add company_id filter when passed."""
    from app.repositories.email_templates_repository import (
        EmailTemplatesRepository,
    )

    session = _make_async_session_returning([])
    repo = EmailTemplatesRepository(session)
    await repo.get_by_id(RECORD_ID, company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    # email_templates uses marketplace OR(company_id, IS NULL) pattern
    assert "company_id" in where_clause


# ── lgpd/data_incident_repository ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_data_incident_get_by_id_with_company_filters() -> None:
    """DataIncidentRepository.get_by_id MUST add company_id filter when passed."""
    from app.domains.lgpd.repositories.data_incident_repository import (
        DataIncidentRepository,
    )

    session = _make_async_session_returning([])
    repo = DataIncidentRepository(session)
    await repo.get_by_id(str(RECORD_ID), company_id=TENANT_A_ID)

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause


# ── journey_mapping/journey_mapping_repository ──────────────────────────────


@pytest.mark.asyncio
async def test_journey_mapping_get_blueprint_with_company_filters() -> None:
    """JourneyMappingRepository.get_blueprint MUST add company_id filter when passed."""
    from app.repositories.journey_mapping_repository import (
        JourneyMappingRepository,
    )

    session = _make_async_session_returning([])
    repo = JourneyMappingRepository(session)
    await repo.get_blueprint(RECORD_ID, company_id=uuid.UUID(TENANT_A_ID))

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" in where_clause


# ── Backwards-compat — without company_id, no tenant filter (RLS) ───────────


@pytest.mark.asyncio
async def test_alert_get_config_by_id_without_company_omits_filter() -> None:
    """get_config_by_id without company_id — backwards-compat path."""
    from app.repositories.alert_repository import (
        AlertRepository,
    )

    session = _make_async_session_returning([])
    repo = AlertRepository(session)
    await repo.get_config_by_id(RECORD_ID)  # no company_id

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" not in where_clause, (
        f"company_id appeared unexpectedly: {where_clause}"
    )


@pytest.mark.asyncio
async def test_goals_get_by_id_without_company_omits_filter() -> None:
    """GoalsRepository.get_by_id without company_id — backwards-compat path."""
    from app.repositories.goals_repository import (
        GoalsRepository,
    )

    session = _make_async_session_returning([])
    repo = GoalsRepository(session)
    await repo.get_by_id(RECORD_ID)  # no company_id

    session.execute.assert_awaited_once()
    stmt = session.execute.await_args.args[0]
    where_clause = _where_clause(stmt)
    assert "company_id" not in where_clause
