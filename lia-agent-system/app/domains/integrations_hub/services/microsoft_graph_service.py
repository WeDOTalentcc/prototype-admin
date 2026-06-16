"""
Microsoft Graph API Service for Teams, Calendar, and Bookings Integration.

This service provides:
- OAuth2 authentication with client credentials flow
- Create Teams online meetings with auto-generated join links
- Create/sync Outlook calendar events with meeting invites
- Microsoft Bookings integration for scheduling pages

Environment Variables Required:
- AZURE_CLIENT_ID: Azure AD Application (client) ID
- AZURE_CLIENT_SECRET: Azure AD Application client secret
- AZURE_TENANT_ID: Azure AD Directory (tenant) ID
"""
import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GraphAPIError(Exception):
    """Base exception for Microsoft Graph API errors."""
    def __init__(self, message: str, status_code: int, error_code: str | None = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class GraphAPIUnauthorizedError(GraphAPIError):
    """401 Unauthorized - Invalid or expired token."""
    def __init__(self, message: str = "Unauthorized - Invalid or expired token"):
        super().__init__(message, 401, "Unauthorized")


class GraphAPIForbiddenError(GraphAPIError):
    """403 Forbidden - Insufficient permissions."""
    def __init__(self, message: str = "Forbidden - Insufficient permissions for this operation"):
        super().__init__(message, 403, "Forbidden")


class GraphAPIRateLimitError(GraphAPIError):
    """429 Too Many Requests - Rate limit exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        super().__init__(message, 429, "TooManyRequests")
        self.retry_after = retry_after or 60


class GraphAPICalendarPermissionError(GraphAPIError):
    """User does not have calendar permissions."""
    def __init__(self, user_email: str):
        super().__init__(
            f"User {user_email} does not have calendar write permissions",
            403,
            "CalendarPermissionDenied"
        )
        self.user_email = user_email


class MeetingProvider(Enum):
    """Supported online meeting providers."""
    TEAMS = "teamsForBusiness"
    SKYPE = "skypeForBusiness"


class AttendeeType(Enum):
    """Types of meeting attendees."""
    REQUIRED = "required"
    OPTIONAL = "optional"


@dataclass
class MeetingAttendee:
    """Represents a meeting attendee."""
    email: str
    name: str
    type: AttendeeType = AttendeeType.REQUIRED


@dataclass
class TeamsOnlineMeeting:
    """Result of creating a Teams online meeting."""
    id: str
    join_url: str
    join_web_url: str
    subject: str
    start_time: datetime
    end_time: datetime
    organizer_email: str
    attendees: list[str]
    calendar_event_id: str | None = None
    dial_in_url: str | None = None
    video_teleconference_id: str | None = None


@dataclass
class CalendarEvent:
    """Result of creating a calendar event."""
    id: str
    subject: str
    start_time: datetime
    end_time: datetime
    location: str | None
    is_online_meeting: bool
    online_meeting_url: str | None
    web_link: str
    ical_uid: str


class MicrosoftGraphService:
    """
    Service for Microsoft Graph API integration.
    
    Provides functionality for:
    - Teams online meeting creation
    - Outlook calendar event management
    - Microsoft Bookings integration
    """
    
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        tenant_id: str | None = None
    ):
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.warning(
                "Microsoft Graph credentials not fully configured. "
                "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID."
            )
    
    @property
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return all([self.client_id, self.client_secret, self.tenant_id])

    async def health_check(self) -> dict[str, Any]:
        """
        Return structured health status for the Microsoft Graph integration.

        When credentials are configured, attempts a lightweight token acquisition
        to verify connectivity. Returns one of:
        - connected:       credentials present and token acquisition succeeded
        - not_configured:  one or more env vars absent
        - disconnected:    credentials present but token request failed
        """
        if not self.is_configured:
            missing = [
                v for v, val in [
                    ("AZURE_CLIENT_ID", self.client_id),
                    ("AZURE_CLIENT_SECRET", self.client_secret),
                    ("AZURE_TENANT_ID", self.tenant_id),
                ]
                if not val
            ]
            return {
                "status": "not_configured",
                "configured": False,
                "missing_vars": missing,
                "message": f"Microsoft Graph not configured — missing: {', '.join(missing)}",
            }
        try:
            await self._get_access_token()
            return {
                "status": "connected",
                "configured": True,
                "tenant_id": self.tenant_id,
            }
        except Exception as exc:
            logger.warning("[MicrosoftGraphService] health_check token acquisition failed: %s", exc)
            return {
                "status": "disconnected",
                "configured": True,
                "message": f"Token acquisition failed: {str(exc)[:200]}",
            }

    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token using client credentials flow.
        Tokens are cached and refreshed when expired.
        """
        if (
            self._access_token 
            and self._token_expires_at 
            and datetime.utcnow() < self._token_expires_at - timedelta(minutes=5)
        ):
            return self._access_token
        
        token_url = self.TOKEN_URL_TEMPLATE.format(tenant_id=self.tenant_id)
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get access token: {response.text}")
                from app.shared.errors import LIAIntegrationError
                raise LIAIntegrationError(
                    message=f"Falha na autenticação Microsoft Graph: {response.status_code}",
                    code="GRAPH_TOKEN_FAILED",
                    details={"status_code": response.status_code},
                )
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained Microsoft Graph access token")
            return self._access_token
    
    async def get_delegated_access_token_for_company(self, company_id: str) -> str | None:
        """
        Load the stored OAuth 2.0 delegated refresh token for a company and exchange it
        for a fresh access token.  This enables per-company calendar operations using
        user-granted permissions (Calendars.ReadWrite) rather than app-level credentials.

        Returns the access token string, or None if no delegated credentials are stored.
        Raises GraphAPIError if token refresh fails.
        """
        import json as _json
        import uuid as _uuid

        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.interview_scheduling.repositories.calendar_credentials_repository import (
                CalendarCredentialsRepository,
            )
            from app.shared.encryption import decrypt_value
        except ImportError as exc:
            logger.warning("[MicrosoftGraphService] delegated token: import failed — %s", exc)
            return None

        try:
            async with AsyncSessionLocal() as db:
                repo = CalendarCredentialsRepository(db)
                creds = await repo.get_credentials(_uuid.UUID(company_id), "microsoft")
        except Exception as exc:
            logger.warning("[MicrosoftGraphService] delegated token DB lookup failed: %s", exc)
            return None

        if not creds or not creds.is_active or not creds.encrypted_credentials:
            return None

        try:
            token_data = _json.loads(decrypt_value(creds.encrypted_credentials))
        except Exception as exc:
            logger.warning("[MicrosoftGraphService] delegated token decrypt failed: %s", exc)
            return None

        refresh_token = token_data.get("refresh_token")
        client_id = token_data.get("client_id") or self.client_id
        tenant_id = token_data.get("tenant_id") or self.tenant_id

        if not refresh_token or not client_id or not tenant_id:
            logger.warning("[MicrosoftGraphService] delegated token: missing refresh_token/client_id/tenant_id")
            return None

        token_url = self.TOKEN_URL_TEMPLATE.format(tenant_id=tenant_id)
        data = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "scope": "offline_access Calendars.ReadWrite",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if resp.status_code != 200:
            logger.error("[MicrosoftGraphService] delegated token refresh failed: %s — %s",
                         resp.status_code, resp.text[:300])
            raise GraphAPIError(
                f"Microsoft delegated token refresh failed: {resp.status_code}",
                resp.status_code,
            )

        refreshed = resp.json()
        access_token = refreshed.get("access_token")

        # Persist updated tokens back to DB so subsequent calls use the new refresh_token
        if refreshed.get("refresh_token"):
            try:
                from app.shared.encryption import encrypt_value
                updated_data = _json.dumps({
                    **token_data,
                    "access_token": access_token,
                    "refresh_token": refreshed["refresh_token"],
                    "expires_in": refreshed.get("expires_in"),
                })
                async with AsyncSessionLocal() as db:
                    repo = CalendarCredentialsRepository(db)
                    await repo.upsert_credentials(
                        company_id=_uuid.UUID(company_id),
                        provider="microsoft",
                        encrypted_credentials=encrypt_value(updated_data),
                        is_active=True,
                    )
                    await db.commit()
            except Exception as exc:
                logger.warning("[MicrosoftGraphService] delegated token re-persist failed: %s", exc)

        logger.info("[MicrosoftGraphService] delegated access token obtained for company %s", company_id)
        return access_token

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        params: dict | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to Microsoft Graph API with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            json_data: JSON body data
            params: Query parameters
            max_retries: Maximum number of retries for rate-limited requests
            retry_delay: Initial delay between retries (uses exponential backoff)
        
        Returns:
            Response JSON data
        
        Raises:
            GraphAPIUnauthorizedError: For 401 errors
            GraphAPIForbiddenError: For 403 errors
            GraphAPIRateLimitError: For 429 errors after retries exhausted
            GraphAPIError: For other API errors
        """
        token = access_token if access_token else await self._get_access_token()
        
        url = f"{self.GRAPH_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        last_exception: Exception | None = None
        
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data,
                        params=params,
                        timeout=30.0
                    )
                    
                    if response.status_code == 204:
                        return {}
                    
                    if response.status_code < 400:
                        return response.json()
                    
                    error_body = response.text
                    try:
                        error_json = response.json()
                        error_message = error_json.get("error", {}).get("message", error_body)
                        error_code = error_json.get("error", {}).get("code", "")
                    except Exception:
                        error_message = error_body
                        error_code = ""
                    
                    if response.status_code == 401:
                        self._access_token = None
                        self._token_expires_at = None
                        logger.error(f"Graph API 401 Unauthorized: {error_message}")
                        raise GraphAPIUnauthorizedError(error_message)
                    
                    elif response.status_code == 403:
                        logger.error(f"Graph API 403 Forbidden: {error_message}")
                        if "calendar" in endpoint.lower() or "event" in endpoint.lower():
                            user_email = endpoint.split("/users/")[1].split("/")[0] if "/users/" in endpoint else "unknown"
                            raise GraphAPICalendarPermissionError(user_email)
                        raise GraphAPIForbiddenError(error_message)
                    
                    elif response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", retry_delay * (2 ** attempt)))
                        logger.warning(f"Graph API 429 Rate Limited. Retry-After: {retry_after}s (attempt {attempt + 1}/{max_retries + 1})")
                        
                        if attempt < max_retries:
                            await asyncio.sleep(min(retry_after, 60))
                            continue
                        else:
                            raise GraphAPIRateLimitError(error_message, retry_after)
                    
                    else:
                        logger.error(f"Graph API error {response.status_code}: {error_message}")
                        raise GraphAPIError(error_message, response.status_code, error_code)
                        
            except (GraphAPIUnauthorizedError, GraphAPIForbiddenError, GraphAPICalendarPermissionError):
                raise
            except GraphAPIRateLimitError as e:
                last_exception = e
                if attempt >= max_retries:
                    raise
            except GraphAPIError:
                raise
            except httpx.TimeoutException as e:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries + 1}): {e}")
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                    continue
                raise GraphAPIError(f"Request timeout after {max_retries + 1} attempts", 408, "Timeout")
            except Exception as e:
                logger.error(f"Unexpected error during Graph API request: {e}")
                raise GraphAPIError(str(e), 500, "InternalError")
        
        if last_exception:
            raise last_exception
        raise GraphAPIError("Request failed after all retries", 500, "InternalError")
    
    async def create_teams_meeting_with_calendar_event(
        self,
        organizer_email: str,
        subject: str,
        start_time: datetime,
        duration_minutes: int = 60,
        attendees: list[MeetingAttendee] | None = None,
        body_content: str | None = None,
        location: str | None = None,
        timezone: str = "America/Sao_Paulo",
        send_invites: bool = True,
        company_id: str | None = None,
    ) -> TeamsOnlineMeeting:
        """
        Create a calendar event with Teams meeting link.
        
        This creates an Outlook calendar event with isOnlineMeeting=true,
        which automatically generates a Teams meeting link and sends
        calendar invites to all attendees.
        
        Args:
            organizer_email: Email of the meeting organizer (must be a user in the tenant)
            subject: Meeting subject/title
            start_time: Meeting start datetime
            duration_minutes: Meeting duration in minutes
            attendees: List of meeting attendees
            body_content: HTML content for meeting body/description
            location: Physical location (optional, Teams link is added automatically)
            timezone: Timezone for the meeting
            send_invites: Whether to send calendar invites to attendees
            company_id: Optional. When provided, uses stored per-company delegated OAuth
                        credentials (Calendars.ReadWrite) instead of app-level token.
        
        Returns:
            TeamsOnlineMeeting object with meeting details and join URL
        """
        if not self.is_configured:
            from app.shared.errors import LIAIntegrationError
            raise LIAIntegrationError(
                message="Microsoft Graph não configurado para este tenant",
                code="GRAPH_NOT_CONFIGURED",
            )

        delegated_token: str | None = None
        if company_id:
            try:
                delegated_token = await self.get_delegated_access_token_for_company(company_id)
            except Exception as exc:
                logger.warning("[MicrosoftGraphService] delegated token failed, falling back to app token: %s", exc)
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event_payload = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_content or f"<p>Você foi convidado para: {subject}</p>"
            },
            "start": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone
            },
            "end": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone
            },
            "isOnlineMeeting": True,
            "onlineMeetingProvider": MeetingProvider.TEAMS.value,
            "allowNewTimeProposals": True,
            "isReminderOn": True,
            "reminderMinutesBeforeStart": 15
        }
        
        if location:
            event_payload["location"] = {"displayName": location}
        
        if attendees:
            event_payload["attendees"] = [
                {
                    "emailAddress": {
                        "address": att.email,
                        "name": att.name
                    },
                    "type": att.type.value
                }
                for att in attendees
            ]
        
        endpoint = f"/users/{organizer_email}/events"
        
        if not send_invites:
            endpoint += "?sendInvites=false"
        
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Creating Teams meeting: {subject} for {organizer_email}")
        
        result = await self._make_request("POST", endpoint, json_data=event_payload,
                                          access_token=delegated_token)
        
        online_meeting = result.get("onlineMeeting", {})
        join_url = online_meeting.get("joinUrl", "")
        
        meeting = TeamsOnlineMeeting(
            id=result.get("id", ""),
            join_url=join_url,
            join_web_url=result.get("webLink", ""),
            subject=result.get("subject", subject),
            start_time=start_time,
            end_time=end_time,
            organizer_email=organizer_email,
            attendees=[att.email for att in (attendees or [])],
            calendar_event_id=result.get("id"),
            dial_in_url=online_meeting.get("dialInUrl"),
            video_teleconference_id=online_meeting.get("videoTeleconferenceId")
        )
        
        logger.info(f"Teams meeting created successfully. Join URL: {join_url}")
        
        return meeting
    
    async def create_standalone_teams_meeting(
        self,
        organizer_email: str,
        subject: str,
        start_time: datetime,
        duration_minutes: int = 60,
        attendees: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Create a standalone Teams online meeting (without calendar event).
        
        Use this for ad-hoc meetings that don't need calendar integration.
        
        Args:
            organizer_email: Email of the meeting organizer
            subject: Meeting subject
            start_time: Meeting start datetime
            duration_minutes: Duration in minutes
            attendees: List of attendee emails
        
        Returns:
            Dictionary with meeting details including joinWebUrl
        """
        if not self.is_configured:
            from app.shared.errors import LIAIntegrationError
            raise LIAIntegrationError(
                message="Microsoft Graph não configurado para este tenant",
                code="GRAPH_NOT_CONFIGURED",
            )
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        meeting_payload = {
            "subject": subject,
            "startDateTime": start_time.isoformat(),
            "endDateTime": end_time.isoformat(),
            "lobbyBypassSettings": {
                "scope": "organization",
                "isDialInBypassEnabled": True
            }
        }
        
        if attendees:
            meeting_payload["participants"] = {
                "attendees": [
                    {
                        "upn": email,
                        "role": "attendee"
                    }
                    for email in attendees
                ]
            }
        
        endpoint = f"/users/{organizer_email}/onlineMeetings"
        result = await self._make_request("POST", endpoint, json_data=meeting_payload)
        
        logger.info(f"Standalone Teams meeting created: {result.get('joinWebUrl')}")
        
        return result
    
    async def get_calendar_event(
        self,
        user_email: str,
        event_id: str
    ) -> CalendarEvent:
        """
        Get details of a calendar event.
        
        Args:
            user_email: Email of the calendar owner
            event_id: ID of the calendar event
        
        Returns:
            CalendarEvent object with event details
        """
        endpoint = f"/users/{user_email}/events/{event_id}"
        result = await self._make_request("GET", endpoint)
        
        return CalendarEvent(
            id=result.get("id", ""),
            subject=result.get("subject", ""),
            start_time=datetime.fromisoformat(result["start"]["dateTime"].replace("Z", "")),
            end_time=datetime.fromisoformat(result["end"]["dateTime"].replace("Z", "")),
            location=result.get("location", {}).get("displayName"),
            is_online_meeting=result.get("isOnlineMeeting", False),
            online_meeting_url=result.get("onlineMeeting", {}).get("joinUrl"),
            web_link=result.get("webLink", ""),
            ical_uid=result.get("iCalUId", "")
        )
    
    async def update_calendar_event(
        self,
        user_email: str,
        event_id: str,
        updates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update a calendar event.
        
        Args:
            user_email: Email of the calendar owner
            event_id: ID of the event to update
            updates: Dictionary of fields to update
        
        Returns:
            Updated event data
        """
        endpoint = f"/users/{user_email}/events/{event_id}"
        result = await self._make_request("PATCH", endpoint, json_data=updates)
        
        logger.info(f"Calendar event {event_id} updated")
        return result
    
    async def cancel_calendar_event(
        self,
        user_email: str,
        event_id: str,
        comment: str | None = None
    ) -> None:
        """
        Cancel a calendar event and notify attendees.
        
        Args:
            user_email: Email of the calendar owner
            event_id: ID of the event to cancel
            comment: Optional cancellation message to attendees
        """
        endpoint = f"/users/{user_email}/events/{event_id}/cancel"
        payload = {}
        if comment:
            payload["comment"] = comment
        
        await self._make_request("POST", endpoint, json_data=payload)
        logger.info(f"Calendar event {event_id} cancelled")
    
    async def get_user_availability(
        self,
        user_emails: list[str],
        start_time: datetime,
        end_time: datetime,
        timezone: str = "America/Sao_Paulo",
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Get free/busy availability for users.
        
        Args:
            user_emails: List of user emails to check
            start_time: Start of time range
            end_time: End of time range
            timezone: Timezone for the query
            company_id: Optional. When provided, uses stored per-company delegated OAuth
                        credentials instead of app-level token.
        
        Returns:
            Availability information for each user
        """
        delegated_token: str | None = None
        if company_id:
            try:
                delegated_token = await self.get_delegated_access_token_for_company(company_id)
            except Exception as exc:
                logger.warning("[MicrosoftGraphService] delegated token failed for availability, using app token: %s", exc)

        payload = {
            "schedules": user_emails,
            "startTime": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone
            },
            "endTime": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone
            },
            "availabilityViewInterval": 30
        }
        
        endpoint = "/me/calendar/getSchedule"
        result = await self._make_request("POST", endpoint, json_data=payload,
                                          access_token=delegated_token)
        
        return result
    
    async def get_bookings_businesses(self) -> list[dict[str, Any]]:
        """
        Get list of Microsoft Bookings businesses.
        
        Returns:
            List of Bookings businesses
        """
        endpoint = "/solutions/bookingBusinesses"
        result = await self._make_request("GET", endpoint)
        
        return result.get("value", [])
    
    async def get_bookings_services(
        self,
        business_id: str
    ) -> list[dict[str, Any]]:
        """
        Get services offered by a Bookings business.
        
        Args:
            business_id: ID of the Bookings business
        
        Returns:
            List of booking services
        """
        endpoint = f"/solutions/bookingBusinesses/{business_id}/services"
        result = await self._make_request("GET", endpoint)
        
        return result.get("value", [])
    
    async def create_bookings_appointment(
        self,
        business_id: str,
        service_id: str,
        customer_email: str,
        customer_name: str,
        start_time: datetime,
        duration_minutes: int = 60,
        staff_member_ids: list[str] | None = None,
        notes: str | None = None,
        timezone: str = "America/Sao_Paulo"
    ) -> dict[str, Any]:
        """
        Create an appointment in Microsoft Bookings.
        
        Args:
            business_id: Bookings business ID
            service_id: Service ID for the appointment
            customer_email: Customer's email
            customer_name: Customer's name
            start_time: Appointment start time
            duration_minutes: Duration in minutes
            staff_member_ids: List of staff member IDs to assign
            notes: Optional notes for the appointment
            timezone: Timezone
        
        Returns:
            Created appointment data
        """
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        payload = {
            "serviceId": service_id,
            "customerEmailAddress": customer_email,
            "customerName": customer_name,
            "startDateTime": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone
            },
            "endDateTime": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone
            },
            "isLocationOnline": True,
            "optOutOfCustomerEmail": False,
            "sendSmsReminder": False
        }
        
        if staff_member_ids:
            payload["staffMemberIds"] = staff_member_ids
        
        if notes:
            payload["customerNotes"] = notes
        
        endpoint = f"/solutions/bookingBusinesses/{business_id}/appointments"
        result = await self._make_request("POST", endpoint, json_data=payload)
        
        logger.info(f"Bookings appointment created: {result.get('id')}")
        
        return result
    
    async def get_booking_page_url(
        self,
        business_id: str
    ) -> str | None:
        """
        Get the public booking page URL for a business.
        
        Args:
            business_id: Bookings business ID
        
        Returns:
            Public booking page URL or None
        """
        endpoint = f"/solutions/bookingBusinesses/{business_id}"
        result = await self._make_request("GET", endpoint)
        
        return result.get("publicUrl")
    
    async def check_calendar_permission(
        self,
        user_email: str
    ) -> bool:
        """
        Check if the organizer has calendar write permissions.
        
        Args:
            user_email: Email of the user to check
        
        Returns:
            True if user has calendar permissions, False otherwise
        """
        if not self.is_configured:
            return False
        
        try:
            endpoint = f"/users/{user_email}/calendar"
            await self._make_request("GET", endpoint)
            return True
        except GraphAPIForbiddenError:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.warning(f"User {user_email} does not have calendar read permissions")
            return False
        except GraphAPICalendarPermissionError:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.warning(f"User {user_email} does not have calendar permissions")
            return False
        except GraphAPIUnauthorizedError:
            logger.error("Graph API authentication failed while checking calendar permissions")
            return False
        except Exception as e:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.warning(f"Failed to check calendar permissions for {user_email}: {e}")
            return False
    
    async def test_connection(self) -> dict[str, Any]:
        """
        Test the Microsoft Graph API connection.
        
        Returns:
            Dictionary with connection status and details
        """
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "Microsoft Graph credentials not configured",
                "configured": False
            }
        
        try:
            await self._get_access_token()
            
            endpoint = "/organization"
            result = await self._make_request("GET", endpoint)
            
            org_info = result.get("value", [{}])[0]
            
            return {
                "status": "connected",
                "message": "Successfully connected to Microsoft Graph API",
                "configured": True,
                "organization": {
                    "name": org_info.get("displayName"),
                    "id": org_info.get("id"),
                    "tenant_type": org_info.get("tenantType")
                }
            }
        except Exception as e:
            logger.error(f"Microsoft Graph connection test failed: {e}")
            return {
                "status": "disconnected",
                "message": str(e),
                "configured": True
            }


microsoft_graph_service = MicrosoftGraphService()
