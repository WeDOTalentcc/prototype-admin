"""
Calendar service for interview scheduling.
High-level business logic for managing interview appointments.

Dual-provider: seleciona Google Calendar ou Microsoft Graph por empresa,
via tabela company_calendar_credentials. Fallback: Microsoft Graph.
"""
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.shared.services.graph_client import graph_client
from app.shared.policy_middleware import get_policy_for_company, resolve_policy_value
from app.utils.datetime_helpers import parse_graph_datetime

logger = logging.getLogger(__name__)


async def _get_company_calendar_credentials(company_id: str, db: AsyncSession, provider: str | None = None):
    """
    Load company calendar credentials from DB.

    Args:
        company_id: Company UUID.
        db: Async DB session.
        provider: Optional provider filter ("google" | "microsoft"). When given, only
                  credentials for that provider are returned, avoiding ambiguity when
                  a company has both Google and Microsoft rows active.

    Returns None if no matching active credentials are found.
    """
    try:
        from app.domains.interview_scheduling.repositories.calendar_credentials_repository import (
            CalendarCredentialsRepository,
        )
        repo = CalendarCredentialsRepository(db)
        return await repo.get_active_credentials(company_id, provider)
    except Exception:
        return None


class _DelegatedGraphClient:
    """
    Thin wrapper around GraphAPIClient that injects a per-company delegated OAuth access token
    into every request, overriding the app-level client credentials token.

    This allows Microsoft calendar operations (create event, get availability, etc.) to run
    under the calendar owner's identity (Calendars.ReadWrite delegated scope) rather than
    the service account's application-level scope.
    """

    def __init__(self, base_client, delegated_token: str) -> None:
        self._base = base_client
        self._token = delegated_token

    async def make_request(self, method: str, endpoint: str, data=None, params=None):
        """Proxy make_request with delegated token injected into Authorization header."""
        import httpx

        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
            )
            if resp.status_code == 204:
                return {}
            resp.raise_for_status()
            return resp.json()

    async def get_user_calendar_view(self, user_email: str, start_time, end_time) -> list:
        """Get calendar events for a user using the delegated OAuth token."""
        endpoint = f"/users/{user_email}/calendar/calendarView"
        params = {
            "startDateTime": start_time.isoformat(),
            "endDateTime": end_time.isoformat(),
            "$select": "subject,start,end,location,attendees,organizer,isAllDay",
            "$orderby": "start/dateTime",
        }
        response = await self.make_request("GET", endpoint, params=params)
        return response.get("value", [])

    async def create_calendar_event(self, user_email, subject, start_time, end_time,
                                    attendees, location=None, body=None, is_online_meeting=False):
        """Create a calendar event using the delegated OAuth token."""
        endpoint = f"/users/{user_email}/calendar/events"
        event_data = {
            "subject": subject,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "attendees": [
                {"emailAddress": {"address": email}, "type": "required"}
                for email in attendees
            ],
        }
        if location:
            event_data["location"] = {"displayName": location}
        if body:
            event_data["body"] = {"contentType": "HTML", "content": body}
        if is_online_meeting:
            event_data["isOnlineMeeting"] = True
            event_data["onlineMeetingProvider"] = "teamsForBusiness"
        return await self.make_request("POST", endpoint, data=event_data)

    def __getattr__(self, name):
        """Fall back to base client for any other methods not explicitly overridden."""
        return getattr(self._base, name)


