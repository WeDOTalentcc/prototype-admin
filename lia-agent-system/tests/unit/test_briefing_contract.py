"""
test_briefing_contract.py — W1-2 contract test for daily_briefing (card 7.2).

harness-engineering sensor computacional:
Validates that the daily_briefing action handler returns the expected
fields and includes the legacy disclaimer. Detects regressions introduced
when BriefingService is migrated to rails_adapter.

TDD: RED (write tests) → GREEN (implementation already in place) → no REFACTOR needed.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


MOCK_BRIEFING = {
    "greeting": "Bom dia",
    "summary": {
        "interviews_today": 2,
        "tasks_today": 3,
        "urgent_count": 1,
    },
    "schedule": [
        {"time": "10:00", "title": "Entrevista com João"},
        {"time": "14:30", "title": "Triagem WSI — Beatriz"},
    ],
    "tasks": [
        {"title": "Revisar candidatos Vaga X"},
        {"title": "Enviar feedback triagem"},
    ],
}


class TestBriefingContractFields:
    """Sensor: response must contain expected top-level fields."""

    def test_briefing_service_import_ok(self):
        """Sensor: BriefingService is importable (not removed before 2026-07-16)."""
        from app.shared.services.briefing_service import BriefingService
        assert BriefingService is not None

    def test_briefing_service_has_generate_method(self):
        from app.shared.services.briefing_service import BriefingService
        svc = BriefingService()
        assert hasattr(svc, "generate_daily_briefing"), (
            "BriefingService.generate_daily_briefing() must exist until 2026-07-16. "
            "Do not remove before replacing with rails_adapter::briefing."
        )

    def test_briefing_service_has_deprecation_marker(self):
        """Sensor: ensure deprecation comment is present in source (not silently removed)."""
        import inspect
        from app.shared.services import briefing_service as bm
        src = inspect.getsource(bm)
        assert "2026-07-16" in src or "deprecated" in src.lower(), (
            "briefing_service.py deve manter o marcador @deprecated until 2026-07-16. "
            "Não remova sem implementar rails_adapter::briefing."
        )


class TestBriefingCapabilityMap:
    """Sensor: daily_briefing must be in capability_map for Phase 0.0 gate."""

    def test_daily_briefing_in_capability_map(self):
        from app.shared.services.capability_map_service import CapabilityMapService
        cap = CapabilityMapService.get("daily_briefing")
        assert cap is not None, (
            "daily_briefing ausente do capability_map.yaml. "
            "Adicione entry com chat_executable: true + navigate_fallback: /analytics "
            "para que o Phase 0.0 gate possa processar corretamente o card 7.2."
        )

    def test_daily_briefing_is_chat_executable(self):
        from app.shared.services.capability_map_service import CapabilityMapService
        cap = CapabilityMapService.get("daily_briefing")
        assert cap is not None
        assert cap.chat_executable is True, (
            "daily_briefing deve ter chat_executable=true — "
            "o resumo diário é processado via chat/LLM, não modal."
        )

    def test_daily_briefing_has_navigate_fallback(self):
        from app.shared.services.capability_map_service import CapabilityMapService
        cap = CapabilityMapService.get("daily_briefing")
        assert cap is not None
        assert cap.navigate_fallback == "/analytics", (
            "daily_briefing.navigate_fallback deve ser /analytics."
        )

    def test_daily_briefing_requires_no_entity(self):
        """daily_briefing is tenant-wide — no specific entity needed."""
        from app.shared.services.capability_map_service import CapabilityMapService
        reqs = CapabilityMapService.needs_entity("daily_briefing")
        assert reqs == [], (
            "daily_briefing não deve exigir entidade — é resumo do tenant como um todo."
        )


class TestBriefingLegacyDisclaimer:
    """Sensor: _generate_daily_briefing must inject _legacy_disclaimer into data."""

    @pytest.mark.asyncio
    async def test_legacy_disclaimer_injected_in_response(self):
        """Sensor: response data contains _legacy_disclaimer when using BriefingService."""
        with (
            patch("app.core.database.AsyncSessionLocal") as mock_session_cls,
            patch("app.shared.services.briefing_service.BriefingService") as mock_svc_cls,
        ):
            mock_svc = mock_svc_cls.return_value
            mock_svc.generate_daily_briefing = AsyncMock(return_value=MOCK_BRIEFING.copy())
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            from app.orchestrator.action_handlers.pipeline_actions import _generate_daily_briefing

            result = await _generate_daily_briefing(
                params={},
                context={"user_id": "user-123", "company_id": "comp-abc"},
            )

        assert result.status == "executed", f"Expected executed, got {result.status}: {result.message}"
        assert result.data is not None
        assert "_legacy_disclaimer" in result.data, (
            "_generate_daily_briefing deve injetar _legacy_disclaimer no data dict. "
            "Este campo indica ao cliente (UI + LLM) que os dados vêm do serviço legado "
            "e serão migrados para rails_adapter antes de 2026-07-16."
        )
        assert "2026-07-16" in result.data["_legacy_disclaimer"], (
            "_legacy_disclaimer deve mencionar a data de remoção planejada (2026-07-16) "
            "para que o consumidor saiba quando esperar a migração."
        )

    @pytest.mark.asyncio
    async def test_response_message_includes_greeting(self):
        """Sensor: message deve incluir o greeting da briefing."""
        with (
            patch("app.core.database.AsyncSessionLocal") as mock_session_cls,
            patch("app.shared.services.briefing_service.BriefingService") as mock_svc_cls,
        ):
            mock_svc = mock_svc_cls.return_value
            mock_svc.generate_daily_briefing = AsyncMock(return_value=MOCK_BRIEFING.copy())
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            from app.orchestrator.action_handlers.pipeline_actions import _generate_daily_briefing
            result = await _generate_daily_briefing({}, {"user_id": "u1", "company_id": "c1"})

        assert "Bom dia" in result.message or "hoje" in result.message.lower(), (
            "Response message deve incluir o greeting ou mencionar 'hoje'."
        )

    @pytest.mark.asyncio
    async def test_missing_user_id_returns_error(self):
        """Sensor: sem user_id, o handler deve retornar status error, não exception."""
        from app.orchestrator.action_handlers.pipeline_actions import _generate_daily_briefing
        result = await _generate_daily_briefing({}, {})
        assert result.status == "error", (
            "Sem user_id no contexto, daily_briefing deve retornar status='error' "
            "com mensagem amigável — nunca levantar exception."
        )
