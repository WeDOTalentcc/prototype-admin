"""
Tests for WSIVoicePlugin (Sprint 3.3 — audit 2026-05-22 W4-1 V2).

Validates the WSI-specific VoiceCorePlugin extracted from the monolith
voice_screening_orchestrator:
- Implements VoiceCorePlugin protocol (ABC contract).
- Owns _register_wsi_session_impl, _generate_and_store_wsi_questions_impl,
  _load_wsi_questions_for_session_impl (the 3 methods historically inline).
- on_session_initiated delegates to _register_wsi_session_impl.
- on_session_finalized + get_next_question return empty/None (Sprint 3.3:
  finalize_screening still uses inline _WSIVoiceOrchestrator).
- VoiceScreeningOrchestrator pre-installs this plugin and keeps thin
  delegate methods that route to plugin (`patch.object` compat preserved).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.voice.plugins.wsi_voice_plugin import WSIVoicePlugin
from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin
from app.domains.voice.services.voice_screening_orchestrator import (
    VoiceScreeningOrchestrator,
    VoiceScreeningSession,
)


@pytest.fixture
def wsi_session() -> VoiceScreeningSession:
    return VoiceScreeningSession(
        session_id="sess-wsi-1",
        candidate_id="cand-1",
        candidate_name="WSI Test",
        job_title="Software Engineer",
        company_id="co-wsi-1",
        phone_number="+5511999999999",
        job_id="job-wsi-1",
        call_sid="CA_TEST",
    )


class TestWSIVoicePluginProtocol:
    """Confirm plugin obeys VoiceCorePlugin contract."""

    def test_implements_voice_core_plugin(self):
        plugin = WSIVoicePlugin()
        assert isinstance(plugin, VoiceCorePlugin)

    def test_plugin_name_is_wsi_screening(self):
        plugin = WSIVoicePlugin()
        assert plugin.plugin_name == "wsi_screening"

    def test_plugin_accepts_orchestrator_reference(self):
        orch = VoiceScreeningOrchestrator()
        plugin = WSIVoicePlugin(orchestrator=orch)
        assert plugin._orchestrator is orch

    def test_plugin_orchestrator_optional(self):
        plugin = WSIVoicePlugin()
        assert plugin._orchestrator is None


class TestWSIVoicePluginHooks:
    """Validate hook semantics specific to WSI plugin."""

    @pytest.mark.asyncio
    async def test_on_session_initiated_with_none_db_is_noop(self, wsi_session):
        """db=None → hook returns without exception (production tests use mock_db)."""
        plugin = WSIVoicePlugin()
        # Must not raise.
        await plugin.on_session_initiated(wsi_session, db=None)

    @pytest.mark.asyncio
    async def test_on_session_initiated_calls_register_impl(self, wsi_session):
        plugin = WSIVoicePlugin()
        with patch.object(
            plugin, "_register_wsi_session_impl", new=AsyncMock()
        ) as mock_impl:
            await plugin.on_session_initiated(wsi_session, db=MagicMock())
            mock_impl.assert_awaited_once_with(wsi_session, mock_impl.await_args.args[1])

    @pytest.mark.asyncio
    async def test_get_next_question_returns_none_sprint_3_3(self, wsi_session):
        """Sprint 3.3: plugin defers to legacy scripted-question flow."""
        plugin = WSIVoicePlugin()
        result = await plugin.get_next_question(wsi_session, db=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_on_session_finalized_returns_empty_dict_sprint_3_3(self, wsi_session):
        """Sprint 3.3: plugin defers to legacy finalize_screening F-17 strategy."""
        plugin = WSIVoicePlugin()
        result = await plugin.on_session_finalized(wsi_session, db=None, transcript=[])
        assert result == {}


class TestWSIVoicePluginLoadQuestions:
    """_load_wsi_questions_for_session_impl semantics."""

    @pytest.mark.asyncio
    async def test_load_questions_none_db_returns_empty(self):
        plugin = WSIVoicePlugin()
        result = await plugin._load_wsi_questions_for_session_impl(
            session_id="sess-x", db=None
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_load_questions_dispatches_to_repository(self):
        plugin = WSIVoicePlugin()
        mock_db = MagicMock()
        with patch(
            "app.domains.voice.repositories.wsi_repository.WsiRepository"
        ) as MockRepo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.list_question_texts_for_session = AsyncMock(
                return_value=["Q1", "Q2", "Q3"]
            )
            MockRepo.return_value = mock_repo_instance

            result = await plugin._load_wsi_questions_for_session_impl(
                session_id="sess-x", db=mock_db
            )

            assert result == ["Q1", "Q2", "Q3"]
            MockRepo.assert_called_once_with(mock_db)
            mock_repo_instance.list_question_texts_for_session.assert_awaited_once_with(
                "sess-x"
            )

    @pytest.mark.asyncio
    async def test_load_questions_returns_empty_on_repository_error(self):
        plugin = WSIVoicePlugin()
        mock_db = MagicMock()
        with patch(
            "app.domains.voice.repositories.wsi_repository.WsiRepository"
        ) as MockRepo:
            MockRepo.side_effect = RuntimeError("simulated DB error")
            result = await plugin._load_wsi_questions_for_session_impl(
                session_id="sess-x", db=mock_db
            )
            assert result == []


class TestVoiceScreeningOrchestratorBackwardCompat:
    """Subclass pre-installs plugin AND keeps delegate methods callable."""

    def test_subclass_preinstalls_wsi_plugin(self):
        orch = VoiceScreeningOrchestrator()
        assert isinstance(orch._wsi_plugin, WSIVoicePlugin)
        assert orch._wsi_plugin in orch._plugins

    def test_plugin_has_orchestrator_backreference(self):
        orch = VoiceScreeningOrchestrator()
        assert orch._wsi_plugin._orchestrator is orch

    @pytest.mark.asyncio
    async def test_register_wsi_session_delegate_routes_to_plugin(self, wsi_session):
        orch = VoiceScreeningOrchestrator()
        with patch.object(
            orch._wsi_plugin, "_register_wsi_session_impl", new=AsyncMock()
        ) as mock_impl:
            await orch._register_wsi_session(wsi_session, db=None)
            mock_impl.assert_awaited_once_with(wsi_session, None)

    @pytest.mark.asyncio
    async def test_load_wsi_questions_delegate_routes_to_plugin(self):
        orch = VoiceScreeningOrchestrator()
        with patch.object(
            orch._wsi_plugin,
            "_load_wsi_questions_for_session_impl",
            new=AsyncMock(return_value=["mocked"]),
        ) as mock_impl:
            result = await orch._load_wsi_questions_for_session("sess-x", db=None)
            assert result == ["mocked"]
            mock_impl.assert_awaited_once_with("sess-x", None)

    @pytest.mark.asyncio
    async def test_generate_and_store_wsi_questions_delegate_routes_to_plugin(
        self, wsi_session
    ):
        orch = VoiceScreeningOrchestrator()
        with patch.object(
            orch._wsi_plugin,
            "_generate_and_store_wsi_questions_impl",
            new=AsyncMock(),
        ) as mock_impl:
            await orch._generate_and_store_wsi_questions(wsi_session, db=None)
            mock_impl.assert_awaited_once_with(wsi_session, None)

    @pytest.mark.asyncio
    async def test_test_patches_still_work_on_delegate(self, wsi_session):
        """
        Regression sentinel for ~240 tests using
        `patch.object(orch, '_register_wsi_session', new=AsyncMock())`.

        Confirms the delegate is a normal bound method (not a property /
        descriptor) — patch.object can substitute it cleanly.
        """
        orch = VoiceScreeningOrchestrator()
        mock = AsyncMock()
        with patch.object(orch, "_register_wsi_session", new=mock):
            await orch._register_wsi_session(wsi_session, db=None)
            mock.assert_awaited_once_with(wsi_session, db=None)
