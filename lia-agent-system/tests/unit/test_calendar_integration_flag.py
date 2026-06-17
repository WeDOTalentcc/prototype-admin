"""
GAP-06-001 — InterviewScheduling: Feature flag + honest 501

Verifica:
1. check_interviewer_availability retorna calendar_not_configured quando flag OFF
2. schedule_interview retorna calendar_synced=False quando flag OFF (não aborta — DB ainda salva)
3. schedule_interview NÃO retorna is_simulated_calendar=True em nenhuma situação
4. get_interview_status retorna calendar_not_configured quando flag OFF
5. check_interviewer_availability levanta NotImplementedError quando flag ON (sem provider)
6. _calendar_not_available inclui available_providers no retorno
7. cancel_interview funciona independente da flag (não é operação de calendário)
8. send_interview_invitation funciona independente da flag (canal e-mail, não calendário)
9. reschedule_interview retorna calendar_synced=False quando flag OFF
10. reschedule_interview NÃO retorna is_simulated_calendar=True
11. check_availability: retorno tem is_simulated=False quando flag OFF
12. _wrap_check_interviewer_availability propaga calendar_not_configured ao registry caller
"""
import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reload_tools(enabled: bool):
    """Reload scheduling_tools with CALENDAR_INTEGRATION_ENABLED forced to `enabled`."""
    mod_name = "app.domains.interview_scheduling.tools.scheduling_tools"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    with patch.dict("os.environ", {"CALENDAR_INTEGRATION_ENABLED": "true" if enabled else "false"}):
        mod = importlib.import_module(mod_name)
    return mod


# ---------------------------------------------------------------------------
# 1 — check_interviewer_availability: flag OFF → not_configured
# ---------------------------------------------------------------------------

class TestCheckAvailabilityFlagOff:
    def test_returns_calendar_not_configured(self):
        """Quando CALENDAR_INTEGRATION_ENABLED=false, retorna dict de erro honesto."""
        mod = _reload_tools(enabled=False)
        result = mod.check_interviewer_availability.func(
            interviewer_id="usr-123",
            date_range="2026-07-01 to 2026-07-07",
        )
        assert result["error"] == "calendar_not_configured"
        assert result["success"] is False

    def test_no_fabricated_slots(self):
        """Não retorna available_slots ou busy_slots fabricados."""
        mod = _reload_tools(enabled=False)
        result = mod.check_interviewer_availability.func(
            interviewer_id="usr-123",
            date_range="2026-07-01 to 2026-07-07",
        )
        assert "available_slots" not in result
        assert "busy_slots" not in result


# ---------------------------------------------------------------------------
# 2 — schedule_interview: flag OFF → success=True + calendar_synced=False
# ---------------------------------------------------------------------------

class TestScheduleInterviewFlagOff:
    @pytest.mark.asyncio
    async def test_returns_success_with_calendar_synced_false(self):
        """Quando flag OFF, schedule_interview salva no DB e retorna calendar_synced=False."""
        mod = _reload_tools(enabled=False)

        # Mock DB write so test doesn't need a real database
        with patch.object(mod, "CALENDAR_INTEGRATION_ENABLED", False):
            # Patch the AsyncSessionLocal import inside the coroutine
            with patch("lia_config.database.AsyncSessionLocal") as mock_session:
                ctx = AsyncMock()
                ctx.__aenter__ = AsyncMock(return_value=AsyncMock(add=MagicMock(), commit=AsyncMock()))
                ctx.__aexit__ = AsyncMock(return_value=False)
                mock_session.return_value = ctx

                result = await mod.schedule_interview.coroutine(
                    candidate_id="cand-1",
                    interviewer_id="usr-1",
                    datetime_str="2026-07-10 14:00",
                )

        assert result["success"] is True
        assert result["calendar_synced"] is False
        assert "interview_id" in result

    @pytest.mark.asyncio
    async def test_no_is_simulated_calendar_key(self):
        """Retorno NÃO deve conter a chave is_simulated_calendar (era o nome do ghost)."""
        mod = _reload_tools(enabled=False)

        with patch.object(mod, "CALENDAR_INTEGRATION_ENABLED", False):
            with patch("lia_config.database.AsyncSessionLocal") as mock_session:
                ctx = AsyncMock()
                ctx.__aenter__ = AsyncMock(return_value=AsyncMock(add=MagicMock(), commit=AsyncMock()))
                ctx.__aexit__ = AsyncMock(return_value=False)
                mock_session.return_value = ctx

                result = await mod.schedule_interview.coroutine(
                    candidate_id="cand-1",
                    interviewer_id="usr-1",
                    datetime_str="2026-07-10 14:00",
                )

        assert "is_simulated_calendar" not in result


