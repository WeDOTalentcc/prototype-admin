"""
Integration Tests — Agendamento de entrevistas: conflitos reais via CalendarService.

Exercita o CalendarService real com Microsoft Graph mockado:
- check_interviewer_availability: detecta slots livres vs ocupados
- find_best_interview_time: usa Graph API para encontrar melhor horário
- _get_client: fallback para Graph quando Google Calendar não configurado
- Conflict gap logic: eventos que cobrem todo o dia = 0 slots
- Sending window: slots só dentro de 9h-18h do dia
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Helper para construir um CalendarService com graph mockado
# ---------------------------------------------------------------------------

def _build_calendar_service(graph_events: list[dict]) -> "CalendarService":
    from app.domains.interview_scheduling.services.calendar_service import CalendarService

    svc = CalendarService.__new__(CalendarService)

    mock_graph = AsyncMock()
    mock_graph.get_user_calendar_view = AsyncMock(return_value=graph_events)
    mock_graph.find_meeting_times = AsyncMock(return_value=[])
    mock_graph.find_available_time_slots = AsyncMock(return_value=[])

    svc.graph = mock_graph
    return svc


# ---------------------------------------------------------------------------
# Seção 1 — check_interviewer_availability: slot detection logic
# ---------------------------------------------------------------------------

class TestCheckInterviewerAvailabilitySlotDetection:

    @pytest.mark.asyncio
    async def test_empty_calendar_returns_slots_for_entire_day(self):
        """Calendário vazio: deve retornar múltiplos slots entre 9h-18h."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)  # Terça

        slots = await svc.check_interviewer_availability(
            interviewer_email="interviewer@test.com",
            date=date,
            duration_minutes=60,
        )

        assert len(slots) > 0, "Calendário vazio deve retornar slots disponíveis"
        for slot in slots:
            assert "start" in slot
            assert "end" in slot
            assert slot["duration_minutes"] == 60

    @pytest.mark.asyncio
    async def test_event_covering_full_day_returns_zero_slots(self):
        """Evento que cobre 9h-18h inteiro → nenhum slot disponível."""
        svc = _build_calendar_service(graph_events=[
            {
                "start": {"dateTime": "2026-04-07T09:00:00", "timeZone": "UTC"},
                "end":   {"dateTime": "2026-04-07T18:00:00", "timeZone": "UTC"},
            }
        ])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="interviewer@test.com",
            date=date,
            duration_minutes=60,
        )

        assert len(slots) == 0, "Agenda cheia não deve retornar slots"

    @pytest.mark.asyncio
    async def test_event_in_morning_returns_afternoon_slots_only(self):
        """Evento 9h-13h → apenas slots da tarde (13h-18h) disponíveis."""
        svc = _build_calendar_service(graph_events=[
            {
                "start": {"dateTime": "2026-04-07T09:00:00", "timeZone": "UTC"},
                "end":   {"dateTime": "2026-04-07T13:00:00", "timeZone": "UTC"},
            }
        ])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="interviewer@test.com",
            date=date,
            duration_minutes=60,
        )

        assert len(slots) > 0
        for slot in slots:
            slot_start_hour = int(slot["start"][11:13])  # ISO: "...T13:00:00..."
            assert slot_start_hour >= 13, \
                f"Slot {slot['start']} esperado após 13h"

    @pytest.mark.asyncio
    async def test_two_consecutive_events_with_no_gap_returns_no_slots(self):
        """Dois eventos consecutivos sem gap suficiente → nenhum slot livre."""
        svc = _build_calendar_service(graph_events=[
            {
                "start": {"dateTime": "2026-04-07T09:00:00", "timeZone": "UTC"},
                "end":   {"dateTime": "2026-04-07T13:00:00", "timeZone": "UTC"},
            },
            {
                "start": {"dateTime": "2026-04-07T13:00:00", "timeZone": "UTC"},
                "end":   {"dateTime": "2026-04-07T18:00:00", "timeZone": "UTC"},
            },
        ])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="interviewer@test.com",
            date=date,
            duration_minutes=60,
        )

        assert len(slots) == 0

    @pytest.mark.asyncio
    async def test_slots_respect_duration_minutes_parameter(self):
        """Duração passada deve ser usada nos slots retornados."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="interviewer@test.com",
            date=date,
            duration_minutes=90,
        )

        assert len(slots) > 0
        for slot in slots:
            assert slot["duration_minutes"] == 90

    @pytest.mark.asyncio
    async def test_default_duration_is_60_minutes_when_not_specified(self):
        """Sem duration_minutes explícito, padrão é 60 minutos."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="interviewer@test.com",
            date=date,
        )

        assert len(slots) > 0
        for slot in slots:
            assert slot["duration_minutes"] == 60


