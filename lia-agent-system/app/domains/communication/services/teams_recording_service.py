"""
Teams Recording Service - Obtém gravações e transcrições do Microsoft Teams via Graph API.

A transcrição do Teams é GRATUITA (incluída no Microsoft 365).
Usa /communications/onlineMeetings/{meetingId}/transcripts endpoint.
"""
import logging
import re
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.shared.services.graph_client import graph_client

logger = logging.getLogger(__name__)


class TeamsTranscript(BaseModel):
    """Transcrição de reunião do Teams."""
    meeting_id: str
    transcript_id: str
    content: str
    created_at: datetime
    language: str = "pt-BR"


class TeamsRecording(BaseModel):
    """Gravação de reunião do Teams."""
    meeting_id: str
    recording_id: str
    download_url: str
    duration_seconds: float | None = None
    size_bytes: int | None = None


class TeamsRecordingService:
    """
    Service to fetch Teams meeting recordings and transcripts via Microsoft Graph API.
    
    Teams transcription is FREE (included in Microsoft 365).
    No need for external STT for Teams meetings!
    
    Required scopes (application permissions):
    - OnlineMeetingTranscript.Read.All (for transcripts)
    - OnlineMeetingRecording.Read.All (for recordings)
    
    Note: Transcripts API requires beta endpoint in some cases.
    """
    
    def __init__(self):
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.graph_beta_url = "https://graph.microsoft.com/beta"
        self._graph = graph_client
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        use_beta: bool = False,
        accept_content_type: str | None = None
    ) -> Any:
        """
        Make authenticated request to Microsoft Graph API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            data: Request body for POST/PATCH
            params: Query parameters
            use_beta: Use beta API endpoint
            accept_content_type: Custom Accept header for content downloads
            
        Returns:
            Response data (JSON or text depending on content type)
        """
        token = self._graph.get_access_token()
        base_url = self.graph_beta_url if use_beta else self.graph_base_url
        url = f"{base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        if accept_content_type:
            headers["Accept"] = accept_content_type
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=60.0
            )
            
            if response.status_code == 404:
                logger.warning(f"Resource not found: {endpoint}")
                return None
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                logger.error(f"Graph API error: {response.status_code} - {error_data}")
                from app.shared.errors import LIAIntegrationError
                raise LIAIntegrationError(
                    message=f"Graph API error: {response.status_code}",
                    code="GRAPH_API_ERROR",
                    details={"status_code": response.status_code, "error": error_data},
                )
            
            if not response.content:
                return {}
            
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            else:
                return response.text
    
    async def list_meeting_transcripts(
        self,
        meeting_id: str,
        organizer_id: str
    ) -> list[dict[str, Any]]:
        """
        List all available transcripts for a meeting.
        
        Args:
            meeting_id: The online meeting ID (joinMeetingIdSettings.joinMeetingId or 
                       the meeting ID from calendar event onlineMeeting property)
            organizer_id: The organizer's user ID or email
            
        Returns:
            List of transcript metadata
        """
        endpoint = f"/users/{organizer_id}/onlineMeetings/{meeting_id}/transcripts"
        
        try:
            response = await self._make_request("GET", endpoint, use_beta=True)
            
            if response is None:
                return []
            
            transcripts = response.get("value", [])
            
            while "@odata.nextLink" in response:
                next_link = response["@odata.nextLink"]
                next_endpoint = next_link.replace(self.graph_beta_url, "")
                response = await self._make_request("GET", next_endpoint, use_beta=True)
                if response:
                    transcripts.extend(response.get("value", []))
            
            logger.info(f"Found {len(transcripts)} transcripts for meeting {meeting_id}")
            return transcripts
            
        except Exception as e:
            logger.error(f"Failed to list transcripts for meeting {meeting_id}: {e}")
            return []
    
    async def get_transcript_content(
        self,
        meeting_id: str,
        organizer_id: str,
        transcript_id: str,
        format: str = "text/vtt"
    ) -> str | None:
        """
        Get the actual transcript content.
        
        Args:
            meeting_id: Online meeting ID
            organizer_id: Organizer's user ID or email
            transcript_id: Transcript ID from list_meeting_transcripts
            format: Content format - "text/vtt" or "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        Returns:
            Transcript content as string (VTT format) or None
        """
        endpoint = f"/users/{organizer_id}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
        params = {"$format": format}
        
        try:
            content = await self._make_request(
                "GET",
                endpoint,
                params=params,
                use_beta=True,
                accept_content_type=format
            )
            return content if content else None
            
        except Exception as e:
            logger.error(f"Failed to get transcript content: {e}")
            return None
    
    async def get_meeting_transcript(
        self,
        meeting_id: str,
        organizer_id: str
    ) -> TeamsTranscript | None:
        """
        Get transcript for a Teams meeting.
        
        Args:
            meeting_id: The online meeting ID (from calendar event)
            organizer_id: The organizer's user ID or email
            
        Returns:
            TeamsTranscript with VTT content or None if not available
        """
        transcripts = await self.list_meeting_transcripts(meeting_id, organizer_id)
        
        if not transcripts:
            logger.info(f"No transcripts available for meeting {meeting_id}")
            return None
        
        latest_transcript = sorted(
            transcripts,
            key=lambda x: x.get("createdDateTime", ""),
            reverse=True
        )[0]
        
        transcript_id = latest_transcript.get("id")
        if not transcript_id:
            return None
        
        content = await self.get_transcript_content(
            meeting_id=meeting_id,
            organizer_id=organizer_id,
            transcript_id=transcript_id,
            format="text/vtt"
        )
        
        if not content:
            return None
        
        created_at_str = latest_transcript.get("createdDateTime", "")
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.utcnow()
        
        return TeamsTranscript(
            meeting_id=meeting_id,
            transcript_id=transcript_id,
            content=content,
            created_at=created_at,
            language=latest_transcript.get("locale", "pt-BR")
        )
    
    async def list_meeting_recordings(
        self,
        meeting_id: str,
        organizer_id: str
    ) -> list[dict[str, Any]]:
        """
        List all available recordings for a meeting.
        
        Args:
            meeting_id: Online meeting ID
            organizer_id: Organizer's user ID or email
            
        Returns:
            List of recording metadata
        """
        endpoint = f"/users/{organizer_id}/onlineMeetings/{meeting_id}/recordings"
        
        try:
            response = await self._make_request("GET", endpoint, use_beta=True)
            
            if response is None:
                return []
            
            recordings = response.get("value", [])
            
            while "@odata.nextLink" in response:
                next_link = response["@odata.nextLink"]
                next_endpoint = next_link.replace(self.graph_beta_url, "")
                response = await self._make_request("GET", next_endpoint, use_beta=True)
                if response:
                    recordings.extend(response.get("value", []))
            
            logger.info(f"Found {len(recordings)} recordings for meeting {meeting_id}")
            return recordings
            
        except Exception as e:
            logger.error(f"Failed to list recordings for meeting {meeting_id}: {e}")
            return []
    
    async def get_recording_download_url(
        self,
        meeting_id: str,
        organizer_id: str,
        recording_id: str
    ) -> str | None:
        """
        Get download URL for a recording.
        
        Args:
            meeting_id: Online meeting ID
            organizer_id: Organizer's user ID or email
            recording_id: Recording ID
            
        Returns:
            Download URL or None
        """
        endpoint = f"/users/{organizer_id}/onlineMeetings/{meeting_id}/recordings/{recording_id}/content"
        
        try:
            token = self._graph.get_access_token()
            url = f"{self.graph_beta_url}{endpoint}"
            
            headers = {
                "Authorization": f"Bearer {token}",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method="GET",
                    url=url,
                    headers=headers,
                    follow_redirects=False,
                    timeout=30.0
                )
                
                if response.status_code in (302, 307):
                    return response.headers.get("Location")
                elif response.status_code == 200:
                    return url
                else:
                    logger.error(f"Failed to get recording URL: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get recording download URL: {e}")
            return None
    
    async def get_meeting_recording(
        self,
        meeting_id: str,
        organizer_id: str
    ) -> TeamsRecording | None:
        """
        Get recording download URL for a Teams meeting.
        
        Args:
            meeting_id: The online meeting ID
            organizer_id: The organizer's user ID or email
            
        Returns:
            TeamsRecording with download URL or None
        """
        recordings = await self.list_meeting_recordings(meeting_id, organizer_id)
        
        if not recordings:
            logger.info(f"No recordings available for meeting {meeting_id}")
            return None
        
        latest_recording = sorted(
            recordings,
            key=lambda x: x.get("createdDateTime", ""),
            reverse=True
        )[0]
        
        recording_id = latest_recording.get("id")
        if not recording_id:
            return None
        
        download_url = await self.get_recording_download_url(
            meeting_id=meeting_id,
            organizer_id=organizer_id,
            recording_id=recording_id
        )
        
        if not download_url:
            return None
        
        return TeamsRecording(
            meeting_id=meeting_id,
            recording_id=recording_id,
            download_url=download_url,
            duration_seconds=latest_recording.get("recordingContentDuration"),
            size_bytes=latest_recording.get("recordingContentLength")
        )
    
    def parse_vtt_to_text(self, vtt_content: str) -> str:
        """
        Parse VTT (WebVTT) format transcript to plain text.
        
        VTT format example:
        WEBVTT
        
        00:00:00.000 --> 00:00:05.000
        <v Speaker Name>Hello, welcome to the meeting</v>
        
        Returns plain text with speaker attribution.
        """
        if not vtt_content:
            return ""
        
        lines = vtt_content.strip().split("\n")
        text_parts = []
        current_speaker = None
        
        timestamp_pattern = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}")
        speaker_pattern = re.compile(r"<v\s+([^>]+)>([^<]*)</v>")
        
        for line in lines:
            line = line.strip()
            
            if not line or line == "WEBVTT" or line.startswith("NOTE"):
                continue
            
            if timestamp_pattern.match(line):
                continue
            
            if line.isdigit():
                continue
            
            speaker_match = speaker_pattern.search(line)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                text = speaker_match.group(2).strip()
                
                if speaker != current_speaker:
                    current_speaker = speaker
                    text_parts.append(f"\n{speaker}: {text}")
                else:
                    text_parts.append(text)
            else:
                clean_text = re.sub(r"<[^>]+>", "", line).strip()
                if clean_text:
                    text_parts.append(clean_text)
        
        result = " ".join(text_parts)
        result = re.sub(r"\s+", " ", result)
        result = result.replace(" \n", "\n").strip()
        
        return result
    
    def extract_speaker_segments(self, vtt_content: str) -> list[dict[str, Any]]:
        """
        Extract speaker segments from VTT transcript.
        
        Returns list of:
        {
            "speaker": "Speaker Name",
            "start_time": "00:00:00",
            "end_time": "00:00:05",
            "text": "Hello, welcome to the meeting"
        }
        """
        if not vtt_content:
            return []
        
        segments = []
        lines = vtt_content.strip().split("\n")
        
        timestamp_pattern = re.compile(
            r"^(\d{2}:\d{2}:\d{2})\.\d{3}\s*-->\s*(\d{2}:\d{2}:\d{2})\.\d{3}"
        )
        speaker_pattern = re.compile(r"<v\s+([^>]+)>([^<]*)</v>")
        
        current_start = None
        current_end = None
        current_text_lines = []
        
        for line in lines:
            line = line.strip()
            
            if not line or line == "WEBVTT" or line.startswith("NOTE") or line.isdigit():
                continue
            
            timestamp_match = timestamp_pattern.match(line)
            if timestamp_match:
                if current_text_lines and current_start:
                    full_text = " ".join(current_text_lines)
                    speaker_match = speaker_pattern.search(full_text)
                    
                    if speaker_match:
                        speaker = speaker_match.group(1).strip()
                        text = speaker_match.group(2).strip()
                    else:
                        speaker = "Unknown"
                        text = re.sub(r"<[^>]+>", "", full_text).strip()
                    
                    if text:
                        segments.append({
                            "speaker": speaker,
                            "start_time": current_start,
                            "end_time": current_end,
                            "text": text
                        })
                
                current_start = timestamp_match.group(1)
                current_end = timestamp_match.group(2)
                current_text_lines = []
            else:
                current_text_lines.append(line)
        
        if current_text_lines and current_start:
            full_text = " ".join(current_text_lines)
            speaker_match = speaker_pattern.search(full_text)
            
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                text = speaker_match.group(2).strip()
            else:
                speaker = "Unknown"
                text = re.sub(r"<[^>]+>", "", full_text).strip()
            
            if text:
                segments.append({
                    "speaker": speaker,
                    "start_time": current_start,
                    "end_time": current_end,
                    "text": text
                })
        
        return segments
    
    async def get_online_meeting_by_join_url(
        self,
        join_url: str,
        user_id: str
    ) -> dict[str, Any] | None:
        """
        Get online meeting details by join URL.
        
        Args:
            join_url: Teams meeting join URL
            user_id: User ID or email to search meetings for
            
        Returns:
            Meeting details or None
        """
        import urllib.parse
        encoded_url = urllib.parse.quote(join_url, safe="")
        
        endpoint = f"/users/{user_id}/onlineMeetings?$filter=JoinWebUrl eq '{encoded_url}'"
        
        try:
            response = await self._make_request("GET", endpoint, use_beta=True)
            
            if response and response.get("value"):
                return response["value"][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get meeting by join URL: {e}")
            return None
    
    async def get_meeting_attendance_report(
        self,
        meeting_id: str,
        organizer_id: str
    ) -> list[dict[str, Any]]:
        """
        Get attendance report for a meeting.
        
        Args:
            meeting_id: Online meeting ID
            organizer_id: Organizer's user ID or email
            
        Returns:
            List of attendance records
        """
        endpoint = f"/users/{organizer_id}/onlineMeetings/{meeting_id}/attendanceReports"
        
        try:
            response = await self._make_request("GET", endpoint, use_beta=True)
            
            if response is None:
                return []
            
            reports = response.get("value", [])
            
            attendance_records = []
            for report in reports:
                report_id = report.get("id")
                if report_id:
                    records_endpoint = f"{endpoint}/{report_id}/attendanceRecords"
                    records_response = await self._make_request(
                        "GET", records_endpoint, use_beta=True
                    )
                    if records_response:
                        attendance_records.extend(records_response.get("value", []))
            
            return attendance_records
            
        except Exception as e:
            logger.error(f"Failed to get attendance report: {e}")
            return []


teams_recording_service = TeamsRecordingService()
