"""
Google Calendar API client.

Espelha a interface de graph_client.py para facilitar a troca de provedor
no CalendarService (dual-provider). Usa Service Account (Google Workspace)
ou OAuth 2.0 user tokens armazenados em company_calendar_credentials.

Dependências:
  google-api-python-client>=2.100.0
  google-auth>=2.23.0
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.shared.resilience.circuit_breaker import GOOGLE_CALENDAR_CIRCUIT

logger = logging.getLogger(__name__)


class TimeSlot:
    """Represents an available time slot."""

    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}


class GoogleCalendarClient:
    """
    Google Calendar API client.

    Autenticação por empresa via Service Account (Google Workspace)
    ou OAuth 2.0. Credenciais carregadas do campo encrypted_credentials
    da tabela company_calendar_credentials.
    """

    def __init__(self, credentials_json: str | None = None, timezone: str = "America/Sao_Paulo"):
        """
        Initialize Google Calendar client.

        Args:
            credentials_json: JSON string with credentials (service account or OAuth tokens).
                              If None, falls back to GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON setting.
            timezone: Default timezone for events.
        """
        self._credentials_json = credentials_json or settings.GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON
        self.timezone = timezone or settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE
        self._service = None
        self._creds = None  # Kept for OAuth 2.0 token refresh

    def _get_service(self):
        """Lazy-initialize Google Calendar service. Auto-refreshes OAuth tokens on expiry."""
        if self._service is not None:
            # For OAuth 2.0 user tokens: check expiry and refresh in-place
            if (
                self._creds is not None
                and hasattr(self._creds, "expired")
                and self._creds.expired
                and getattr(self._creds, "refresh_token", None)
            ):
                try:
                    from google.auth.transport.requests import Request  # type: ignore[union-attr]
                    self._creds.refresh(Request())
                    logger.info("Google Calendar OAuth token refreshed successfully")
                except Exception as exc:
                    logger.error("Failed to refresh Google Calendar OAuth token: %s", exc)
                    self._service = None  # Force full rebuild on next call
                    raise RuntimeError(f"Google Calendar token refresh failed: {exc}")
            return self._service

        if not self._credentials_json:
            raise ValueError(
                "Google Calendar credentials not configured. "
                "Set GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON or provide credentials_json."
            )

        try:
            from google.oauth2 import service_account  # type: ignore[union-attr]
            from google.oauth2.credentials import Credentials  # type: ignore[union-attr]
            from googleapiclient.discovery import build  # type: ignore[union-attr]

            creds_data = json.loads(self._credentials_json)

            if creds_data.get("type") == "service_account":
                creds = service_account.Credentials.from_service_account_info(
                    creds_data,
                    scopes=["https://www.googleapis.com/auth/calendar"],
                )
            else:
                # OAuth 2.0 user token — include expiry so google-auth tracks freshness
                expiry = None
                if creds_data.get("expiry"):
                    expiry = datetime.fromisoformat(creds_data["expiry"])
                creds = Credentials(
                    token=creds_data.get("access_token"),
                    refresh_token=creds_data.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.GOOGLE_CALENDAR_CLIENT_ID,
                    client_secret=settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    scopes=creds_data.get("scopes", ["https://www.googleapis.com/auth/calendar"]),
                    expiry=expiry,
                )

            self._creds = creds
            self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            return self._service

        except ImportError:
            raise RuntimeError(
                "google-api-python-client and google-auth are required for Google Calendar. "
                "Install with: pip install google-api-python-client>=2.100.0 google-auth>=2.23.0"
            )

    async def create_calendar_event(
        self,
        attendees: list[str],
        start_time: datetime,
        duration_minutes: int,
        summary: str,
        description: str = "",
        create_meet_link: bool = True,
        organizer_email: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a Google Calendar event with optional Google Meet link.

        Args:
            attendees: List of attendee email addresses.
            start_time: Event start datetime (UTC).
            duration_minutes: Duration in minutes.
            summary: Event title.
            description: Event description / notes.
            create_meet_link: Whether to create a Google Meet link.
            organizer_email: Calendar owner email (for service account delegation).

        Returns:
            Dict with event_id, meet_link, html_link, start, end.
        """
        service = self._get_service()
        end_time = start_time + timedelta(minutes=duration_minutes)

        event_body: dict[str, Any] = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": self.timezone,
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": self.timezone,
            },
            "attendees": [{"email": email} for email in attendees],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        if create_meet_link:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"lia-{start_time.timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }

        calendar_id = organizer_email or "primary"

        def _insert():
            return (
                service.events()
                .insert(
                    calendarId=calendar_id,
                    body=event_body,
                    conferenceDataVersion=1 if create_meet_link else 0,
                    sendUpdates="all",
                )
                .execute()
            )

        result = await GOOGLE_CALENDAR_CIRCUIT.call(_insert)

        meet_link = None
        if create_meet_link:
            meet_link = (
                result.get("conferenceData", {})
                .get("entryPoints", [{}])[0]
                .get("uri")
            )

        return {
            "event_id": result["id"],
            "meet_link": meet_link,
            "html_link": result.get("htmlLink"),
            "start": result["start"]["dateTime"],
            "end": result["end"]["dateTime"],
        }

    async def get_user_busy_times(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, str]]:
        """
        Get busy time blocks for a user using freebusy API.

        Returns:
            List of dicts with 'start' and 'end' ISO strings.
        """
        service = self._get_service()
        body = {
            "timeMin": start_date.isoformat() + "Z",
            "timeMax": end_date.isoformat() + "Z",
            "items": [{"id": user_email}],
        }
        result = await GOOGLE_CALENDAR_CIRCUIT.call(
            lambda: service.freebusy().query(body=body).execute()
        )
        busy_slots = result.get("calendars", {}).get(user_email, {}).get("busy", [])
        return [{"start": slot["start"], "end": slot["end"]} for slot in busy_slots]

    async def update_calendar_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        **kwargs,
    ) -> dict[str, Any]:
        """Update an existing calendar event."""
        service = self._get_service()

        def _update():
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            event.update(kwargs)
            return (
                service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=event, sendUpdates="all")
                .execute()
            )

        return await GOOGLE_CALENDAR_CIRCUIT.call(_update)

    async def delete_calendar_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> bool:
        """Delete a calendar event. Returns True on success."""
        service = self._get_service()
        try:
            await GOOGLE_CALENDAR_CIRCUIT.call(
                lambda: service.events().delete(
                    calendarId=calendar_id, eventId=event_id, sendUpdates="all"
                ).execute()
            )
            return True
        except Exception as exc:
            logger.error("Failed to delete Google Calendar event %s: %s", event_id, exc)
            return False

    async def get_available_slots(
        self,
        organizer_email: str,
        attendees: list[str],
        duration_minutes: int,
        start: datetime,
        end: datetime,
        slot_step_minutes: int = 30,
    ) -> list[TimeSlot]:
        """
        Find available slots where all attendees are free.

        Args:
            organizer_email: Organizer (whose calendar is checked first).
            attendees: All attendee emails.
            duration_minutes: Required slot duration.
            start: Search window start.
            end: Search window end.
            slot_step_minutes: Resolution for slot generation (default 30 min).

        Returns:
            List of TimeSlot objects representing free windows.
        """
        all_emails = list({organizer_email, *attendees})
        service = self._get_service()

        body = {
            "timeMin": start.isoformat() + "Z",
            "timeMax": end.isoformat() + "Z",
            "items": [{"id": email} for email in all_emails],
        }
        freebusy = await GOOGLE_CALENDAR_CIRCUIT.call(
            lambda: service.freebusy().query(body=body).execute()
        )

        # Collect all busy blocks
        busy_blocks: list[tuple[datetime, datetime]] = []
        for calendar_data in freebusy.get("calendars", {}).values():
            for slot in calendar_data.get("busy", []):
                busy_start = datetime.fromisoformat(slot["start"].replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(slot["end"].replace("Z", "+00:00"))
                busy_blocks.append((busy_start.replace(tzinfo=None), busy_end.replace(tzinfo=None)))

        # Generate candidate slots and filter out busy ones
        slots: list[TimeSlot] = []
        current = start
        step = timedelta(minutes=slot_step_minutes)
        slot_duration = timedelta(minutes=duration_minutes)

        while current + slot_duration <= end:
            candidate_end = current + slot_duration
            is_free = all(
                not (current < b_end and candidate_end > b_start)
                for b_start, b_end in busy_blocks
            )
            if is_free:
                slots.append(TimeSlot(start=current, end=candidate_end))
            current += step

        return slots
