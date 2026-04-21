"""
FIX 6 — Structured logging of tool calls.

Verify that agentic_loop.py emits logger.info("tool_call", extra={...})
with the expected metadata fields.
"""


class TestFix6Observability:
    def test_agentic_loop_source_has_structured_log(self):
        """Check that the source file contains the structured log call."""
        from pathlib import Path
        import app.orchestrator.agentic_loop as ag
        src = Path(ag.__file__).read_text()
        # Expected fields in the structured log
        assert '"tool_call"' in src
        assert '"first_shot"' in src
        assert '"company_id"' in src
        assert '"call_index"' in src
        assert '"governance_tags"' in src
        assert '"has_related_tools"' in src
        assert '"success"' in src

    def test_logging_is_non_blocking(self):
        """The observability block must be wrapped in try/except to be non-blocking."""
        from pathlib import Path
        import app.orchestrator.agentic_loop as ag
        src = Path(ag.__file__).read_text()
        idx = src.find('"tool_call"')
        assert idx > 0
        # Check that within a window around the log there's both `try:` and `except`
        # Check a large window (8000 chars) around the log for try/except wrapping
        window = src[max(0, idx - 2000):idx + 1500]
        assert "try:" in window and "except" in window, (
            "tool_call log must be wrapped in try/except to be non-blocking"
        )