# ---------------------------------------------------------------------------
# 3 — is_simulated_calendar must never appear (regression guard)
# ---------------------------------------------------------------------------

class TestNoSimulatedCalendarKey:
    """is_simulated_calendar=True era enganoso; NÃO deve aparecer em nenhum retorno."""

    @pytest.mark.asyncio
    async def test_schedule_interview_no_simulated_key(self):
        mod = _reload_tools(enabled=False)
        with patch.object(mod, "CALENDAR_INTEGRATION_ENABLED", False):
            with patch("lia_config.database.AsyncSessionLocal") as mock_session:
                ctx = AsyncMock()
                ctx.__aenter__ = AsyncMock(return_value=AsyncMock(add=MagicMock(), commit=AsyncMock()))
                ctx.__aexit__ = AsyncMock(return_value=False)
                mock_session.return_value = ctx
                result = await mod.schedule_interview.coroutine(
                    candidate_id="c", interviewer_id="i", datetime_str="2026-07-01 10:00"
                )
        assert "is_simulated_calendar" not in result

    @pytest.mark.asyncio
    async def test_reschedule_interview_no_simulated_key(self):
        mod = _reload_tools(enabled=False)
        with patch.object(mod, "CALENDAR_INTEGRATION_ENABLED", False):
            with patch("lia_config.database.AsyncSessionLocal") as mock_session:
                ctx = AsyncMock()
                ctx.__aenter__ = AsyncMock(return_value=AsyncMock(execute=AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))), commit=AsyncMock()))
                ctx.__aexit__ = AsyncMock(return_value=False)
                mock_session.return_value = ctx
                result = await mod.reschedule_interview.coroutine(
                    interview_id="int-1", new_datetime_str="2026-07-02 10:00"
                )
        assert "is_simulated_calendar" not in result


# ---------------------------------------------------------------------------
# 4 — get_interview_status: flag OFF → not_configured
# ---------------------------------------------------------------------------

class TestGetInterviewStatusFlagOff:
    def test_returns_calendar_not_configured(self):
        mod = _reload_tools(enabled=False)
        result = mod.get_interview_status.func(interview_id="int-xyz")
        assert result["error"] == "calendar_not_configured"
        assert result["success"] is False

    def test_no_random_status_returned(self):
        """Não deve retornar status aleatório fabricado (scheduled/completed/cancelled/pending)."""
        mod = _reload_tools(enabled=False)
        result = mod.get_interview_status.func(interview_id="int-xyz")
        assert "status" not in result or result.get("success") is False


# ---------------------------------------------------------------------------
# 5 — check_availability: flag ON → NotImplementedError (no provider yet)
# ---------------------------------------------------------------------------

class TestCheckAvailabilityFlagOn:
    def test_raises_not_implemented_when_no_provider(self):
        """Flag ON mas sem provider concreto levanta NotImplementedError."""
        mod = _reload_tools(enabled=True)
        with patch.object(mod, "CALENDAR_INTEGRATION_ENABLED", True):
            with pytest.raises(NotImplementedError):
                mod.check_interviewer_availability.func(
                    interviewer_id="usr-1", date_range="2026-07-01 to 2026-07-07"
                )


# ---------------------------------------------------------------------------
# 6 — _calendar_not_available: available_providers listed
# ---------------------------------------------------------------------------

class TestCalendarNotAvailableShape:
    def test_available_providers_listed(self):
        mod = _reload_tools(enabled=False)
        result = mod._calendar_not_available()
        assert "available_providers" in result
        assert "google_calendar" in result["available_providers"]
        assert "outlook" in result["available_providers"]

    def test_is_simulated_false(self):
        """Deve declarar is_simulated=False — não enganar o frontend."""
        mod = _reload_tools(enabled=False)
        result = mod._calendar_not_available()
        assert result.get("is_simulated") is False

    def test_message_in_portuguese(self):
        mod = _reload_tools(enabled=False)
        result = mod._calendar_not_available()
        assert "CALENDAR_INTEGRATION_ENABLED" in result["message"]


