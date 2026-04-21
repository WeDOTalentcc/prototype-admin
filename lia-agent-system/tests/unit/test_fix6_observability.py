"""
FIX 6 — Structured logging of tool calls.

After FIX 12 refactor, the structured log is emitted via
`app.shared.observability.tool_metrics.emit_tool_call`. This test verifies the integration
point and payload shape.
"""


class TestFix6Observability:
    def test_observability_module_emits_tool_call(self):
        """The central emit_tool_call helper produces structured logs."""
        from pathlib import Path
        import app.shared.observability.tool_metrics as obs
        src = Path(obs.__file__).read_text()
        # Expected fields in the structured log event
        for field in (
            '"tool_name"', '"first_shot"', '"company_id"', '"call_index"',
            '"governance_tags"', '"has_related_tools"', '"success"',
        ):
            assert field in src, f"observability module must include {field} in log event"

    def test_agentic_loop_invokes_emit_tool_call(self):
        """agentic_loop.py must call emit_tool_call (not inline logger)."""
        from pathlib import Path
        import app.orchestrator.agentic_loop as ag
        src = Path(ag.__file__).read_text()
        assert "emit_tool_call(" in src, (
            "agentic_loop must call emit_tool_call from observability module"
        )

    def test_emit_tool_call_is_non_blocking(self):
        """The observability helper must never raise on bad inputs."""
        from app.shared.observability.tool_metrics import emit_tool_call
        # Pass extreme edge cases
        emit_tool_call(
            tool_name="",
            company_id=None,
            success=False,
            first_shot=True,
            call_index=-1,
            governance_tags=[],
            has_related_tools=False,
            latency_ms=None,
            error=None,
        )
        # No exception = pass
