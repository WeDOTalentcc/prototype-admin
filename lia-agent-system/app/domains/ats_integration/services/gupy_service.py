"""
Gupy ATS Integration Service.
Handles candidate synchronization, job posting, and webhook processing.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GupyService:
    """
    Service for integrating with Gupy ATS platform.
    API Docs: https://developers.gupy.io/reference/introduction
    """
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.base_url = "https://api.gupy.io/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test API connection and authentication."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/jobs",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Gupy connection test failed: {e}")
            return False
    
    async def get_jobs(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict[str, Any]:
        """
        Get list of job postings from Gupy.
        
        Args:
            status: Filter by status (open, closed, draft)
            limit: Number of jobs to return
            offset: Pagination offset
            
        Returns:
            {"total": int, "jobs": [...]}
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/jobs",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"✅ Fetched {len(data.get('data', []))} jobs from Gupy")
                return {
                    "total": data.get("totalElements", 0),
                    "jobs": data.get("data", [])
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch Gupy jobs: {e}")
            return {"total": 0, "jobs": []}
    
    async def get_job_applications(
        self,
        job_id: str,
        status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get applications for a specific job.
        
        Args:
            job_id: Gupy job ID
            status: Filter by status (active, hired, rejected, etc)
            
        Returns:
            List of applications
        """
        try:
            params = {}
            if status:
                params["status"] = status
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/jobs/{job_id}/applications",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                applications = data.get("data", [])
                logger.info(f"✅ Fetched {len(applications)} applications for job {job_id}")
                return applications
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch applications for job {job_id}: {e}")
            return []
    
    async def get_candidate_details(self, candidate_id: str) -> dict[str, Any] | None:
        """
        Get detailed candidate information.
        
        Args:
            candidate_id: Gupy candidate ID
            
        Returns:
            Candidate data or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/candidates/{candidate_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                candidate = response.json()
                
                logger.info(f"✅ Fetched candidate {candidate_id} details")
                return candidate
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️ Candidate {candidate_id} not found")
            else:
                logger.error(f"❌ Failed to fetch candidate {candidate_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to fetch candidate {candidate_id}: {e}")
            return None
    
    async def create_webhook(
        self,
        event_type: str,
        postback_url: str,
        tech_owner_email: str,
        tech_owner_name: str,
        custom_headers: dict[str, str] | None = None
    ) -> dict[str, Any] | None:
        """
        Create a webhook for Gupy events.
        
        Args:
            event_type: Event to listen to (e.g., "application.created", "candidate.hired")
            postback_url: Your webhook endpoint URL
            tech_owner_email: Technical contact email
            tech_owner_name: Technical contact name
            custom_headers: Optional custom headers for webhook requests
            
        Returns:
            Webhook configuration or None if failed
        """
        payload = {
            "action": event_type,
            "status": "active",
            "techOwnerEmail": tech_owner_email,
            "techOwnerName": tech_owner_name,
            "postbackUrl": postback_url
        }
        
        if custom_headers:
            payload["clientHeaders"] = custom_headers
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/webhooks",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                webhook = response.json()
                
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"✅ Created Gupy webhook for {event_type}")
                return webhook
                
        except Exception as e:
            logger.error(f"❌ Failed to create Gupy webhook: {e}")
            return None
    
    async def list_webhooks(self) -> list[dict[str, Any]]:
        """Get all configured webhooks."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/webhooks?fields=all",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                webhooks = data.get("data", [])
                logger.info(f"✅ Fetched {len(webhooks)} Gupy webhooks")
                return webhooks
                
        except Exception as e:
            logger.error(f"❌ Failed to list Gupy webhooks: {e}")
            return []
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/webhooks/{webhook_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                logger.info(f"✅ Deleted Gupy webhook {webhook_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to delete Gupy webhook {webhook_id}: {e}")
            return False
    
    def process_webhook_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process and normalize webhook payload.
        
        Args:
            payload: Raw webhook payload from Gupy
            
        Returns:
            Normalized data structure
        """
        event_type = payload.get("event")
        data = payload.get("data", {})
        
        normalized = {
            "event_type": event_type,
            "event_id": payload.get("id"),
            "event_date": payload.get("date"),
            "company_name": payload.get("companyName"),
            "raw_payload": payload
        }
        
        # Extract candidate info if present
        if "candidate" in data:
            normalized["candidate"] = {
                "id": data["candidate"].get("id"),
                "name": data["candidate"].get("name")
            }
        
        # Extract job info if present
        if "job" in data:
            normalized["job"] = {
                "id": data["job"].get("id"),
                "name": data["job"].get("name"),
                "department_code": data["job"].get("departmentCode"),
                "role_code": data["job"].get("roleCode"),
                "branch_code": data["job"].get("branchCode")
            }
        
        # Extract application info if present
        if "application" in data:
            normalized["application"] = {
                "id": data["application"].get("id"),
                "score": data["application"].get("score"),
                "tags": data["application"].get("tags", []),
                "hiring_date": data["application"].get("hiringDate"),
                "current_step": data["application"].get("currentStep", {})
            }
        
        return normalized


# Global instance
gupy_service = None

def init_gupy_service(api_key: str) -> GupyService:
    """Initialize Gupy service with API key."""
    global gupy_service
    gupy_service = GupyService(api_key=api_key)
    return gupy_service