class _GoogleCalendarAdapter:
    """
    Adapter that wraps GoogleCalendarClient to expose the same interface expected by CalendarService:
        - create_calendar_event(user_email, subject, start_time, end_time, attendees, location, body, is_online_meeting)
        - get_user_calendar_view(user_email, start_time, end_time)

    GoogleCalendarClient has a different signature — this adapter bridges the gap so
    CalendarService._get_client() always returns a uniform client regardless of provider.
    """

    def __init__(self, google_client) -> None:
        self._client = google_client

    async def create_calendar_event(
        self,
        user_email: str,
        subject: str,
        start_time,
        end_time,
        attendees: list[str],
        location: str | None = None,
        body: str | None = None,
        is_online_meeting: bool = False,
    ) -> dict:
        """
        Translate CalendarService's generic call into GoogleCalendarClient.create_calendar_event().
        end_time is converted to duration_minutes as expected by the Google client.
        """
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        return await self._client.create_calendar_event(
            attendees=attendees,
            start_time=start_time,
            duration_minutes=duration_minutes,
            summary=subject,
            description=body or "",
            create_meet_link=is_online_meeting,
            organizer_email=user_email,
        )

    async def get_user_calendar_view(self, user_email: str, start_time, end_time) -> list:
        """
        Translate to GoogleCalendarClient.get_user_busy_times() and return busy slots
        in a shape compatible with the Graph calendarView format consumed by
        check_interviewer_availability().
        """
        busy_slots = await self._client.get_user_busy_times(
            user_email=user_email,
            start_date=start_time,
            end_date=end_time,
        )
        # Normalise to the shape that check_interviewer_availability expects
        # (each slot needs start.dateTime and end.dateTime)
        result = []
        for slot in busy_slots:
            result.append({
                "start": {"dateTime": slot["start"], "timeZone": "UTC"},
                "end": {"dateTime": slot["end"], "timeZone": "UTC"},
            })
        return result

    def __getattr__(self, name):
        """Delegate any other method call to the underlying GoogleCalendarClient."""
        return getattr(self._client, name)


