"""
Merge.dev ATS Service
Unified API for 40+ ATS platforms via Merge.dev
"""
import os
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MergeATSService:
    """
    Service for integrating with Merge.dev's Unified ATS API.
    Supports: Greenhouse, Lever, Workable, BambooHR, iCIMS, etc.
    """
    
    def __init__(self):
        self.base_url = os.getenv("MERGE_API_BASE_URL", "https://api.merge.dev/api/ats/v1")
        self.api_key = os.getenv("MERGE_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _headers(self, account_token: str) -> Dict[str, str]:
        """Get headers for Merge API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Account-Token": account_token,
            "Content-Type": "application/json"
        }
    
    async def list_candidates(
        self,
        account_token: str,
        cursor: Optional[str] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """List all candidates from the linked ATS."""
        client = await self.get_client()
        params = {"page_size": page_size}
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get(
            f"{self.base_url}/candidates",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_candidate(self, account_token: str, candidate_id: str) -> Dict[str, Any]:
        """Get a specific candidate by ID."""
        client = await self.get_client()
        response = await client.get(
            f"{self.base_url}/candidates/{candidate_id}",
            headers=self._headers(account_token)
        )
        response.raise_for_status()
        return response.json()
    
    async def create_candidate(
        self,
        account_token: str,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new candidate in the linked ATS."""
        client = await self.get_client()
        
        emails = [{"value": email, "email_address_type": "PERSONAL"}] if email else []
        phones = [{"value": phone, "phone_number_type": "MOBILE"}] if phone else []
        
        data = {
            "model": {
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "title": title,
                "email_addresses": emails,
                "phone_numbers": phones,
                **kwargs
            }
        }
        
        response = await client.post(
            f"{self.base_url}/candidates",
            headers=self._headers(account_token),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def update_candidate(
        self,
        account_token: str,
        candidate_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update an existing candidate."""
        client = await self.get_client()
        data = {"model": kwargs}
        
        response = await client.patch(
            f"{self.base_url}/candidates/{candidate_id}",
            headers=self._headers(account_token),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def list_applications(
        self,
        account_token: str,
        candidate_id: Optional[str] = None,
        job_id: Optional[str] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """List applications, optionally filtered by candidate or job."""
        client = await self.get_client()
        params = {}
        if candidate_id:
            params["candidate_id"] = candidate_id
        if job_id:
            params["job_id"] = job_id
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get(
            f"{self.base_url}/applications",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_application(self, account_token: str, application_id: str) -> Dict[str, Any]:
        """Get a specific application by ID."""
        client = await self.get_client()
        response = await client.get(
            f"{self.base_url}/applications/{application_id}",
            headers=self._headers(account_token)
        )
        response.raise_for_status()
        return response.json()
    
    async def create_application(
        self,
        account_token: str,
        candidate_id: str,
        job_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new application linking candidate to job."""
        client = await self.get_client()
        data = {
            "model": {
                "candidate": candidate_id,
                "job": job_id,
                **kwargs
            }
        }
        
        response = await client.post(
            f"{self.base_url}/applications",
            headers=self._headers(account_token),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def update_application_stage(
        self,
        account_token: str,
        application_id: str,
        stage_id: str
    ) -> Dict[str, Any]:
        """Update an application's current stage."""
        client = await self.get_client()
        data = {
            "model": {
                "current_stage": stage_id
            }
        }
        
        response = await client.patch(
            f"{self.base_url}/applications/{application_id}",
            headers=self._headers(account_token),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def list_jobs(
        self,
        account_token: str,
        status: Optional[str] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all jobs from the linked ATS."""
        client = await self.get_client()
        params = {}
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get(
            f"{self.base_url}/jobs",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_job(self, account_token: str, job_id: str) -> Dict[str, Any]:
        """Get a specific job by ID."""
        client = await self.get_client()
        response = await client.get(
            f"{self.base_url}/jobs/{job_id}",
            headers=self._headers(account_token)
        )
        response.raise_for_status()
        return response.json()
    
    async def list_interviews(
        self,
        account_token: str,
        application_id: Optional[str] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """List scheduled interviews."""
        client = await self.get_client()
        params = {}
        if application_id:
            params["application_id"] = application_id
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get(
            f"{self.base_url}/scheduled-interviews",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def create_interview(
        self,
        account_token: str,
        application_id: str,
        scheduled_at: datetime,
        interviewers: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Schedule a new interview."""
        client = await self.get_client()
        data = {
            "model": {
                "application": application_id,
                "scheduled_at": scheduled_at.isoformat(),
                "interviewers": interviewers,
                **kwargs
            }
        }
        
        response = await client.post(
            f"{self.base_url}/scheduled-interviews",
            headers=self._headers(account_token),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def list_stages(
        self,
        account_token: str,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List job interview stages (pipeline stages)."""
        client = await self.get_client()
        params = {}
        if job_id:
            params["job_id"] = job_id
        
        response = await client.get(
            f"{self.base_url}/job-interview-stages",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_sync_status(self, account_token: str) -> Dict[str, Any]:
        """Get the sync status for a linked account."""
        client = await self.get_client()
        response = await client.get(
            f"{self.base_url}/sync-status",
            headers=self._headers(account_token)
        )
        response.raise_for_status()
        return response.json()
    
    async def force_resync(self, account_token: str) -> Dict[str, Any]:
        """Force a resync of all data for the linked account."""
        client = await self.get_client()
        response = await client.post(
            f"{self.base_url}/force-resync",
            headers=self._headers(account_token)
        )
        response.raise_for_status()
        return response.json()
    
    async def list_users(
        self,
        account_token: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """List users (recruiters, hiring managers) from the linked ATS."""
        client = await self.get_client()
        params = {}
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get(
            f"{self.base_url}/users",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def list_departments(
        self,
        account_token: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """List departments from the linked ATS."""
        client = await self.get_client()
        params = {}
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get(
            f"{self.base_url}/departments",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def list_offices(
        self,
        account_token: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """List offices/locations from the linked ATS."""
        client = await self.get_client()
        params = {}
        if cursor:
            params["cursor"] = cursor
        
        response = await client.get(
            f"{self.base_url}/offices",
            headers=self._headers(account_token),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def add_note_to_candidate(
        self,
        account_token: str,
        candidate_id: str,
        note_content: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a note to a candidate."""
        client = await self.get_client()
        data = {
            "model": {
                "candidate": candidate_id,
                "body": note_content
            }
        }
        if user_id:
            data["model"]["user"] = user_id
        
        response = await client.post(
            f"{self.base_url}/notes",
            headers=self._headers(account_token),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def map_lia_stage_to_merge(self, lia_stage: str) -> str:
        """Map LIA pipeline stages to common Merge stage names."""
        stage_mapping = {
            "triagem": "Application Review",
            "screening": "Phone Screen",
            "entrevista": "Interview",
            "avaliacao": "Assessment",
            "oferta": "Offer",
            "contratado": "Hired",
            "reprovado": "Rejected",
            "desistencia": "Withdrawn"
        }
        return stage_mapping.get(lia_stage.lower(), lia_stage)
    
    def map_merge_stage_to_lia(self, merge_stage: str) -> str:
        """Map Merge stage names to LIA pipeline stages."""
        stage_mapping = {
            "application review": "triagem",
            "phone screen": "screening",
            "interview": "entrevista",
            "assessment": "avaliacao",
            "offer": "oferta",
            "hired": "contratado",
            "rejected": "reprovado",
            "withdrawn": "desistencia"
        }
        return stage_mapping.get(merge_stage.lower(), merge_stage)


merge_ats_service = MergeATSService()
