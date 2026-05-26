"""Sprint 7C Part 1.5a — GET /talent-pools/{pool_id}/agents/{assignment_id}/runs canonical.

Substituiu stub Sprint 7A. Mock-based, foca em wiring + cross-tenant + empty list.
Repo integration coverage vive em tests/contract/test_pool_agent_run_repo.py.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
    return a


def _fake_run(run_id, assignment_id, company_id, status_value="success"):
    r = MagicMock()
    r.id = run_id
    r.assignment_id = assignment_id
    r.company_id = company_id
    r.trigger_source = "cron"
    r.status = status_value
    r.started_at = datetime.now(timezone.utc)
    r.finished_at = datetime.now(timezone.utc)
    r.dispatch_metadata = {"cron_expression": "0 9 * * *"}
    r.results = {"candidates_evaluated": 7}
    r.runtime_metrics = {"latency_ms": 3100}
    r.error_message = None
    r.created_at = datetime.now(timezone.utc)
    r.updated_at = datetime.now(timezone.utc)
    return r


async def test_list_runs_returns_canonical_list(mock_db):
    """GET .../runs retorna lista de PoolAgentRunResponse canonical."""
    from app.api.v1 import talent_pool_agents as tpa

    pool_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    company_id = "comp-7c-1"
    run_id = uuid.uuid4()

    assign_repo = MagicMock()
    assign_repo.get_by_id = AsyncMock(
        return_value=_fake_assignment(assignment_id, pool_id, company_id)
    )
    run_repo = MagicMock()
    run_repo.list_by_assignment = AsyncMock(
        return_value=[_fake_run(run_id, assignment_id, company_id)]
    )

    with patch.object(
        tpa, "PoolAgentAssignmentRepository", return_value=assign_repo
    ), patch.object(tpa, "PoolAgentRunRepository", return_value=run_repo):
        result = await tpa.list_runs(
            pool_id=pool_id,
            assignment_id=assignment_id,
            limit=50,
            offset=0,
            current_user=MagicMock(),
            db=mock_db,
            company_id=company_id,
        )

    assert isinstance(result, list)
    assert len(result) == 1
    assert str(result[0].id) == str(run_id)
    assert result[0].trigger_source == "cron"
    assert result[0].status == "success"
    run_repo.list_by_assignment.assert_awaited_once()


async def test_list_runs_cross_tenant_returns_404(mock_db):
    """Assignment não encontrado (tenant mismatch via repo) => 404 canonical."""
    from fastapi import HTTPException

    from app.api.v1 import talent_pool_agents as tpa

    pool_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())

    assign_repo = MagicMock()
    assign_repo.get_by_id = AsyncMock(return_value=None)  # tenant gate

    with patch.object(
        tpa, "PoolAgentAssignmentRepository", return_value=assign_repo
    ):
        with pytest.raises(HTTPException) as exc:
            await tpa.list_runs(
                pool_id=pool_id,
                assignment_id=assignment_id,
                limit=50,
                offset=0,
                current_user=MagicMock(),
                db=mock_db,
                company_id="other-tenant",
            )
    assert exc.value.status_code == 404
    assert "assignment_not_found" in str(exc.value.detail)


async def test_list_runs_empty_when_no_runs(mock_db):
    """Quando 0 runs no histórico => lista vazia (não 404)."""
    from app.api.v1 import talent_pool_agents as tpa

    pool_id = str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    company_id = "comp-7c-empty"

    assign_repo = MagicMock()
    assign_repo.get_by_id = AsyncMock(
        return_value=_fake_assignment(assignment_id, pool_id, company_id)
    )
    run_repo = MagicMock()
    run_repo.list_by_assignment = AsyncMock(return_value=[])

    with patch.object(
        tpa, "PoolAgentAssignmentRepository", return_value=assign_repo
    ), patch.object(tpa, "PoolAgentRunRepository", return_value=run_repo):
        result = await tpa.list_runs(
            pool_id=pool_id,
            assignment_id=assignment_id,
            limit=50,
            offset=0,
            current_user=MagicMock(),
            db=mock_db,
            company_id=company_id,
        )

    assert result == []
