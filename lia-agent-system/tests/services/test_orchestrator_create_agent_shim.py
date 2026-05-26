"""Sprint 7B-3b Part 1 Fase B — create_agent refactor (CustomAgent canonical).

Tests Red→Green pra create_agent que escreve CustomAgent + PoolAgentAssignment
preservando dict return shape (backward compat /sourcing-agents POST).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


async def test_create_agent_writes_custom_agent(mock_db):
    """create_agent escreve CustomAgent (category='sourcing'), não SourcingAgent legacy."""
    from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator
    from lia_models.custom_agent import CustomAgent

    orch = SourcingAgentOrchestrator()
    with patch.object(orch, "_extract_strategy_from_job", new=AsyncMock(return_value={"required_skills": ["py"]})):
        result = await orch.create_agent(
            company_id="comp-1",
            agent_name="Test Agent",
            job_id="job-1",
            db=mock_db,
        )

    # db.add foi chamado pelo menos uma vez com CustomAgent
    added = [c.args[0] for c in mock_db.add.call_args_list]
    assert any(isinstance(a, CustomAgent) for a in added), \
        f"CustomAgent não foi adicionado. Adicionados: {[type(a).__name__ for a in added]}"

    ca = next(a for a in added if isinstance(a, CustomAgent))
    assert ca.category == "sourcing"
    assert ca.company_id == "comp-1"


async def test_create_agent_with_talent_pool_creates_assignment(mock_db):
    """talent_pool_id provided → cria PoolAgentAssignment."""
    from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator
    from lia_models.custom_agent import CustomAgent
    from lia_models.pool_agent_assignment import PoolAgentAssignment

    orch = SourcingAgentOrchestrator()
    await orch.create_agent(
        company_id="comp-1",
        agent_name="Pool Agent",
        talent_pool_id="pool-1",
        search_strategy={"required_skills": []},
        db=mock_db,
    )

    added = [c.args[0] for c in mock_db.add.call_args_list]
    types_added = [type(a).__name__ for a in added]
    assert "CustomAgent" in types_added, f"CustomAgent missing. Added: {types_added}"
    assert "PoolAgentAssignment" in types_added, f"PoolAgentAssignment missing. Added: {types_added}"


async def test_create_agent_with_template_copies_system_prompt(mock_db):
    """agent_template_id provided → copia system_prompt do template (ou marker)."""
    from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator
    from lia_models.custom_agent import CustomAgent

    orch = SourcingAgentOrchestrator()
    # template lookup será via dbexec — mockamos com prompt
    fake_template = MagicMock()
    fake_template.system_prompt = "Template prompt canonical X"

    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=fake_template)
    mock_db.execute = AsyncMock(return_value=exec_result)

    await orch.create_agent(
        company_id="comp-1",
        agent_name="Tmpl Agent",
        agent_template_id="tmpl-1",
        search_strategy={"required_skills": []},
        db=mock_db,
    )

    added = [c.args[0] for c in mock_db.add.call_args_list]
    ca = next(a for a in added if isinstance(a, CustomAgent))
    assert "Template prompt canonical X" in (ca.system_prompt or "")


async def test_create_agent_returns_dict_backward_compat(mock_db):
    """Return shape: {agent_id, status, strategy} dict (NÃO model)."""
    from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator

    orch = SourcingAgentOrchestrator()
    result = await orch.create_agent(
        company_id="comp-1",
        agent_name="Test",
        search_strategy={"required_skills": ["py"]},
        db=mock_db,
    )

    assert isinstance(result, dict)
    assert set(result.keys()) >= {"agent_id", "status", "strategy"}
    assert isinstance(result["agent_id"], str)
    assert result["strategy"] == {"required_skills": ["py"]}
