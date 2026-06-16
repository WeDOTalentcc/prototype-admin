"""Sprint 7C Part 1.5c — POST /talent-pools/{pool_id}/agents/{assignment_id}/run canonical.

Substituiu stub Sprint 7A. Wire dispatch_pool_agent_assignment_task.delay().
Pré-validate assignment existe + cross-tenant pool_id match.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db


def _fake_assignment(assignment_id, pool_id, company_id):
    a = MagicMock()
    a.id = assignment_id
    a.company_id = company_id
    a.talent_pool_id = pool_id
    a.custom_agent_id = uuid.uuid4()
    return a


async def test_post_dispatch_wires_celery_task_and_returns_queued(mock_db):
    """Test 7: POST .../run wire dispatch_pool_agent_assignment_task.delay + retorna run_id|status."""
    from app.api.v1 import talent_pool_agents as tpa

    pool_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    company_id = "comp-7c-2"

    assign_repo = MagicMock()
    assign_repo.get_by_id = AsyncMock(
        return_value=_fake_assignment(assignment_id, pool_id, company_id)
    )

    with patch.object(
        tpa, "PoolAgentAssignmentRepository", return_value=assign_repo
    ), patch.object(tpa, "dispatch_pool_agent_assignment_task") as mock_task:
        mock_task.delay = MagicMock()
        result = await tpa.dispatch_on_demand(
            pool_id=pool_id,
            assignment_id=assignment_id,
            current_user=MagicMock(),
            db=mock_db,
            company_id=company_id,
        )

    # Celery task dispatched canonical
    mock_task.delay.assert_called_once()
    kwargs = mock_task.delay.call_args.kwargs
    assert kwargs["assignment_id"] == assignment_id
    assert kwargs["trigger_source"] == "on_demand"

    # Response shape canonical
    assert result["status"] == "queued"
    assert result["assignment_id"] == assignment_id
    # NÃO deve mais ter sprint marker 7A-stub
    assert "sprint" not in result or result.get("sprint") != "7A-stub"


async def test_post_dispatch_cross_tenant_404(mock_db):
    """Test 8: cross-tenant assignment_id → 404 (não vaza outro tenant)."""
    from app.api.v1 import talent_pool_agents as tpa

    pool_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    company_id = "comp-7c-3"

    assign_repo = MagicMock()
    assign_repo.get_by_id = AsyncMock(return_value=None)  # outro tenant ou inexistente

    with patch.object(
        tpa, "PoolAgentAssignmentRepository", return_value=assign_repo
    ), patch.object(tpa, "dispatch_pool_agent_assignment_task") as mock_task:
        mock_task.delay = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await tpa.dispatch_on_demand(
                pool_id=pool_id,
                assignment_id=assignment_id,
                current_user=MagicMock(),
                db=mock_db,
                company_id=company_id,
            )
        assert exc_info.value.status_code == 404

    # Não despachou
    mock_task.delay.assert_not_called()
