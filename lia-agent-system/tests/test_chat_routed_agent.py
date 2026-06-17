"""Task #552 — chat reply must echo which specialist actually answered.

The persona-diagnostic routing audit reads `metadata.routed_agent` (or any of
the documented fallbacks) to populate `agent_observed`. These tests pin the
contract end-to-end at the adapter layer so we don't accidentally drop the
identifier again.
"""
from __future__ import annotations

from app.orchestrator.context.chat_adapter import ChatAdapter


class _FakeChatResponse:
    def __init__(self, agent_used="wsi_evaluator", consulted=None):
        self.content = "ok"
        self.intent_detected = "wsi_evaluation"
        self.agent_used = agent_used
        self.agents_consulted = consulted or [agent_used]
        self.fairness_warnings = []
        self.from_cache = False
        self.actions = []
        self.structured_data = None
        self.action_result = None
        self.pending_action_id = None
        self.success = True


def _adapter() -> ChatAdapter:
    return ChatAdapter.__new__(ChatAdapter)


def test_convert_response_exposes_agent_used():
    out = _adapter()._convert_response(_FakeChatResponse())
    assert out["agent_used"] == "wsi_evaluator"
    assert out["agents_consulted"] == ["wsi_evaluator"]


def test_convert_response_falls_back_when_agent_used_missing():
    resp = _FakeChatResponse(agent_used="")
    out = _adapter()._convert_response(resp)
    assert out["agent_used"] == "main_orchestrator"


def test_error_response_still_carries_agent_used_key():
    out = _adapter()._error_response("boom")
    assert "agent_used" in out
    assert out["agent_used"] == "chat_adapter_error"


def test_runner_extract_agent_handles_chat_api_payload():
    """The persona-diagnostic runner must locate `routed_agent` inside
    `ChatResponse.message.message_metadata` (the exact shape returned by
    `POST /api/v1/chat`)."""
    import importlib.util
    from pathlib import Path
    runner_py = Path(__file__).resolve().parents[1] / "eval/persona-diagnostic/runner/runner.py"
    spec = importlib.util.spec_from_file_location("persona_diag_runner", runner_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _extract_agent = mod._extract_agent

    payload = {
        "message": {
            "id": "m-1",
            "conversation_id": "c-1",
            "role": "assistant",
            "content": "ok",
            "message_metadata": {
                "intent": "wsi_evaluation",
                "routed_agent": "wsi_evaluator",
                "agent_used": "wsi_evaluator",
            },
            "tool_calls": [],
            "created_at": "2026-04-20T00:00:00",
        },
        "conversation": {"id": "c-1"},
    }
    assert _extract_agent(payload) == "wsi_evaluator"


def test_runner_extract_agent_handles_fairness_blocked_payload():
    """Even compliance-blocked replies (fairness_guard) must surface a
    routed identifier so `agent_observed` is never silently `None`."""
    import importlib.util
    from pathlib import Path
    runner_py = Path(__file__).resolve().parents[1] / "eval/persona-diagnostic/runner/runner.py"
    spec = importlib.util.spec_from_file_location("persona_diag_runner_blk", runner_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _extract_agent = mod._extract_agent

    payload = {
        "message": {
            "id": "m-2",
            "conversation_id": "c-2",
            "role": "assistant",
            "content": "Solicitação bloqueada.",
            "message_metadata": {
                "fairness_blocked": True,
                "routed_agent": "fairness_guard",
                "agent_used": "fairness_guard",
            },
            "tool_calls": [],
            "created_at": "2026-04-20T00:00:00",
        },
        "conversation": {"id": "c-2"},
    }
    assert _extract_agent(payload) == "fairness_guard"
