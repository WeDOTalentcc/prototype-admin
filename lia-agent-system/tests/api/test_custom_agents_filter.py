"""Sprint 7B-3b Part 2 v2 — backend filter extension canonical.

Tests Red→Green pra GET /api/v1/custom-agents com talent_pool_id + job_id
query params. Filter computacional (JOIN canonical PoolAgentAssignment +
JSONB config->>job_id), não in-memory.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


def _mock_execute_returning(agents):
    """Helper: mock db.execute returning a result whose .scalars().all() = agents."""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all = MagicMock(return_value=agents)
    result.scalars = MagicMock(return_value=scalars)
    result.scalar = MagicMock(return_value=len(agents))
    return result


async def test_list_agents_filter_by_talent_pool_id(mock_db):
    """talent_pool_id=X devolve apenas agents com PoolAgentAssignment(pool=X)."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    fake_agents = [MagicMock(id="agent-1"), MagicMock(id="agent-2")]
    mock_db.execute = AsyncMock(side_effect=[
        _mock_execute_returning(fake_agents),  # count
        _mock_execute_returning(fake_agents),  # list
    ])

    agents, total = await svc.list_agents(
        db=mock_db,
        company_id="comp-1",
        talent_pool_id="pool-abc",
    )

    assert total == 2
    assert len(agents) == 2
    # Inspecionar SQL emitida pra confirmar JOIN canonical
    call_args = mock_db.execute.await_args_list[0].args[0]
    sql = str(call_args).lower()
    assert "pool_agent_assignments" in sql, "deve fazer JOIN canonical PoolAgentAssignment"
    assert "talent_pool_id" in sql


async def test_list_agents_filter_by_job_id(mock_db):
    """job_id=X devolve apenas agents com config->>job_id == X."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    fake_agents = [MagicMock(id="agent-1")]
    mock_db.execute = AsyncMock(side_effect=[
        _mock_execute_returning(fake_agents),
        _mock_execute_returning(fake_agents),
    ])

    agents, total = await svc.list_agents(
        db=mock_db,
        company_id="comp-1",
        job_id="job-xyz",
    )

    assert total == 1
    call_args = mock_db.execute.await_args_list[0].args[0]
    sql = str(call_args).lower()
    # JSONB config->>job_id deve aparecer na query (operador ->> SQLAlchemy)
    assert "config" in sql
    assert "->>" in sql


async def test_list_agents_filter_combined_pool_and_category(mock_db):
    """talent_pool_id + category combinados aplicam ambas restrições."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    fake_agents = [MagicMock(id="agent-1")]
    mock_db.execute = AsyncMock(side_effect=[
        _mock_execute_returning(fake_agents),
        _mock_execute_returning(fake_agents),
    ])

    agents, total = await svc.list_agents(
        db=mock_db,
        company_id="comp-1",
        talent_pool_id="pool-abc",
        category="sourcing",
    )

    assert total == 1
    call_args = mock_db.execute.await_args_list[0].args[0]
    sql = str(call_args).lower()
    assert "pool_agent_assignments" in sql
    assert "category" in sql


async def test_list_agents_default_no_filter_when_params_absent(mock_db):
    """Ausência de talent_pool_id+job_id preserva behavior original (sem JOIN)."""
    from app.services.agent_marketplace_service import AgentMarketplaceService

    svc = AgentMarketplaceService()
    fake_agents = [MagicMock(id="a-1"), MagicMock(id="a-2"), MagicMock(id="a-3")]
    mock_db.execute = AsyncMock(side_effect=[
        _mock_execute_returning(fake_agents),
        _mock_execute_returning(fake_agents),
    ])

    agents, total = await svc.list_agents(
        db=mock_db,
        company_id="comp-1",
    )

    assert total == 3
    call_args = mock_db.execute.await_args_list[0].args[0]
    sql = str(call_args).lower()
    # SEM JOIN — query simples sobre custom_agents
    assert "pool_agent_assignments" not in sql
