"""W4-032 P0 · TDD tests · HITL gate em ats_integration + autonomous + kanban.

Verifica:
1. Helper `maybe_request_hitl_approval` importável.
2. Cada P0 agent declara `_HITL_ACTION_TYPES` com action_types canonical.
3. Helper retorna None se action_type não match (passthrough).
4. Helper retorna None se `hitl_approved=True` (já approved).
5. Helper retorna AgentOutput "Aguardando..." quando gate triggered (mock HITL).
6. Helper é fail-open (passthrough) em DB error.
7. Each P0 agent.process imports `maybe_request_hitl_approval`.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_helper_importable():
    """W4-032 · maybe_request_hitl_approval canonical importável."""
    from app.shared.hitl.agent_gate import maybe_request_hitl_approval
    assert callable(maybe_request_hitl_approval)


def test_ats_integration_hitl_action_types():
    """W4-032 P0 · ats_integration declara _HITL_ACTION_TYPES canonical."""
    from app.domains.ats_integration.agents.ats_integration_react_agent import (
        ATSIntegrationReActAgent,
    )
    expected = {
        "sync_to_ats", "webhook_trigger", "ats_create_application",
        "ats_update_application", "ats_reject_application",
    }
    assert expected.issubset(set(ATSIntegrationReActAgent._HITL_ACTION_TYPES))


def test_kanban_hitl_action_types():
    """W4-032 P0 · kanban declara _HITL_ACTION_TYPES canonical."""
    from app.domains.recruiter_assistant.agents.kanban_react_agent import (
        KanbanReActAgent,
    )
    expected = {
        "move_candidate", "bulk_move", "bulk_reject",
        "bulk_advance", "reject_candidate",
    }
    assert expected.issubset(set(KanbanReActAgent._HITL_ACTION_TYPES))


@pytest.mark.asyncio
async def test_helper_passthrough_no_context():
    """W4-032 · helper retorna None se sem context."""
    from lia_agents_core.agent_interface import AgentInput
    from app.shared.hitl.agent_gate import maybe_request_hitl_approval

    fake = MagicMock(spec=AgentInput)
    fake.context = None
    result = await maybe_request_hitl_approval(
        agent_input=fake,
        domain="test_domain",
        action_types=frozenset({"test"}),
        agent_name="test_agent",
    )
    assert result is None


@pytest.mark.asyncio
async def test_helper_passthrough_action_not_in_set():
    """W4-032 · helper passthrough quando action_type NÃO está em set."""
    from lia_agents_core.agent_interface import AgentInput
    from app.shared.hitl.agent_gate import maybe_request_hitl_approval

    fake = MagicMock(spec=AgentInput)
    fake.context = {"action_type": "read_only", "hitl_approved": False}
    fake.session_id = "s1"
    fake.company_id = "c1"
    fake.user_id = "u1"
    fake.message = "msg"
    fake.conversation_history = []

    result = await maybe_request_hitl_approval(
        agent_input=fake,
        domain="d",
        action_types=frozenset({"write_action"}),
        agent_name="test_agent",
    )
    assert result is None


@pytest.mark.asyncio
async def test_helper_passthrough_already_approved():
    """W4-032 · helper passthrough quando hitl_approved=True (reprise)."""
    from lia_agents_core.agent_interface import AgentInput
    from app.shared.hitl.agent_gate import maybe_request_hitl_approval

    fake = MagicMock(spec=AgentInput)
    fake.context = {"action_type": "write_action", "hitl_approved": True}
    fake.session_id = "s1"
    fake.company_id = "c1"
    fake.user_id = "u1"
    fake.message = "msg"
    fake.conversation_history = []

    result = await maybe_request_hitl_approval(
        agent_input=fake,
        domain="d",
        action_types=frozenset({"write_action"}),
        agent_name="test_agent",
    )
    assert result is None


@pytest.mark.asyncio
async def test_helper_gate_triggered_returns_pending_output():
    """W4-032 · helper retorna AgentOutput 'Aguardando aprovação' quando gate triggers."""
    from lia_agents_core.agent_interface import AgentInput, AgentOutput
    from app.shared.hitl.agent_gate import maybe_request_hitl_approval

    fake = MagicMock(spec=AgentInput)
    fake.context = {"action_type": "sync_to_ats", "hitl_approved": False}
    fake.session_id = "s1"
    fake.company_id = "c1"
    fake.user_id = "u1"
    fake.message = "msg"
    fake.conversation_history = []

    mock_hitl = AsyncMock()
    mock_hitl.request_approval = AsyncMock(return_value="pending-uuid-123")
    mock_hitl.store_resume_info = AsyncMock(return_value=None)

    with patch("app.services.hitl_service.hitl_service", mock_hitl):
        result = await maybe_request_hitl_approval(
            agent_input=fake,
            domain="ats_integration",
            action_types=frozenset({"sync_to_ats"}),
            agent_name="ats_integration_react_agent",
        )

    assert result is not None
    assert isinstance(result, AgentOutput)
    assert "Aguardando aprovação" in result.message
    assert result.metadata["hitl_pending"] is True
    assert result.metadata["hitl_pending_id"] == "pending-uuid-123"
    mock_hitl.request_approval.assert_awaited_once()
    mock_hitl.store_resume_info.assert_awaited_once()


@pytest.mark.asyncio
async def test_helper_fail_open_on_service_error():
    """W4-032 · helper fail-open (return None) quando hitl_service quebra."""
    from lia_agents_core.agent_interface import AgentInput
    from app.shared.hitl.agent_gate import maybe_request_hitl_approval

    fake = MagicMock(spec=AgentInput)
    fake.context = {"action_type": "sync_to_ats", "hitl_approved": False}
    fake.session_id = "s1"
    fake.company_id = "c1"
    fake.user_id = "u1"
    fake.message = "msg"
    fake.conversation_history = []

    mock_hitl = AsyncMock()
    mock_hitl.request_approval = AsyncMock(side_effect=RuntimeError("DB down"))

    with patch("app.services.hitl_service.hitl_service", mock_hitl):
        result = await maybe_request_hitl_approval(
            agent_input=fake,
            domain="ats_integration",
            action_types=frozenset({"sync_to_ats"}),
            agent_name="ats_integration_react_agent",
        )

    # Fail-open: helper retornou None (caller prossegue normalmente)
    assert result is None


def test_p0_agents_import_helper():
    """W4-032 P0 · cada agent file importa o helper."""
    files = [
        "app/domains/ats_integration/agents/ats_integration_react_agent.py",
        "app/domains/recruiter_assistant/agents/kanban_react_agent.py",
    ]
    repo_root = Path(__file__).resolve().parents[2]
    for f in files:
        src = (repo_root / f).read_text()
        assert "from app.shared.hitl.agent_gate import maybe_request_hitl_approval" in src, (
            f"{f} NÃO importa maybe_request_hitl_approval"
        )
        assert "if hitl_response is not None:" in src or "if _hitl_response is not None:" in src, (
            f"{f} NÃO tem early return pattern do gate"
        )
