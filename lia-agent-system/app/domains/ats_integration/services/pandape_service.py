"""
Pandapé ATS Integration Service.
Handles candidate synchronization and job posting for Pandapé platform.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PandapeService:
    """
    Service for integrating with Pandapé ATS platform.
    API Docs: https://api-ats.pandape.com/index.html
    """
    
    def __init__(self, api_key: str | None = None, api_url: str | None = None):
        self.api_key = api_key
        self.base_url = api_url or "https://api-ats.pandape.com/api/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test API connection and authentication."""
        try:
            async with httpx.AsyncClient() as client:
                # Test endpoint - adjust based on actual Pandapé API
                response = await client.get(
                    f"{self.base_url}/jobs",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Pandapé connection test failed: {e}")
            return False
    
    async def get_jobs(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict[str, Any]:
        """
        Get list of job postings from Pandapé.
        
        Args:
            status: Filter by status (active, closed, etc)
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
                
                jobs = data.get("data", data) if isinstance(data, dict) else data
                logger.info(f"✅ Fetched {len(jobs)} jobs from Pandapé")
                return {
                    "total": len(jobs),
                    "jobs": jobs
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch Pandapé jobs: {e}")
            return {"total": 0, "jobs": []}
    
    async def get_candidates(
        self,
        job_id: str | None = None,
        status: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get candidates from Pandapé.
        
        Args:
            job_id: Filter by specific job (optional)
            status: Filter by candidate status (optional)
            limit: Maximum number of candidates
            
        Returns:
            List of candidates
        """
        params = {"limit": limit}
        if job_id:
            params["jobId"] = job_id
        if status:
            params["status"] = status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/candidates",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                candidates = data.get("data", data) if isinstance(data, dict) else data
                logger.info(f"✅ Fetched {len(candidates)} candidates from Pandapé")
                return candidates
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch Pandapé candidates: {e}")
            return []
    
    async def get_candidate_details(self, candidate_id: str) -> dict[str, Any] | None:
        """
        Get detailed candidate information.
        
        Args:
            candidate_id: Pandapé candidate ID
            
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
                
                logger.info(f"✅ Fetched candidate {candidate_id} details from Pandapé")
                return candidate
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️ Candidate {candidate_id} not found in Pandapé")
            else:
                logger.error(f"❌ Failed to fetch Pandapé candidate {candidate_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to fetch Pandapé candidate {candidate_id}: {e}")
            return None
    
    async def get_applications(
        self,
        job_id: str | None = None,
        candidate_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get applications/candidacies.
        
        Args:
            job_id: Filter by job (optional)
            candidate_id: Filter by candidate (optional)
            
        Returns:
            List of applications
        """
        params = {}
        if job_id:
            params["jobId"] = job_id
        if candidate_id:
            params["candidateId"] = candidate_id
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/applications",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                applications = data.get("data", data) if isinstance(data, dict) else data
                logger.info(f"✅ Fetched {len(applications)} applications from Pandapé")
                return applications
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch Pandapé applications: {e}")
            return []
    
    def normalize_candidate(self, raw_candidate: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize Pandapé candidate data to LIA standard format.
        
        Args:
            raw_candidate: Raw candidate data from Pandapé API
            
        Returns:
            Normalized candidate data
        """
        # This is a generic mapping - adjust based on actual Pandapé schema
        return {
            "ats_candidate_id": raw_candidate.get("id"),
            "name": raw_candidate.get("name") or raw_candidate.get("fullName"),
            "email": raw_candidate.get("email"),
            "phone": raw_candidate.get("phone") or raw_candidate.get("phoneNumber"),
            "linkedin_url": raw_candidate.get("linkedinUrl") or raw_candidate.get("linkedin"),
            "current_title": raw_candidate.get("currentPosition") or raw_candidate.get("title"),
            "current_company": raw_candidate.get("currentCompany") or raw_candidate.get("company"),
            "location": raw_candidate.get("location") or raw_candidate.get("city"),
            "application_status": raw_candidate.get("status"),
            "applied_job_id": raw_candidate.get("jobId"),
            "applied_job_title": raw_candidate.get("jobTitle"),
            "application_date": raw_candidate.get("applicationDate") or raw_candidate.get("createdAt"),
            "ats_score": raw_candidate.get("score") or raw_candidate.get("rating"),
            "ats_tags": raw_candidate.get("tags", []),
            "ats_raw_data": raw_candidate
        }
    
    def normalize_job(self, raw_job: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize Pandapé job data to LIA standard format.
        
        Args:
            raw_job: Raw job data from Pandapé API
            
        Returns:
            Normalized job data
        """
        return {
            "ats_job_id": raw_job.get("id"),
            "job_title": raw_job.get("title") or raw_job.get("name"),
            "department": raw_job.get("department") or raw_job.get("area"),
            "location": raw_job.get("location") or raw_job.get("city"),
            "employment_type": raw_job.get("employmentType") or raw_job.get("type"),
            "ats_status": raw_job.get("status"),
            "description": raw_job.get("description"),
            "requirements": raw_job.get("requirements"),
            "ats_raw_data": raw_job
        }


# Global instance
pandape_service = None

def init_pandape_service(api_key: str, api_url: str | None = None) -> PandapeService:
    """Initialize Pandapé service with API key."""
    global pandape_service
    pandape_service = PandapeService(api_key=api_key, api_url=api_url)
    return pandape_service
