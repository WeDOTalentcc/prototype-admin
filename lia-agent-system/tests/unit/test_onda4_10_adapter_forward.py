"""Onda 4.10 — ChatAdapter must forward V.B citations + G3.B hitl_checkpoint.

PARTE L audit revealed: MainOrchestrator produces ChatResponse with
`citations`, `has_citations`, `hitl_checkpoint` fields (wired in Onda 4.5
and 4.6) but ChatAdapter._convert_response() strips them when converting
to the dict format chat.py consumes.

Canonical-fix: producer (orchestrator) is correct; consumer (adapter) was
too narrow. Widen _convert_response to forward the new fields.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_orch_response(**overrides):
    """Build a MagicMock shaped like ChatResponse with sensible defaults."""
    resp = MagicMock()
    resp.content = "test response"
    resp.intent_detected = "agentic_tool_call"
    resp.agent_used = "main_orchestrator"
    resp.agents_consulted = []
    resp.structured_data = None
    resp.action_result = None
    resp.pending_action_id = None
    resp.needs_confirmation = False
    resp.needs_params = False
    resp.fairness_warnings = []
    resp.from_cache = False
    resp.actions = []
    resp.success = True
    # New Onda 4 fields
    resp.citations = []
    resp.has_citations = False
    resp.hitl_checkpoint = None
    for k, v in overrides.items():
        setattr(resp, k, v)
    return resp


def test_adapter_forwards_citations_when_present() -> None:
    """Onda 4.10: ChatAdapter._convert_response must forward .citations."""
    from app.orchestrator.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=MagicMock())
    resp = _make_orch_response(
        citations=[{"id": "c1", "tool_name": "search_jobs", "marker": "[^1]"}],
        has_citations=True,
    )
    result = adapter._convert_response(resp)
    assert "citations" in result, "adapter must expose citations field"
    assert result["citations"] == [{"id": "c1", "tool_name": "search_jobs", "marker": "[^1]"}]
    assert result.get("has_citations") is True


def test_adapter_forwards_empty_citations() -> None:
    """Default empty citations still exposed (frontend can rely on key existence)."""
    from app.orchestrator.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=MagicMock())
    resp = _make_orch_response()  # citations=[] by default
    result = adapter._convert_response(resp)
    # Must expose key even when empty — so frontend can count on shape
    assert "citations" in result
    assert result["citations"] == []
    assert result.get("has_citations") is False


def test_adapter_forwards_hitl_checkpoint_when_present() -> None:
    """Onda 4.10: ChatAdapter must forward .hitl_checkpoint."""
    from app.orchestrator.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=MagicMock())
    checkpoint = {
        "id": "hitl-123",
        "tool_name": "close_job",
        "tool_params": {"job_id": "v0040", "reason": "budget"},
        "governance_tags": ["destructive"],
        "reason": "requires approval",
    }
    resp = _make_orch_response(hitl_checkpoint=checkpoint)
    result = adapter._convert_response(resp)
    assert "hitl_checkpoint" in result
    assert result["hitl_checkpoint"] == checkpoint


def test_adapter_omits_hitl_checkpoint_when_none() -> None:
    """hitl_checkpoint=None should NOT pollute dict (frontend checks presence)."""
    from app.orchestrator.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=MagicMock())
    resp = _make_orch_response(hitl_checkpoint=None)
    result = adapter._convert_response(resp)
    # key may be absent or explicitly None — accept both
    assert result.get("hitl_checkpoint") is None


def test_adapter_preserves_existing_fields() -> None:
    """Regression: adapter must still forward response/intent/workflow_data/etc."""
    from app.orchestrator.chat_adapter import ChatAdapter

    adapter = ChatAdapter(main_orchestrator=MagicMock())
    resp = _make_orch_response(
        content="hello",
        intent_detected="greeting",
        agent_used="main_orchestrator",
        structured_data={"k": "v"},
        citations=[{"id": "c1"}],
    )
    result = adapter._convert_response(resp)
    # Pre-Onda 4.10 contract must stay intact
    assert result["response"] == "hello"
    assert result["intent"] == "greeting"
    assert result["agent_used"] == "main_orchestrator"
    assert result["workflow_data"] == {"k": "v"}
    # New field also present
    assert result["citations"] == [{"id": "c1"}]