# ---------------------------------------------------------------------------
# Seção 2 — check_interviewer_availability: graph.get_user_calendar_view called
# ---------------------------------------------------------------------------

class TestCalendarServiceGraphCalls:

    @pytest.mark.asyncio
    async def test_graph_get_calendar_view_is_called_with_correct_email(self):
        """check_interviewer_availability deve chamar graph.get_user_calendar_view."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        await svc.check_interviewer_availability(
            interviewer_email="recruiter@company.com",
            date=date,
            duration_minutes=60,
        )

        svc.graph.get_user_calendar_view.assert_awaited_once()
        call_kwargs = svc.graph.get_user_calendar_view.call_args
        assert call_kwargs[1].get("user_email") == "recruiter@company.com" or \
               call_kwargs[0][0] == "recruiter@company.com"

    @pytest.mark.asyncio
    async def test_graph_query_time_window_starts_at_9am(self):
        """A janela de consulta ao graph deve começar às 9h do dia especificado."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        await svc.check_interviewer_availability(
            interviewer_email="r@company.com",
            date=date,
            duration_minutes=60,
        )

        call_kwargs = svc.graph.get_user_calendar_view.call_args[1]
        start_time = call_kwargs.get("start_time")
        assert start_time is not None
        assert start_time.hour == 9


# ---------------------------------------------------------------------------
# Seção 3 — _get_client: provider selection logic
# ---------------------------------------------------------------------------

class TestCalendarServiceProviderSelection:

    @pytest.mark.asyncio
    async def test_get_client_returns_graph_when_google_calendar_disabled(self):
        """_get_client deve retornar graph quando ENABLE_GOOGLE_CALENDAR=False."""
        from app.domains.interview_scheduling.services.calendar_service import CalendarService
        svc = _build_calendar_service(graph_events=[])

        with patch(
            "app.domains.interview_scheduling.services.calendar_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_GOOGLE_CALENDAR = False
            client = await svc._get_client(company_id=None, db=None)

        assert client is svc.graph

    @pytest.mark.asyncio
    async def test_get_client_returns_graph_when_no_company_id(self):
        """_get_client sem company_id deve retornar graph (Microsoft Graph)."""
        svc = _build_calendar_service(graph_events=[])

        with patch(
            "app.domains.interview_scheduling.services.calendar_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_GOOGLE_CALENDAR = True
            client = await svc._get_client(company_id=None, db=None)

        assert client is svc.graph


# ---------------------------------------------------------------------------
# Seção 4 — Slot ordering and boundary checks
# ---------------------------------------------------------------------------

class TestAvailabilitySlotOrdering:

    @pytest.mark.asyncio
    async def test_slots_start_at_or_after_9am(self):
        """Nenhum slot deve iniciar antes das 9h."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="r@c.com",
            date=date,
            duration_minutes=30,
        )

        for slot in slots:
            hour = int(slot["start"][11:13])
            assert hour >= 9, f"Slot {slot['start']} começa antes das 9h"

    @pytest.mark.asyncio
    async def test_slots_end_at_or_before_18h(self):
        """Nenhum slot deve terminar após as 18h."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="r@c.com",
            date=date,
            duration_minutes=60,
        )

        for slot in slots:
            end_hour = int(slot["end"][11:13])
            end_min = int(slot["end"][14:16])
            assert end_hour < 18 or (end_hour == 18 and end_min == 0), \
                f"Slot termina após 18h: {slot['end']}"

    @pytest.mark.asyncio
    async def test_each_slot_has_required_keys(self):
        """Cada slot deve ter as chaves 'start', 'end', 'duration_minutes'."""
        svc = _build_calendar_service(graph_events=[])
        date = datetime(2026, 4, 7, 0, 0, tzinfo=UTC)

        slots = await svc.check_interviewer_availability(
            interviewer_email="r@c.com",
            date=date,
            duration_minutes=60,
        )

        for slot in slots:
            assert "start" in slot, f"Slot sem 'start': {slot}"
            assert "end" in slot, f"Slot sem 'end': {slot}"
            assert "duration_minutes" in slot, f"Slot sem 'duration_minutes': {slot}"
