"""Contract tests P2-2 Sprint A.5 — handler novo no OnboardingOrchestrator.

Valida wire-up cirurgico:
  - OnboardingPhase.SETTINGS_EXTRACTION existe
  - OnboardingSession.settings_extraction_status_json field opcional
  - handle_settings_extraction_message delega ao settings_runner
"""
import json
import pytest
from unittest.mock import AsyncMock, patch

from app.services.onboarding_orchestrator import (
    OnboardingOrchestrator,
    OnboardingSession,
    OnboardingPhase,
)


def _make_session(**overrides) -> OnboardingSession:
    base = dict(
        session_id="sess-test-1",
        user_id=1,
        account_id=42,
        user_name="Paulo Test",
        user_email="paulo@test.cc",
    )
    base.update(overrides)
    return OnboardingSession(**base)


class TestSettingsExtractionPhase:
    def test_new_phase_exists(self):
        assert OnboardingPhase.SETTINGS_EXTRACTION.value == "settings_extraction"

    def test_session_has_settings_extraction_field(self):
        s = _make_session()
        assert hasattr(s, "settings_extraction_status_json")
        assert s.settings_extraction_status_json is None  # default opcional


class TestHandleSettingsExtractionMessage:
    @pytest.mark.asyncio
    async def test_first_call_starts_with_greeting(self):
        """Sem status previo -> runner_start retorna greeting (message nao vazia)."""
        session = _make_session()
        orchestrator = OnboardingOrchestrator()
        with patch.object(orchestrator, "_audit", new=AsyncMock()), \
             patch.object(orchestrator, "_persist", new=AsyncMock()):
            result = await orchestrator.handle_settings_extraction_message(session, "")

        assert result["phase"] == "settings_extraction"
        assert isinstance(result["message"], str) and len(result["message"]) > 0
        assert result["is_complete"] is False
        assert result["progress_percent"] == 0

    @pytest.mark.asyncio
    async def test_persists_status_as_json(self):
        session = _make_session()
        orchestrator = OnboardingOrchestrator()
        with patch.object(orchestrator, "_audit", new=AsyncMock()), \
             patch.object(orchestrator, "_persist", new=AsyncMock()):
            await orchestrator.handle_settings_extraction_message(session, "")

        assert session.settings_extraction_status_json is not None
        parsed = json.loads(session.settings_extraction_status_json)
        assert "state" in parsed
        assert "answered_fields" in parsed
        assert "skipped_fields" in parsed

    @pytest.mark.asyncio
    async def test_invalid_json_status_resets_without_crash(self):
        """Status JSON corrupto -> re-inicia (nao crash)."""
        session = _make_session()
        session.settings_extraction_status_json = "{invalid json"
        orchestrator = OnboardingOrchestrator()
        with patch.object(orchestrator, "_audit", new=AsyncMock()), \
             patch.object(orchestrator, "_persist", new=AsyncMock()):
            result = await orchestrator.handle_settings_extraction_message(session, "")

        # Deve ter retornado dict valido (nao crash)
        assert "message" in result
        assert "phase" in result
        assert result["phase"] == "settings_extraction"

    @pytest.mark.asyncio
    async def test_audit_called_with_canonical_action(self):
        session = _make_session()
        orchestrator = OnboardingOrchestrator()
        audit_mock = AsyncMock()
        with patch.object(orchestrator, "_audit", new=audit_mock), \
             patch.object(orchestrator, "_persist", new=AsyncMock()):
            await orchestrator.handle_settings_extraction_message(session, "")

        audit_mock.assert_called_once()
        # _audit(action, session, details) — positional
        args = audit_mock.call_args.args
        assert args[0] == "settings_extraction_step"

    @pytest.mark.asyncio
    async def test_persist_called(self):
        session = _make_session()
        orchestrator = OnboardingOrchestrator()
        persist_mock = AsyncMock()
        with patch.object(orchestrator, "_audit", new=AsyncMock()), \
             patch.object(orchestrator, "_persist", new=persist_mock):
            await orchestrator.handle_settings_extraction_message(session, "")

        persist_mock.assert_called_once_with(session)
