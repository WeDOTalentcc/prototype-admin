"""
Tests for VoiceCorePlugin protocol (Sprint 3.2 — audit 2026-05-22 W4-1 V2).

Validates the ABC contract: subclasses MUST implement all 4 hooks (plugin_name,
on_session_initiated, get_next_question, on_session_finalized). Incomplete
implementations fail to instantiate at construction time.
"""
from __future__ import annotations

from typing import Any

import pytest

from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin


class TestVoiceCorePluginProtocol:
    """Sprint 3.2 ABC contract enforcement."""

    def test_cannot_instantiate_abc_directly(self):
        """VoiceCorePlugin is abstract — direct instantiation must fail."""
        with pytest.raises(TypeError, match="abstract"):
            VoiceCorePlugin()  # type: ignore[abstract]

    def test_incomplete_subclass_fails_to_instantiate(self):
        """Subclass missing any of the 4 abstract methods cannot be instantiated."""

        class IncompletePlugin(VoiceCorePlugin):
            @property
            def plugin_name(self) -> str:
                return "incomplete"

            # Missing: on_session_initiated, get_next_question, on_session_finalized

        with pytest.raises(TypeError, match="abstract"):
            IncompletePlugin()  # type: ignore[abstract]

    def test_complete_subclass_instantiates_ok(self):
        """A subclass implementing all 4 hooks must instantiate cleanly."""

        class CompletePlugin(VoiceCorePlugin):
            @property
            def plugin_name(self) -> str:
                return "complete_test_plugin"

            async def on_session_initiated(self, session, db) -> None:
                return None

            async def get_next_question(self, session, db) -> str | None:
                return None

            async def on_session_finalized(
                self, session, db, transcript: list[dict[str, Any]]
            ) -> dict[str, Any]:
                return {}

        plugin = CompletePlugin()
        assert plugin.plugin_name == "complete_test_plugin"
        assert isinstance(plugin, VoiceCorePlugin)
