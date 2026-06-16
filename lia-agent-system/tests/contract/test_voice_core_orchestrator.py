"""
Tests for VoiceCoreOrchestrator (Sprint 3.2 — audit 2026-05-22 W4-1 V2).

Validates that the generic voice core:
- Works in plugin-less mode (zero plugins → no domain-specific behavior).
- Accepts custom plugins implementing VoiceCorePlugin.
- Fans out lifecycle hooks (on_session_initiated / get_next_question /
  on_session_finalized) to registered plugins in order.
- Swallows plugin errors (best-effort — voice call never blocked by plugin
  failure).
- Is importable from the canonical voice_core_orchestrator module path.

Backward-compat tests (VoiceScreeningOrchestrator subclass + WSI behavior) live
in tests/contract/test_voice_screening_orchestrator_regression.py (Sprint 3.1).
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin
from app.domains.voice.services.voice_core_orchestrator import (
    VoiceCoreOrchestrator,
    VoiceScreeningOrchestrator,
    VoiceScreeningSession,
)


@pytest.fixture
def session() -> VoiceScreeningSession:
    """Minimal session for hook tests."""
    return VoiceScreeningSession(
        session_id="sess-core-test",
        candidate_id="cand-1",
        candidate_name="Test Cand",
        job_title="Test Job",
        company_id="co-1",
        phone_number="+5511999999999",
        job_id="job-1",
    )


@pytest.fixture
def recording_plugin() -> "RecordingPlugin":
    """A plugin that records every hook call for assertion."""

    class RecordingPlugin(VoiceCorePlugin):
        def __init__(self):
            self.calls: list[str] = []
            self.next_question_value: str | None = None
            self.finalized_value: dict = {}

        @property
        def plugin_name(self) -> str:
            return "recording_test_plugin"

        async def on_session_initiated(self, session, db) -> None:
            self.calls.append(f"initiated:{session.session_id}")

        async def get_next_question(self, session, db) -> str | None:
            self.calls.append(f"next_q:{session.session_id}")
            return self.next_question_value

        async def on_session_finalized(
            self, session, db, transcript: list[dict[str, Any]]
        ) -> dict[str, Any]:
            self.calls.append(f"finalized:{session.session_id}:{len(transcript)}")
            return self.finalized_value

    return RecordingPlugin()


class TestVoiceCoreOrchestratorPluginless:
    """Core works as pure voice transport when no plugins are registered."""

    def test_core_instantiates_without_plugins(self):
        """Default constructor → plugin-less mode (generic voice transport)."""
        core = VoiceCoreOrchestrator()
        assert core._plugins == []

    def test_core_instantiates_with_explicit_empty_list(self):
        """Explicit empty plugin list is equivalent to default."""
        core = VoiceCoreOrchestrator(plugins=[])
        assert core._plugins == []

    @pytest.mark.asyncio
    async def test_session_initiated_hook_is_noop_without_plugins(self, session):
        """No plugins → _on_session_initiated returns None silently."""
        core = VoiceCoreOrchestrator()
        result = await core._on_session_initiated(session, db=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_next_question_returns_none_without_plugins(self, session):
        """No plugins → core falls through to scripted fallback."""
        core = VoiceCoreOrchestrator()
        result = await core._plugin_next_question(session, db=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_finalized_hook_returns_empty_dict_without_plugins(self, session):
        """No plugins → completion merge is an empty dict."""
        core = VoiceCoreOrchestrator()
        result = await core._on_session_finalized(session, db=None, transcript=[])
        assert result == {}


class TestVoiceCoreOrchestratorWithPlugin:
    """Core dispatches lifecycle hooks to registered plugins in order."""

    @pytest.mark.asyncio
    async def test_on_session_initiated_dispatches_to_plugin(
        self, session, recording_plugin
    ):
        """Lifecycle hook dispatch contract.

        C.3 (2026-05-23): after fanning out on_session_initiated, the
        orchestrator also queries _plugin_next_question to cache the
        bootstrap initial_greeting into session.metadata. A plugin that
        implements both hooks will record TWO calls: initiated + next_q.
        """
        core = VoiceCoreOrchestrator(plugins=[recording_plugin])
        await core._on_session_initiated(session, db=None)
        assert recording_plugin.calls == [
            f"initiated:{session.session_id}",
            f"next_q:{session.session_id}",
        ]

    @pytest.mark.asyncio
    async def test_next_question_returns_plugin_value(self, session, recording_plugin):
        recording_plugin.next_question_value = "Conte sobre Python."
        core = VoiceCoreOrchestrator(plugins=[recording_plugin])
        result = await core._plugin_next_question(session, db=None)
        assert result == "Conte sobre Python."

    @pytest.mark.asyncio
    async def test_next_question_falls_through_when_plugin_returns_none(
        self, session, recording_plugin
    ):
        recording_plugin.next_question_value = None  # plugin defers
        core = VoiceCoreOrchestrator(plugins=[recording_plugin])
        result = await core._plugin_next_question(session, db=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_finalized_merges_plugin_result(self, session, recording_plugin):
        recording_plugin.finalized_value = {"custom_score": 7.5, "tag": "passed"}
        core = VoiceCoreOrchestrator(plugins=[recording_plugin])
        result = await core._on_session_finalized(
            session, db=None, transcript=[{"text": "hi", "role": "candidate"}]
        )
        assert result == {"custom_score": 7.5, "tag": "passed"}


class TestVoiceCoreOrchestratorPluginErrorSwallowing:
    """Plugin failures MUST NOT propagate (voice call resilience)."""

    @pytest.mark.asyncio
    async def test_plugin_exception_in_initiated_is_swallowed(self, session, caplog):
        class BrokenPlugin(VoiceCorePlugin):
            @property
            def plugin_name(self) -> str:
                return "broken"

            async def on_session_initiated(self, session, db) -> None:
                raise RuntimeError("simulated plugin failure")

            async def get_next_question(self, session, db) -> str | None:
                return None

            async def on_session_finalized(self, session, db, transcript) -> dict:
                return {}

        core = VoiceCoreOrchestrator(plugins=[BrokenPlugin()])
        # MUST NOT raise.
        await core._on_session_initiated(session, db=None)
        # Should have logged a warning containing plugin name.
        assert any("broken" in rec.getMessage() for rec in caplog.records)

    @pytest.mark.asyncio
    async def test_plugin_exception_in_finalized_is_swallowed(self, session):
        class BrokenPlugin(VoiceCorePlugin):
            @property
            def plugin_name(self) -> str:
                return "broken"

            async def on_session_initiated(self, session, db) -> None:
                return None

            async def get_next_question(self, session, db) -> str | None:
                return None

            async def on_session_finalized(self, session, db, transcript) -> dict:
                raise ValueError("simulated finalize failure")

        core = VoiceCoreOrchestrator(plugins=[BrokenPlugin()])
        result = await core._on_session_finalized(session, db=None, transcript=[])
        # Returns empty dict (no merge happened) rather than propagating.
        assert result == {}


class TestVoiceCoreOrchestratorMultipleHooksOrder:
    """Multi-plugin registration order is preserved; get_next_question returns first hit."""

    @pytest.mark.asyncio
    async def test_initiated_hooks_run_in_registration_order(self, session):
        order: list[str] = []

        def make_plugin(name: str) -> VoiceCorePlugin:
            class P(VoiceCorePlugin):
                @property
                def plugin_name(self):
                    return name

                async def on_session_initiated(self, session, db):
                    order.append(name)

                async def get_next_question(self, session, db):
                    return None

                async def on_session_finalized(self, session, db, transcript):
                    return {}

            return P()

        core = VoiceCoreOrchestrator(plugins=[make_plugin("a"), make_plugin("b"), make_plugin("c")])
        await core._on_session_initiated(session, db=None)
        assert order == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_next_question_returns_first_non_none(self, session):
        def make_plugin(name: str, q: str | None) -> VoiceCorePlugin:
            class P(VoiceCorePlugin):
                @property
                def plugin_name(self):
                    return name

                async def on_session_initiated(self, session, db):
                    return None

                async def get_next_question(self, session, db):
                    return q

                async def on_session_finalized(self, session, db, transcript):
                    return {}

            return P()

        core = VoiceCoreOrchestrator(
            plugins=[
                make_plugin("none1", None),
                make_plugin("hit", "FIRST_HIT"),
                make_plugin("hit2", "SHOULD_NOT_BE_USED"),
            ]
        )
        result = await core._plugin_next_question(session, db=None)
        assert result == "FIRST_HIT"


class TestVoiceCoreOrchestratorBackwardCompat:
    """VoiceScreeningOrchestrator subclass preserves legacy API."""

    def test_legacy_subclass_inherits_from_core(self):
        assert issubclass(VoiceScreeningOrchestrator, VoiceCoreOrchestrator)

    def test_legacy_subclass_instantiates_without_args(self):
        """Existing callers do `VoiceScreeningOrchestrator()` — must keep working."""
        orch = VoiceScreeningOrchestrator()
        assert isinstance(orch, VoiceCoreOrchestrator)
        # Sprint 3.3: WSIVoicePlugin pre-installed.
        assert len(orch._plugins) == 1
        assert orch._plugins[0].plugin_name == "wsi_screening"

    def test_legacy_subclass_has_wsi_delegate_methods(self):
        """Sprint 3.3: backward-compat delegates for test patches."""
        orch = VoiceScreeningOrchestrator()
        # These 3 methods exist on the instance and are patchable.
        assert callable(orch._register_wsi_session)
        assert callable(orch._generate_and_store_wsi_questions)
        assert callable(orch._load_wsi_questions_for_session)

    def test_canonical_reexport_module_works(self):
        """`from voice_core_orchestrator import VoiceCoreOrchestrator` works."""
        from app.domains.voice.services.voice_core_orchestrator import (
            VoiceCoreOrchestrator as CoreFromReexport,
        )

        assert CoreFromReexport is VoiceCoreOrchestrator
