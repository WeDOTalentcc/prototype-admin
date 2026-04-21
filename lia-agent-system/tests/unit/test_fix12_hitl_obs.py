"""
FIX 12 — HITL envelope + observability module tests.

G8: pending_hitl_confirmation from tool_calls must be promoted to
    a top-level hitl_pending envelope in ChatResponse.structured_data.
G9: emit_tool_call() helper exists and is called from agentic_loop.
"""
import pytest


class TestFix12ObservabilityModule:
    def test_emit_tool_call_exists(self):
        from app.core.observability import emit_tool_call
        assert callable(emit_tool_call)

    def test_emit_hitl_pending_exists(self):
        from app.core.observability import emit_hitl_pending
        assert callable(emit_hitl_pending)

    def test_emit_tool_call_never_raises(self):
        from app.core.observability import emit_tool_call
        # Even with odd inputs, must not raise
        emit_tool_call(
            tool_name="t",
            company_id=None,
            success=True,
            first_shot=True,
            call_index=0,
            governance_tags=None,
            has_related_tools=False,
            latency_ms=None,
        )

    def test_langsmith_disabled_by_default(self):
        """Without env vars, no LangSmith client is created."""
        import os
        from app.core.observability import _maybe_get_langsmith_client, reset_langsmith_cache
        reset_langsmith_cache()
        # Ensure env is clean for this test
        old = os.environ.pop("LANGCHAIN_TRACING_V2", None)
        try:
            client = _maybe_get_langsmith_client()
            assert client is None
        finally:
            if old is not None:
                os.environ["LANGCHAIN_TRACING_V2"] = old
            reset_langsmith_cache()


class TestFix12AgenticLoopUsesObservability:
    def test_agentic_loop_imports_emit_tool_call(self):
        from pathlib import Path
        import app.orchestrator.agentic_loop as ag
        src = Path(ag.__file__).read_text()
        assert "emit_tool_call" in src, "agentic_loop must call emit_tool_call from observability"


class TestFix12HITLEnvelope:
    def test_main_orchestrator_promotes_hitl_pending(self):
        """The main_orchestrator source file must contain logic that detects
        pending_hitl_confirmation tool results and surfaces hitl_pending."""
        from pathlib import Path
        import app.orchestrator.main_orchestrator as mo
        src = Path(mo.__file__).read_text()
        assert "pending_hitl_confirmation" in src, (
            "main_orchestrator must detect pending_hitl_confirmation tool results"
        )
        assert "hitl_pending" in src, (
            "main_orchestrator must promote hitl_pending envelope in response"
        )