class CalendarService:
    """
    Service for managing interview scheduling.
    Dual-provider: Google Calendar or Microsoft Graph (default).
    """

    def __init__(self):
        self.graph = graph_client

    async def _get_client(self, company_id: str | None, db: AsyncSession | None = None):
        """
        Return the appropriate calendar client for the company.

        Priority:
        1. Google Calendar (if ENABLE_GOOGLE_CALENDAR=True and company has Google credentials)
        2. Microsoft Graph with delegated OAuth (if company has stored provider=microsoft credentials)
        3. Microsoft Graph with app-level client credentials (default)
        """
        if company_id and db:
            # Provider-specific lookups to avoid ambiguity when multiple rows exist

            # 1. Google Calendar (user-delegated)
            if settings.ENABLE_GOOGLE_CALENDAR:
                google_creds = await _get_company_calendar_credentials(company_id, db, provider="google")
                if google_creds and google_creds.is_active:
                    try:
                        from app.domains.integrations_hub.services.google_calendar_client import GoogleCalendarClient
                        from app.shared.encryption import decrypt_value
                        raw_json = decrypt_value(google_creds.encrypted_credentials)
                        google_client = GoogleCalendarClient(
                            credentials_json=raw_json,
                            timezone=google_creds.timezone or settings.GOOGLE_CALENDAR_DEFAULT_TIMEZONE,
                        )
                        # Wrap in adapter so it exposes the same interface as GraphAPIClient
                        return _GoogleCalendarAdapter(google_client)
                    except Exception as exc:
                        logger.warning(
                            "Failed to load Google Calendar client for company %s: %s — falling back to Graph",
                            company_id,
                            exc,
                        )

            # 2. Microsoft Calendar with per-company delegated OAuth token
            ms_creds = await _get_company_calendar_credentials(company_id, db, provider="microsoft")
            if ms_creds and ms_creds.is_active:
                try:
                    from app.domains.integrations_hub.services.microsoft_graph_service import MicrosoftGraphService
                    ms_service = MicrosoftGraphService()
                    delegated_token = await ms_service.get_delegated_access_token_for_company(company_id)
                    if delegated_token:
                        return _DelegatedGraphClient(self.graph, delegated_token)
                except Exception as exc:
                    logger.warning(
                        "Failed to load Microsoft delegated token for company %s: %s — using app token",
                        company_id,
                        exc,
                    )

        return self.graph
    
    async def check_interviewer_availability(
        self,
        interviewer_email: str,
        date: datetime,
        duration_minutes: int | None = None,
        company_id: str | None = None,
        db=None
    ) -> list[dict[str, Any]]:
        """
        Check interviewer's availability for a specific date.
        Returns list of available time slots.
        
        Args:
            interviewer_email: Interviewer's email address
            date: Date to check (will check business hours from policy or 9am-6pm)
            duration_minutes: Duration of interview slot (None = use policy or default 60)
            company_id: Optional company ID to lookup scheduling policy
            db: Optional database session for policy lookup
            
        Returns:
            List of available time slots with start/end times
        """
        start_hour = 9
        end_hour = 18
        effective_duration = duration_minutes

        if company_id and db:
            try:
                policy = await get_policy_for_company(company_id, db)
                allowed_hours = resolve_policy_value(
                    policy, "scheduling_rules", "allowed_hours",
                    override=None, default={"start": "09:00", "end": "18:00"},
                )
                start_hour = int(allowed_hours["start"].split(":")[0])
                end_hour = int(allowed_hours["end"].split(":")[0])
                if effective_duration is None:
                    effective_duration = resolve_policy_value(
                        policy, "scheduling_rules", "default_duration_minutes",
                        override=None, default=60,
                    )
            except Exception as e:
                logger.warning(f"Failed to load scheduling policy for calendar: {e}")
        
        if effective_duration is None:
            effective_duration = 60

        start_of_day = date.replace(hour=start_hour, minute=0, second=0, microsecond=0, tzinfo=UTC)
        end_of_day = date.replace(hour=end_hour, minute=0, second=0, microsecond=0, tzinfo=UTC)

        # Select calendar client (uses per-company delegated token when available)
        client = await self._get_client(company_id, db)

        # Get existing events
        events = await client.get_user_calendar_view(
            user_email=interviewer_email,
            start_time=start_of_day,
            end_time=end_of_day
        )
        
        # Find all free slots in each gap
        available_slots = []
        current_time = start_of_day
        
        for event in events:
            # Parse with timezone hint from Graph response
            event_start_tz = event["start"].get("timeZone", "UTC")
            event_end_tz = event["end"].get("timeZone", "UTC")
            event_start = parse_graph_datetime(event["start"]["dateTime"], event_start_tz)
            event_end = parse_graph_datetime(event["end"]["dateTime"], event_end_tz)
            
            # Generate all possible slots in the gap before this event
            gap_duration = (event_start - current_time).total_seconds() / 60
            if gap_duration >= effective_duration:
                slot_time = current_time
                while (event_start - slot_time).total_seconds() >= effective_duration * 60:
                    available_slots.append({
                        "start": slot_time.isoformat(),
                        "end": (slot_time + timedelta(minutes=effective_duration)).isoformat(),
                        "duration_minutes": effective_duration
                    })
                    # Move to next 30-minute boundary for cleaner scheduling
                    slot_time += timedelta(minutes=30)
            
            current_time = max(current_time, event_end)
        
        # Generate all slots after last event until end of day
        if (end_of_day - current_time).total_seconds() >= effective_duration * 60:
            slot_time = current_time
            while (end_of_day - slot_time).total_seconds() >= effective_duration * 60:
                available_slots.append({
                    "start": slot_time.isoformat(),
                    "end": (slot_time + timedelta(minutes=effective_duration)).isoformat(),
                    "duration_minutes": effective_duration
                })
                slot_time += timedelta(minutes=30)
        
        return available_slots
    
    async def find_best_interview_time(
        self,
        organizer_email: str,
        interviewer_emails: list[str],
        candidate_email: str,
        duration_minutes: int | None = None,
        preferred_days: list[str] | None = None,
        company_id: str | None = None,
        db=None
    ) -> list[dict[str, Any]]:
        """
        Find best interview times using Graph findMeetingTimes API.
        
        Args:
            organizer_email: Meeting organizer (HR/recruiter)
            interviewer_emails: List of interviewer emails
            candidate_email: Candidate's email
            duration_minutes: Interview duration (None = use policy or default 60)
            preferred_days: List of preferred days (Mon, Tue, etc.)
            company_id: Optional company ID to lookup scheduling policy
            db: Optional database session for policy lookup
            
        Returns:
            List of suggested meeting times sorted by confidence
        """
        effective_duration = duration_minutes
        if company_id and db:
            try:
                policy = await get_policy_for_company(company_id, db)
                if effective_duration is None:
                    effective_duration = resolve_policy_value(
                        policy, "scheduling_rules", "default_duration_minutes",
                        override=None, default=60,
                    )
                if preferred_days is None:
                    preferred_days = resolve_policy_value(
                        policy, "scheduling_rules", "allowed_days",
                        override=None, default=None,
                    )
            except Exception as e:
                logger.warning(f"Failed to load scheduling policy for find_best_time: {e}")
        
        if effective_duration is None:
            effective_duration = 60

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)
        
        all_attendees = interviewer_emails + [candidate_email]
        
        suggestions = await self.graph.find_available_time_slots(
            organizer_email=organizer_email,
            attendee_emails=all_attendees,
            duration_minutes=effective_duration,
            start_date=start_date,
            end_date=end_date,
            minimum_confidence=50
        )
        
        if preferred_days:
            filtered = []
            for suggestion in suggestions:
                slot_tz = suggestion["meetingTimeSlot"]["start"].get("timeZone", "UTC")
                start_time = parse_graph_datetime(
                    suggestion["meetingTimeSlot"]["start"]["dateTime"],
                    slot_tz
                )
                day_name = start_time.strftime("%a")
                if day_name in preferred_days:
                    filtered.append(suggestion)
            return filtered
        
        return suggestions
    
    async def schedule_interview(
        self,
        organizer_email: str,
        candidate_name: str,
        candidate_email: str,
        interviewer_emails: list[str],
        position: str,
        start_time: datetime,
        duration_minutes: int | None = None,
        location: str | None = None,
        as_teams_meeting: bool = True,
        notes: str | None = None,
        company_id: str | None = None,
        db=None
    ) -> dict[str, Any]:
        """
        Schedule an interview appointment.
        
        Args:
            organizer_email: HR/recruiter email (event organizer)
            candidate_name: Candidate's full name
            candidate_email: Candidate's email
            interviewer_emails: List of interviewer emails
            position: Job position being interviewed for
            start_time: Interview start time
            duration_minutes: Interview duration (None = use policy or default 60)
            location: Physical location (if not Teams)
            as_teams_meeting: Create as Teams online meeting
            notes: Additional notes for the interview
            company_id: Optional company ID to lookup scheduling policy
            db: Optional database session for policy lookup
            
        Returns:
            Created calendar event data
        """
        effective_duration = duration_minutes
        if company_id and db and duration_minutes is None:
            try:
                policy = await get_policy_for_company(company_id, db)
                effective_duration = resolve_policy_value(
                    policy, "scheduling_rules", "default_duration_minutes",
                    override=None, default=60,
                )
            except Exception as e:
                logger.warning(f"Failed to load scheduling policy for schedule_interview: {e}")

        if effective_duration is None:
            effective_duration = 60

        end_time = start_time + timedelta(minutes=effective_duration)
        
        subject = f"Entrevista: {candidate_name} - {position}"
        
        # Build email body
        body_parts = [
            "<h2>Entrevista de Seleção</h2>",
            f"<p><strong>Candidato:</strong> {candidate_name}</p>",
            f"<p><strong>Posição:</strong> {position}</p>",
            f"<p><strong>Duração:</strong> {effective_duration} minutos</p>",
        ]
        
        if notes:
            body_parts.append(f"<p><strong>Observações:</strong><br/>{notes}</p>")
        
        body_parts.append(
            "<hr/>"
            "<p><em>Este agendamento foi criado automaticamente pela LIA "
            "(Learning Intelligence Assistant) da WedoTalent.</em></p>"
        )
        
        body_html = "\n".join(body_parts)
        
        # All attendees (candidate + interviewers)
        all_attendees = [candidate_email] + interviewer_emails

        # Select calendar client — uses per-company delegated token when available
        client = await self._get_client(company_id, db)

        event = await client.create_calendar_event(
            user_email=organizer_email,
            subject=subject,
            start_time=start_time,
            end_time=end_time,
            attendees=all_attendees,
            location=location,
            body=body_html,
            is_online_meeting=as_teams_meeting
        )
        
        logger.info(f"Interview scheduled: {subject} at {start_time.isoformat()}")
        
        return event
    
    async def cancel_interview(
        self,
        organizer_email: str,
        event_id: str,
        cancellation_message: str | None = None
    ) -> bool:
        """
        Cancel a scheduled interview.
        
        Args:
            organizer_email: Event organizer email
            event_id: Calendar event ID
            cancellation_message: Optional message to attendees
            
        Returns:
            True if cancelled successfully
        """
        try:
            endpoint = f"/users/{organizer_email}/calendar/events/{event_id}/cancel"
            
            data = {}
            if cancellation_message:
                data["comment"] = cancellation_message
            
            await self.graph.make_request("POST", endpoint, data=data)
            
            logger.info(f"Interview cancelled: event_id={event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel interview: {e}")
            return False
    
    async def reschedule_interview(
        self,
        organizer_email: str,
        event_id: str,
        new_start_time: datetime,
        new_duration_minutes: int | None = None
    ) -> dict[str, Any]:
        """
        Reschedule an existing interview.
        
        Args:
            organizer_email: Event organizer email
            event_id: Calendar event ID
            new_start_time: New start time
            new_duration_minutes: New duration (optional)
            
        Returns:
            Updated event data
        """
        endpoint = f"/users/{organizer_email}/calendar/events/{event_id}"
        
        # Get current event to preserve attendees/details
        current_event = await self.graph.make_request("GET", endpoint)
        
        # Calculate new end time
        if new_duration_minutes:
            new_end_time = new_start_time + timedelta(minutes=new_duration_minutes)
        else:
            # Preserve original duration
            start_tz = current_event["start"].get("timeZone", "UTC")
            end_tz = current_event["end"].get("timeZone", "UTC")
            original_start = parse_graph_datetime(current_event["start"]["dateTime"], start_tz)
            original_end = parse_graph_datetime(current_event["end"]["dateTime"], end_tz)
            duration = original_end - original_start
            new_end_time = new_start_time + duration
        
        # Update event
        update_data = {
            "start": {
                "dateTime": new_start_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": new_end_time.isoformat(),
                "timeZone": "UTC"
            }
        }
        
        updated_event = await self.graph.make_request("PATCH", endpoint, data=update_data)
        
        logger.info(f"Interview rescheduled: event_id={event_id} to {new_start_time.isoformat()}")
        
        return updated_event


    async def create_generic_event(
        self,
        title: str,
        start_time: str,
        organizer_id: str,
        description: str = "",
        location: str = "",
        duration_minutes: int = 60,
    ) -> dict[str, Any]:
        """
        Persist a generic calendar commitment (non-interview) to calendar_events table.
        Returns the created event data or raises on failure.
        """
        import uuid as uuid_mod
        from datetime import datetime

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        event_id = str(uuid_mod.uuid4())

        start_dt = None
        if start_time:
            try:
                from app.orchestrator.action_executor import _resolve_ptbr_datetime
                resolved = _resolve_ptbr_datetime(start_time)
                start_dt = resolved.isoformat() if resolved else start_time
            except Exception:
                try:
                    from dateutil import parser as dt_parser
                    start_dt = dt_parser.parse(start_time, dayfirst=True).isoformat()
                except Exception:
                    start_dt = start_time

        async with AsyncSessionLocal() as db:
            await db.execute(
                # RLS-EXEMPT: calendar_events — user-scoped via organizer_id
                text("""
                    INSERT INTO calendar_events
                        (id, title, description, location, start_time,
                         duration_minutes, organizer_id, event_type, created_at, updated_at)
                    VALUES
                        (:id, :title, :description, :location, :start_time,
                         :duration, CAST(:organizer_id AS uuid), 'generic', NOW(), NOW())
                """),
                {
                    "id": event_id,
                    "title": title,
                    "description": description,
                    "location": location,
                    "start_time": start_dt,
                    "duration": duration_minutes,
                    "organizer_id": organizer_id,
                },
            )
            await db.commit()

        return {
            "event_id": event_id,
            "title": title,
            "datetime": start_dt or start_time,
            "location": location,
            "duration_minutes": duration_minutes,
            "created_at": datetime.utcnow().isoformat(),
        }


# Global calendar service instance
calendar_service = CalendarService()


def get_calendar_service() -> "CalendarService":
    return calendar_service
