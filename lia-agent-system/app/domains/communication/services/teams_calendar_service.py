"""
Teams Calendar Service — Interview scheduling via Microsoft Graph.

Wraps the existing microsoft_graph_service to provide a
Teams-friendly interface for scheduling interviews directly
from chat commands or card button actions.

Prerequisites (configured in Azure AD):
  - Calendars.ReadWrite
  - OnlineMeetings.ReadWrite
  - User.Read (for participant lookup)
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

PLATFORM_URL = os.environ.get("WEDOTALENT_PLATFORM_URL", "https://app.wedotalent.com").rstrip("/")


class TeamsCalendarService:
    """
    Schedules interviews via Microsoft Graph Calendar API.
    Creates Outlook events with Teams Meeting links automatically.
    """

    def is_configured(self) -> bool:
        from app.shared.services.microsoft_graph_service import microsoft_graph_service
        return microsoft_graph_service.is_configured()

    async def schedule_interview(
        self,
        *,
        title: str,
        recruiter_email: str,
        candidate_name: str,
        candidate_email: str | None = None,
        start_time: datetime,
        duration_minutes: int = 60,
        vacancy_title: str | None = None,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a Teams Meeting + Outlook calendar event.

        Returns:
          {
            success: bool,
            join_url: str,          # Teams meeting link
            event_id: str,          # Outlook event ID (for cancel/reschedule)
            start_time: str,
            end_time: str,
            message: str,           # Human-readable summary
          }
        """
        try:
            from app.shared.services.microsoft_graph_service import (
                CreateTeamsMeetingRequest,
                microsoft_graph_service,
            )

            if not self.is_configured():
                return {
                    "success": False,
                    "message": "⚠️ Microsoft Graph não configurado. Defina AZURE_CLIENT_ID, AZURE_CLIENT_SECRET e AZURE_TENANT_ID.",
                }

            attendees = [recruiter_email]
            if candidate_email:
                attendees.append(candidate_email)

            # Build description with platform deep link
            description_parts = [
                f"Entrevista com {candidate_name}",
            ]
            if vacancy_title:
                description_parts.append(f"Vaga: {vacancy_title}")
            if candidate_id:
                description_parts.append(
                    f"Ver candidato: {PLATFORM_URL}/candidatos/{candidate_id}"
                )
            if notes:
                description_parts.append(f"Notas: {notes}")
            description = "\n".join(description_parts)

            end_time = start_time + timedelta(minutes=duration_minutes)

            req = CreateTeamsMeetingRequest(
                subject=title,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                attendees=attendees,
                organizer_email=recruiter_email,
                description=description,
                is_online_meeting=True,
            )

            meeting = await microsoft_graph_service.create_teams_meeting_with_calendar_event(req)

            start_fmt = start_time.strftime("%d/%m/%Y às %H:%M")
            return {
                "success": True,
                "join_url": meeting.join_url,
                "join_web_url": getattr(meeting, "join_web_url", meeting.join_url),
                "event_id": meeting.calendar_event_id or meeting.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "message": (
                    f"✅ Entrevista agendada!\n"
                    f"📅 {start_fmt} ({duration_minutes} min)\n"
                    f"👥 {candidate_name}" + (f" • {vacancy_title}" if vacancy_title else "") + "\n"
                    f"🔗 [Entrar na reunião]({meeting.join_url})"
                ),
                "attendees": attendees,
            }

        except Exception as e:
            logger.error(f"[TeamsCalendarService] schedule_interview error: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ Erro ao agendar: {str(e)}. Verifique as permissões do Azure AD.",
            }

    async def cancel_interview(
        self,
        event_id: str,
        organizer_email: str,
        cancellation_message: str | None = None,
    ) -> dict[str, Any]:
        """Cancel an existing interview event."""
        try:
            from app.shared.services.microsoft_graph_service import microsoft_graph_service
            if not self.is_configured():
                return {"success": False, "message": "Microsoft Graph não configurado."}

            await microsoft_graph_service.cancel_calendar_event(
                event_id=event_id,
                user_email=organizer_email,
                cancellation_message=cancellation_message or "Entrevista cancelada via WeDOTalent.",
            )
            return {"success": True, "message": "✅ Entrevista cancelada. Participantes foram notificados."}

        except Exception as e:
            logger.error(f"[TeamsCalendarService] cancel_interview error: {e}", exc_info=True)
            return {"success": False, "message": f"❌ Erro ao cancelar: {str(e)}"}

    async def reschedule_interview(
        self,
        event_id: str,
        organizer_email: str,
        new_start_time: datetime,
        duration_minutes: int = 60,
    ) -> dict[str, Any]:
        """Reschedule an existing interview to a new time."""
        try:
            from app.shared.services.microsoft_graph_service import microsoft_graph_service
            if not self.is_configured():
                return {"success": False, "message": "Microsoft Graph não configurado."}

            new_end_time = new_start_time + timedelta(minutes=duration_minutes)
            await microsoft_graph_service.update_calendar_event(
                event_id=event_id,
                user_email=organizer_email,
                updates={
                    "start": {"dateTime": new_start_time.isoformat(), "timeZone": "America/Sao_Paulo"},
                    "end":   {"dateTime": new_end_time.isoformat(),   "timeZone": "America/Sao_Paulo"},
                },
            )
            start_fmt = new_start_time.strftime("%d/%m/%Y às %H:%M")
            return {
                "success": True,
                "message": f"✅ Entrevista reagendada para {start_fmt}.",
                "start_time": new_start_time.isoformat(),
                "end_time": new_end_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"[TeamsCalendarService] reschedule_interview error: {e}", exc_info=True)
            return {"success": False, "message": f"❌ Erro ao reagendar: {str(e)}"}

    def render_schedule_card(
        self,
        candidate_name: str,
        vacancy_title: str,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Adaptive Card with a date/time picker for scheduling interviews.
        Submitted via Action.Submit → POST /api/v1/teams/calendar/schedule
        """
        from datetime import date
        from datetime import timedelta as td
        tomorrow = (date.today() + td(days=1)).isoformat()

        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"📅 Agendar entrevista — {candidate_name}",
                    "weight": "Bolder",
                    "size": "Medium",
                },
                {
                    "type": "TextBlock",
                    "text": f"Vaga: **{vacancy_title}**",
                    "spacing": "None",
                },
                {
                    "type": "Input.Date",
                    "id": "interview_date",
                    "label": "Data",
                    "min": tomorrow,
                    "value": tomorrow,
                },
                {
                    "type": "Input.Time",
                    "id": "interview_time",
                    "label": "Horário",
                    "value": "10:00",
                },
                {
                    "type": "Input.ChoiceSet",
                    "id": "duration",
                    "label": "Duração",
                    "value": "60",
                    "choices": [
                        {"title": "30 minutos", "value": "30"},
                        {"title": "45 minutos", "value": "45"},
                        {"title": "1 hora",     "value": "60"},
                        {"title": "1h30",       "value": "90"},
                    ],
                },
                {
                    "type": "Input.Text",
                    "id": "recruiter_email",
                    "label": "Seu e-mail (organizador)",
                    "placeholder": "recruiter@empresa.com",
                    "style": "Email",
                },
                {
                    "type": "Input.Text",
                    "id": "candidate_email",
                    "label": "E-mail do candidato (opcional)",
                    "placeholder": "candidato@email.com",
                    "style": "Email",
                },
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "✅ Confirmar agendamento",
                    "style": "positive",
                    "data": {
                        "action": "schedule_interview",
                        "candidate_name": candidate_name,
                        "vacancy_title": vacancy_title,
                        "candidate_id": candidate_id or "",
                        "vacancy_id": vacancy_id or "",
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Cancelar",
                    "data": {"action": "cancel_scheduling"},
                },
            ],
            "msteams": {"width": "Full"},
        }


teams_calendar_service = TeamsCalendarService()
