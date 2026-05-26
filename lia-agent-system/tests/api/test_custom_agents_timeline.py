"""Sprint 7B-3b Part 1 Fase B — endpoint timeline canonical (CustomAgent).

Tests Red→Green pra GET /api/v1/custom-agents/{id}/timeline shim transicional.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


async def test_timeline_resolves_via_or_shim(mock_db):
    """GET /custom-agents/{id}/timeline resolve agent via OR shim (custom_agent.id OR legacy_sourcing_agent_id)."""
    from app.api.v1 import custom_agents as ca_module

    # Mock get_agent_timeline retornando 1 evento real-shape
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_agent_timeline = AsyncMock(return_value=[{
        "id": "evt-1",
        "icon": "✅",
        "type": "positive",
        "reason": "good fit python",
        "criteria": ["python"],
        "candidate_id": "cand-1",
        "created_at": "2026-05-26T00:00:00",
    }])

    # Mock agent lookup
    fake_agent = MagicMock()
    fake_agent.id = "custom-uuid-1"
    fake_agent.company_id = "comp-1"
    fake_agent.category = "sourcing"

    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=fake_agent)
    mock_db.execute = AsyncMock(return_value=exec_result)

    with patch.object(ca_module, "sourcing_agent_orchestrator", mock_orchestrator):
        result = await ca_module.get_custom_agent_timeline(
            agent_id="custom-uuid-1",
            company_id="comp-1",
            db=mock_db,
        )

    assert "timeline" in result
    assert len(result["timeline"]) == 1
    assert result["timeline"][0].type == "positive"
    assert result["timeline"][0].id == "evt-1"


async def test_timeline_cross_tenant_404(mock_db):
    """Agent de outra company retorna 404."""
    from fastapi import HTTPException

    from app.api.v1 import custom_agents as ca_module

    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=exec_result)

    with pytest.raises(HTTPException) as exc_info:
        await ca_module.get_custom_agent_timeline(
            agent_id="other-tenant-id",
            company_id="comp-1",
            db=mock_db,
        )
    assert exc_info.value.status_code == 404


async def test_timeline_response_shape_canonical(mock_db):
    """Response: {'timeline': [AgentTimelineEventResponse, ...]} envelope."""
    from app.api.v1 import custom_agents as ca_module
    from app.schemas.agent_timeline import AgentTimelineEventResponse

    mock_orchestrator = MagicMock()
    mock_orchestrator.get_agent_timeline = AsyncMock(return_value=[
        {
            "id": "e1",
            "icon": "❌",
            "type": "negative",
            "reason": "no react exp",
            "criteria": ["react"],
            "candidate_id": "c1",
            "created_at": "2026-05-26T01:00:00",
        },
    ])

    fake_agent = MagicMock()
    fake_agent.id = "uuid-x"
    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=fake_agent)
    mock_db.execute = AsyncMock(return_value=exec_result)

    with patch.object(ca_module, "sourcing_agent_orchestrator", mock_orchestrator):
        result = await ca_module.get_custom_agent_timeline(
            agent_id="uuid-x",
            company_id="comp-1",
            db=mock_db,
        )

    assert isinstance(result, dict)
    assert isinstance(result["timeline"], list)
    assert all(isinstance(ev, AgentTimelineEventResponse) for ev in result["timeline"])