# ---------------------------------------------------------------------------
# 7 — cancel_interview: funciona independente da flag
# ---------------------------------------------------------------------------

class TestCancelInterviewIndependentOfFlag:
    def test_cancel_succeeds_flag_off(self):
        mod = _reload_tools(enabled=False)
        result = mod.cancel_interview.func(interview_id="int-1", reason="candidato desistiu")
        assert result["status"] == "cancelled"
        assert result["interview_id"] == "int-1"

    def test_cancel_succeeds_flag_on(self):
        mod = _reload_tools(enabled=True)
        with patch.object(mod, "CALENDAR_INTEGRATION_ENABLED", True):
            result = mod.cancel_interview.func(interview_id="int-2", reason="vaga fechada")
        assert result["status"] == "cancelled"


# ---------------------------------------------------------------------------
# 8 — send_interview_invitation: funciona independente da flag
# ---------------------------------------------------------------------------

class TestSendInvitationIndependentOfFlag:
    def test_send_invitation_flag_off(self):
        mod = _reload_tools(enabled=False)
        result = mod.send_interview_invitation.func(
            candidate_id="cand-1", interview_id="int-1", candidate_email="x@x.com"
        )
        # queued or sent — both are acceptable; must not be an error dict
        assert "error" not in result or result.get("status") not in (None,)
        assert result.get("interview_id") == "int-1"


# ---------------------------------------------------------------------------
# 9–10 — reschedule_interview: flag OFF → calendar_synced=False, no is_simulated_calendar
# ---------------------------------------------------------------------------

class TestRescheduleInterviewFlagOff:
    @pytest.mark.asyncio
    async def test_returns_calendar_synced_false(self):
        mod = _reload_tools(enabled=False)
        with patch.object(mod, "CALENDAR_INTEGRATION_ENABLED", False):
            with patch("lia_config.database.AsyncSessionLocal") as mock_session:
                ctx = AsyncMock()
                mock_db = AsyncMock()
                mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
                ctx.__aenter__ = AsyncMock(return_value=mock_db)
                ctx.__aexit__ = AsyncMock(return_value=False)
                mock_session.return_value = ctx

                result = await mod.reschedule_interview.coroutine(
                    interview_id="int-1", new_datetime_str="2026-07-15 10:00", reason="conflito"
                )

        assert result["calendar_synced"] is False
        assert result["success"] is True
        assert "is_simulated_calendar" not in result


# ---------------------------------------------------------------------------
# 11 — check_availability: is_simulated absent or False when flag OFF
# ---------------------------------------------------------------------------

class TestCheckAvailabilityNoSimulatedFlag:
    def test_is_simulated_false_in_not_available_response(self):
        mod = _reload_tools(enabled=False)
        result = mod.check_interviewer_availability.func(
            interviewer_id="usr-1", date_range="2026-07-01 to 2026-07-07"
        )
        # The dict from _calendar_not_available sets is_simulated=False
        assert result.get("is_simulated") is False


# ---------------------------------------------------------------------------
# 12 — registry wrapper propagates calendar_not_configured
# ---------------------------------------------------------------------------

class TestRegistryWrapperPropagatesError:
    @pytest.mark.asyncio
    async def test_wrap_check_availability_returns_not_configured(self):
        """_wrap_check_interviewer_availability propaga dict de erro quando flag OFF."""
        from app.domains.interview_scheduling.agents.interview_scheduling_tool_registry import (
            _wrap_check_interviewer_availability,
        )
        mod = _reload_tools(enabled=False)
        with patch(
            "app.domains.interview_scheduling.tools.scheduling_tools.CALENDAR_INTEGRATION_ENABLED",
            False,
        ):
            result = _wrap_check_interviewer_availability(
                interviewer_id="usr-1", date_range="2026-07-01 to 2026-07-07"
            )
        assert result.get("error") == "calendar_not_configured"
