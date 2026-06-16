"""
Integration tests — W2.6: P1-4 auth nos endpoints proativos + calendar.

Auditoria 2026-04-26 (P1-4): 5+ endpoints internos do Teams sem
Depends(get_current_user). Atacante poderia disparar notificacoes falsas,
agendar entrevistas em nome de outros, etc.

Endpoints alvo (7):
  POST /send-notification
  POST /proactive/check
  POST /proactive/new-candidate
  POST /proactive/screening-complete
  POST /proactive/daily-digest
  POST /calendar/schedule
  POST /calendar/cancel
"""
from __future__ import annotations
import inspect
import pytest


_ENDPOINT_FNS = [
    "send_proactive_notification",
    "run_proactivity_checks",
    "notify_new_candidate",
    "notify_screening_complete",
    "send_daily_digest",
    "schedule_interview_via_teams",
    "cancel_interview_via_teams",
]


class TestProactiveAndCalendarEndpointsAuth:
    """All 7 internal endpoints must require Depends(get_current_user)."""

    @pytest.mark.parametrize("fn_name", _ENDPOINT_FNS)
    def test_endpoint_declares_get_current_user_dependency(self, fn_name):
        import app.api.v1.teams as mod
        fn = getattr(mod, fn_name)
        src = inspect.getsource(fn)
        assert "get_current_user" in src or "current_user" in src, (
            f"{fn_name} deve declarar Depends(get_current_user) (P1-4)"
        )
