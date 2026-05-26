"""Sprint 7B-3b Part 3b v2 — endpoints canonical novos no custom_agents.py.

4 endpoints adicionados (substituem legacy sourcing_agents.py que será deletado):
- GET /api/v1/custom-agents/{id}/calibration-candidates
- POST /api/v1/custom-agents/{id}/feedback
- POST /api/v1/custom-agents/{id}/pause
- POST /api/v1/custom-agents/{id}/resume

Reuse orchestrator (get_calibration_candidates, process_feedback) + studio_audit dim 5.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db


def _fake_agent(agent_id="agent-1", company_id="comp-1", status_value="active"):
    a = MagicMock()
    a.id = agent_id
    a.company_id = company_id
    a.category = "sourcing"
    a.status = status_value
    return a


async def test_calibration_candidates_canonical_returns_list(mock_db):
    """GET /custom-agents/{id}/calibration-candidates reusa orchestrator + retorna {candidates: [...]}."""
    from app.api.v1 import custom_agents as ca_module

    mock_orch = MagicMock()
    mock_orch.get_calibration_candidates = AsyncMock(return_value=[
        {"id": "c1", "name": "Alice"},
        {"id": "c2", "name": "Bob"},
    ])
    with patch.object(ca_module, "sourcing_agent_orchestrator", mock_orch):
        result = await ca_module.get_custom_agent_calibration_candidates(
            agent_id="agent-1",
            limit=10,
            company_id="comp-1",
            db=mock_db,
        )
    assert "candidates" in result
    assert len(result["candidates"]) == 2
    mock_orch.get_calibration_candidates.assert_awaited_once()
    call_kwargs = mock_orch.get_calibration_candidates.call_args.kwargs
    assert call_kwargs.get("agent_id") == "agent-1"
    assert call_kwargs.get("company_id") == "comp-1"


async def test_feedback_canonical_reuses_orchestrator_and_audits(mock_db):
    """POST /custom-agents/{id}/feedback reusa process_feedback + emite studio_audit dim 5."""
    from app.api.v1 import custom_agents as ca_module

    fake_result = MagicMock()
    fake_result.calibration_version = 2
    fake_result.strategy_updated = True
    fake_result.new_exclusions = ["x"]
    fake_result.new_positive_signals = ["y"]
    fake_result.approved_count = 3
    fake_result.rejected_count = 1

    mock_orch = MagicMock()
    mock_orch.process_feedback = AsyncMock(return_value=fake_result)

    audit_calls = []

    async def fake_studio_audit(**kwargs):
        audit_calls.append(kwargs)

    body = ca_module.FeedbackCanonicalRequest(
        candidate_id="cand-1",
        signal_type="positive",
        reason="great fit python",
    )

    current_user = MagicMock()
    current_user.id = "user-1"
    current_user.company_id = "comp-1"

    with patch.object(ca_module, "sourcing_agent_orchestrator", mock_orch),          patch("app.domains.agent_studio._audit_helper.studio_audit", side_effect=fake_studio_audit):
        result = await ca_module.submit_custom_agent_feedback(
            agent_id="agent-1",
            body=body,
            company_id="comp-1",
            current_user=current_user,
            db=mock_db,
        )

    assert result["calibration_version"] == 2
    assert result["strategy_updated"] is True
    mock_orch.process_feedback.assert_awaited_once()
    # Audit dim 5 emitted
    assert len(audit_calls) >= 1
    assert audit_calls[0]["action"] == "custom_agent_feedback"
    assert audit_calls[0]["company_id"] == "comp-1"


async def test_pause_canonical_updates_status_and_audits(mock_db):
    """POST /custom-agents/{id}/pause => status=paused + studio_audit dim 5."""
    from app.api.v1 import custom_agents as ca_module

    fake_agent = _fake_agent(status_value="active")
    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=fake_agent)
    mock_db.execute = AsyncMock(return_value=exec_result)

    audit_calls = []

    async def fake_studio_audit(**kwargs):
        audit_calls.append(kwargs)

    current_user = MagicMock()
    current_user.id = "user-1"
    current_user.company_id = "comp-1"

    with patch("app.domains.agent_studio._audit_helper.studio_audit", side_effect=fake_studio_audit):
        result = await ca_module.pause_custom_agent(
            agent_id="agent-1",
            company_id="comp-1",
            current_user=current_user,
            db=mock_db,
        )
    assert fake_agent.status == "paused"
    mock_db.commit.assert_awaited()
    assert result["status"] == "paused"
    assert any(c["action"] == "custom_agent_paused" for c in audit_calls)


async def test_resume_canonical_updates_status_and_audits(mock_db):
    """POST /custom-agents/{id}/resume => status=active + studio_audit dim 5."""
    from app.api.v1 import custom_agents as ca_module

    fake_agent = _fake_agent(status_value="paused")
    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=fake_agent)
    mock_db.execute = AsyncMock(return_value=exec_result)

    audit_calls = []

    async def fake_studio_audit(**kwargs):
        audit_calls.append(kwargs)

    current_user = MagicMock()
    current_user.id = "user-1"
    current_user.company_id = "comp-1"

    with patch("app.domains.agent_studio._audit_helper.studio_audit", side_effect=fake_studio_audit):
        result = await ca_module.resume_custom_agent(
            agent_id="agent-1",
            company_id="comp-1",
            current_user=current_user,
            db=mock_db,
        )
    assert fake_agent.status == "active"
    mock_db.commit.assert_awaited()
    assert result["status"] == "active"
    assert any(c["action"] == "custom_agent_resumed" for c in audit_calls)


async def test_pause_cross_tenant_404(mock_db):
    """Agent inexistente / outro tenant => HTTPException 404."""
    from fastapi import HTTPException

    from app.api.v1 import custom_agents as ca_module

    exec_result = MagicMock()
    exec_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=exec_result)

    current_user = MagicMock()
    current_user.id = "user-1"
    current_user.company_id = "comp-1"

    with pytest.raises(HTTPException) as exc_info:
        await ca_module.pause_custom_agent(
            agent_id="other-tenant",
            company_id="comp-1",
            current_user=current_user,
            db=mock_db,
        )
    assert exc_info.value.status_code == 404
