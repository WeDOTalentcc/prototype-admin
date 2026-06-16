"""
Contract test: wizard handoff stage is TERMINAL (2026-06-13).

Root cause: handoff_node sets current_stage="handoff" but never transitions
to "completed". is_wizard_session_active only checked stage == "completed",
so a finished wizard remained "active" — causing the frontend to rehydrate
the stale "Vaga publicada" panel on every page load until the 2h TTL expired.

Fix A: wizard_session_service marks checkpoint as "completed" after handoff.
Fix B (defensive): is_wizard_session_active treats handoff/done as terminal.

These tests pin both fixes so the bug never resurfaces.
"""
import pytest
from app.shared.sessions.thread_id import (
    _TERMINAL_STAGES,
    is_wizard_session_active,
)


class TestTerminalStages:
    """Fix B: _TERMINAL_STAGES includes handoff and done."""

    def test_completed_is_terminal(self):
        assert "completed" in _TERMINAL_STAGES

    def test_handoff_is_terminal(self):
        assert "handoff" in _TERMINAL_STAGES

    def test_done_is_terminal(self):
        assert "done" in _TERMINAL_STAGES

    def test_intake_is_not_terminal(self):
        assert "intake" not in _TERMINAL_STAGES

    def test_publish_is_not_terminal(self):
        assert "publish" not in _TERMINAL_STAGES


class TestIsWizardSessionActiveWithTerminalStages:
    """is_wizard_session_active returns False for terminal stages."""

    @pytest.mark.asyncio
    async def test_handoff_stage_returns_inactive(self):
        """A wizard at handoff stage must NOT be considered active."""
        from unittest.mock import patch, MagicMock
        import asyncio

        mock_snapshot = MagicMock()
        mock_snapshot.values = {
            "current_stage": "handoff",
            "conversation_messages": [{"role": "user", "content": "ok"}],
        }
        mock_snapshot.tasks = []
        mock_snapshot.created_at = None

        mock_graph = MagicMock()
        mock_graph._graph.get_state.return_value = mock_snapshot

        with patch(
            "app.shared.sessions.thread_id.asyncio.to_thread",
            side_effect=lambda fn, *a, **kw: asyncio.coroutine(lambda: fn(*a, **kw))(),
        ), patch(
            "app.domains.job_creation.graph.get_job_creation_graph",
            return_value=mock_graph,
        ):
            result = await is_wizard_session_active("company-123", "session-abc")
            assert result is False, (
                "handoff stage must be terminal — wizard should not be "
                "considered active after job creation is complete"
            )

    @pytest.mark.asyncio
    async def test_completed_stage_returns_inactive(self):
        """A wizard at completed stage must NOT be considered active."""
        from unittest.mock import patch, MagicMock
        import asyncio

        mock_snapshot = MagicMock()
        mock_snapshot.values = {
            "current_stage": "completed",
            "conversation_messages": [],
        }
        mock_snapshot.tasks = []
        mock_snapshot.created_at = None

        mock_graph = MagicMock()
        mock_graph._graph.get_state.return_value = mock_snapshot

        with patch(
            "app.shared.sessions.thread_id.asyncio.to_thread",
            side_effect=lambda fn, *a, **kw: asyncio.coroutine(lambda: fn(*a, **kw))(),
        ), patch(
            "app.domains.job_creation.graph.get_job_creation_graph",
            return_value=mock_graph,
        ):
            result = await is_wizard_session_active("company-123", "session-abc")
            assert result is False

    @pytest.mark.asyncio
    async def test_intake_stage_returns_active(self):
        """A wizard at intake stage must be considered active."""
        from unittest.mock import patch, MagicMock
        import asyncio

        mock_snapshot = MagicMock()
        mock_snapshot.values = {
            "current_stage": "intake",
            "conversation_messages": [{"role": "user", "content": "criar vaga"}],
        }
        mock_snapshot.tasks = []
        mock_snapshot.created_at = None

        mock_graph = MagicMock()
        mock_graph._graph.get_state.return_value = mock_snapshot

        with patch(
            "app.shared.sessions.thread_id.asyncio.to_thread",
            side_effect=lambda fn, *a, **kw: asyncio.coroutine(lambda: fn(*a, **kw))(),
        ), patch(
            "app.domains.job_creation.graph.get_job_creation_graph",
            return_value=mock_graph,
        ):
            result = await is_wizard_session_active("company-123", "session-abc")
            assert result is True, (
                "intake stage is an active wizard stage — must return True"
            )
