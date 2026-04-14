"""
Microsoft Graph API client.
Handles authentication and API calls to Microsoft Graph.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from msal import ConfidentialClientApplication

from app.core.config import settings

logger = logging.getLogger(__name__)


class GraphAPIClient:
    """
    Microsoft Graph API client for accessing user calendars, emails, etc.
    Uses OAuth 2.0 client credentials flow.
    """
    
    def __init__(self):
        """Initialize Graph API client."""
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.tenant_id = settings.AZURE_TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]
        
        self._access_token: str | None = None
        self._token_expires: datetime | None = None
        self._msal_app: ConfidentialClientApplication | None = None
    
    def _get_msal_app(self) -> ConfidentialClientApplication:
        """Get or create MSAL application."""
        if not self._msal_app:
            if not self.client_id or not self.client_secret or not self.tenant_id:
                raise ValueError(
                    "Microsoft Graph not configured. Set AZURE_CLIENT_ID, "
                    "AZURE_CLIENT_SECRET, and AZURE_TENANT_ID."
                )
            
            self._msal_app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
        
        return self._msal_app
    
    def get_access_token(self) -> str:
        """
        Get Microsoft Graph access token using client credentials flow.
        
        Returns:
            Access token string
        """
        # Check cached token
        if self._access_token and self._token_expires:
            if datetime.utcnow() < self._token_expires:
                return self._access_token
        
        # Get new token
        msal_app = self._get_msal_app()
        
        result = msal_app.acquire_token_for_client(scopes=self.scopes)
        
        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "Unknown error"))
            logger.error(f"Failed to acquire Graph API token: {error}")
            from app.shared.errors import LIAIntegrationError
            raise LIAIntegrationError(
                message=f"Falha ao obter token Graph API: {error}",
                code="GRAPH_TOKEN_FAILED",
                details={"error": error},
            )
        
        self._access_token = result["access_token"]
        expires_in = result.get("expires_in", 3600)
        self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 300)
        
        logger.info("Successfully acquired Microsoft Graph access token")
        return self._access_token
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Make authenticated request to Microsoft Graph API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: Graph API endpoint (e.g., "/me/calendar/events")
            data: Request body (for POST/PATCH)
            params: Query parameters
            
        Returns:
            Response JSON
        """
        token = self.get_access_token()
        
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30.0
            )
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                logger.error(f"Graph API error: {response.status_code} - {error_data}")
                from app.shared.errors import LIAIntegrationError
                raise LIAIntegrationError(
                    message=f"Graph API error: {response.status_code}",
                    code="GRAPH_API_ERROR",
                    details={"status_code": response.status_code, "error": error_data},
                )
            
            return response.json() if response.content else {}
    
    async def get_user_calendar_view(
        self,
        user_email: str,
        start_time: datetime,
        end_time: datetime
    ) -> list[dict[str, Any]]:
        """
        Get calendar events for a user within a time range.
        
        Args:
            user_email: User's email address
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of calendar events
        """
        endpoint = f"/users/{user_email}/calendar/calendarView"
        
        params = {
            "startDateTime": start_time.isoformat(),
            "endDateTime": end_time.isoformat(),
            "$select": "subject,start,end,location,attendees,organizer,isAllDay",
            "$orderby": "start/dateTime"
        }
        
        response = await self.make_request("GET", endpoint, params=params)
        return response.get("value", [])
    
    async def create_calendar_event(
        self,
        user_email: str,
        subject: str,
        start_time: datetime,
        end_time: datetime,
        attendees: list[str],
        location: str | None = None,
        body: str | None = None,
        is_online_meeting: bool = False
    ) -> dict[str, Any]:
        """
        Create a calendar event.
        
        Args:
            user_email: Organizer's email
            subject: Event subject/title
            start_time: Event start time
            end_time: Event end time
            attendees: List of attendee email addresses
            location: Event location
            body: Event description
            is_online_meeting: Create as Teams meeting
            
        Returns:
            Created event data
        """
        endpoint = f"/users/{user_email}/calendar/events"
        
        event_data = {
            "subject": subject,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            },
            "attendees": [
                {
                    "emailAddress": {"address": email},
                    "type": "required"
                }
                for email in attendees
            ]
        }
        
        if location:
            event_data["location"] = {"displayName": location}
        
        if body:
            event_data["body"] = {
                "contentType": "HTML",
                "content": body
            }
        
        if is_online_meeting:
            event_data["isOnlineMeeting"] = True
            event_data["onlineMeetingProvider"] = "teamsForBusiness"
        
        return await self.make_request("POST", endpoint, data=event_data)
    
    async def find_available_time_slots(
        self,
        organizer_email: str,
        attendee_emails: list[str],
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
        minimum_confidence: int = 50
    ) -> list[dict[str, Any]]:
        """
        Find available meeting times for attendees using findMeetingTimes API.
        
        Args:
            organizer_email: Organizer/meeting owner email (for user context)
            attendee_emails: List of required attendees
            duration_minutes: Meeting duration in minutes
            start_date: Search start date
            end_date: Search end date
            minimum_confidence: Minimum confidence percentage (0-100)
            
        Returns:
            List of suggested meeting times
        """
        # Use /users/{id}/findMeetingTimes for application permissions
        endpoint = f"/users/{organizer_email}/findMeetingTimes"
        
        request_data = {
            "attendees": [
                {
                    "emailAddress": {"address": email},
                    "type": "required"
                }
                for email in attendee_emails
            ],
            "timeConstraint": {
                "timeslots": [
                    {
                        "start": {
                            "dateTime": start_date.isoformat(),
                            "timeZone": "UTC"
                        },
                        "end": {
                            "dateTime": end_date.isoformat(),
                            "timeZone": "UTC"
                        }
                    }
                ]
            },
            "meetingDuration": f"PT{duration_minutes}M",
            "minimumAttendeePercentage": minimum_confidence,
            "returnSuggestionReasons": True
        }
        
        response = await self.make_request("POST", endpoint, data=request_data)
        return response.get("meetingTimeSuggestions", [])


# Global Graph API client instance
graph_client = GraphAPIClient()
