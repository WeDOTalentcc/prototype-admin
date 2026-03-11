"""
StackOne Unified ATS Client Implementation

StackOne provides a unified API to connect to multiple ATS platforms.
This allows connecting to any ATS supported by StackOne through a single integration.
API Docs: https://docs.stackone.com/
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from .base import ATSClient, ATSClientConfig, ATSCandidate, ATSJob

logger = logging.getLogger(__name__)


class StackOneClient(ATSClient):
    """
    StackOne Unified ATS API Client.
    
    StackOne provides a single unified API to connect to 40+ ATS platforms.
    This allows WedoTalent to support any StackOne-connected ATS through
    a single integration point.
    
    Supported ATSs via StackOne include:
    - Greenhouse, Lever, Workday, SAP SuccessFactors
    - Jobvite, iCIMS, Bullhorn, Recruitee
    - And many more...
    """
    
    DEFAULT_BASE_URL = "https://api.stackone.com/unified"
    
    @property
    def name(self) -> str:
        return "stackone"
    
    def _validate_config(self) -> None:
        if not self.config.api_key:
            raise ValueError("StackOne API key is required")
        if not self.config.base_url:
            self.config.base_url = self.DEFAULT_BASE_URL
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.config.company_id:
            headers["x-account-id"] = self.config.company_id
        return headers
    
    async def test_connection(self) -> bool:
        """Test StackOne API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/ats/jobs",
                    headers=self._get_headers(),
                    params={"page_size": 1},
                    timeout=self.config.timeout
                )
                return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"StackOne connection test failed: {e}")
            return False
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Safely parse datetime from various formats."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            if "T" in str(value):
                return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return datetime.strptime(str(value), "%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    
    def _extract_nested(self, data: Dict[str, Any], path: str) -> Any:
        """Extract value from nested dictionary using dot notation."""
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
    
    def _parse_candidate(self, data: Dict[str, Any]) -> ATSCandidate:
        """Parse StackOne candidate response to normalized format."""
        name_parts = []
        if data.get("first_name"):
            name_parts.append(data["first_name"])
        if data.get("last_name"):
            name_parts.append(data["last_name"])
        name = " ".join(name_parts) if name_parts else data.get("name", "")
        
        emails = data.get("emails", [])
        primary_email = ""
        if emails and isinstance(emails, list):
            for e in emails:
                if isinstance(e, dict) and e.get("type") == "primary":
                    primary_email = e.get("value", "")
                    break
            if not primary_email and emails:
                first_email = emails[0]
                primary_email = first_email.get("value", "") if isinstance(first_email, dict) else str(first_email)
        elif isinstance(emails, str):
            primary_email = emails
        
        phones = data.get("phone_numbers", [])
        primary_phone = None
        if phones and isinstance(phones, list):
            for p in phones:
                if isinstance(p, dict) and p.get("type") == "mobile":
                    primary_phone = p.get("value")
                    break
            if not primary_phone and phones:
                first_phone = phones[0]
                primary_phone = first_phone.get("value") if isinstance(first_phone, dict) else str(first_phone)
        
        social_links = data.get("social_links", {})
        linkedin_url = None
        if isinstance(social_links, dict):
            linkedin_url = social_links.get("linkedin")
        elif isinstance(social_links, list):
            for link in social_links:
                if isinstance(link, dict) and "linkedin" in link.get("type", "").lower():
                    linkedin_url = link.get("url")
                    break
        
        custom_fields = data.get("custom_fields", {})
        wsi_score = self._extract_nested(custom_fields, "wsi_score") if isinstance(custom_fields, dict) else None
        
        return ATSCandidate(
            ats_id=str(data.get("id", "")),
            name=name,
            email=primary_email,
            phone=primary_phone,
            status=data.get("stage") or data.get("status"),
            stage=data.get("stage"),
            cv_url=data.get("resume_url") or data.get("resume", {}).get("url"),
            linkedin_url=linkedin_url,
            location=data.get("location", {}).get("city") if isinstance(data.get("location"), dict) else data.get("location"),
            notes=data.get("notes"),
            custom_fields=custom_fields if isinstance(custom_fields, dict) else None,
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            raw_data=data
        )
    
    async def get_candidate(self, candidate_id: str) -> Optional[ATSCandidate]:
        """Get candidate from StackOne."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/ats/candidates/{candidate_id}",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
                if response.status_code == 404:
                    logger.warning(f"Candidate {candidate_id} not found in StackOne")
                    return None
                response.raise_for_status()
                data = response.json()
                candidate_data = data.get("data", data)
                return self._parse_candidate(candidate_data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Failed to get StackOne candidate {candidate_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get StackOne candidate {candidate_id}: {e}")
            raise
    
    async def list_candidates(
        self,
        job_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ATSCandidate]:
        """List candidates from StackOne."""
        params: Dict[str, Any] = {
            "page_size": limit,
            "page": offset // limit + 1 if limit > 0 else 1
        }
        if job_id:
            params["job_id"] = job_id
        if status:
            params["stage"] = status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/ats/candidates",
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                data = response.json()
                candidates_data = data.get("data", []) if isinstance(data, dict) else data
                logger.info(f"✅ Fetched {len(candidates_data)} candidates from StackOne")
                return [self._parse_candidate(c) for c in candidates_data]
        except Exception as e:
            logger.error(f"Failed to list StackOne candidates: {e}")
            raise
    
    async def create_candidate(self, data: Dict[str, Any]) -> ATSCandidate:
        """Create candidate in StackOne."""
        emails = []
        if data.get("email"):
            emails.append({"type": "primary", "value": data["email"]})
        
        phone_numbers = []
        if data.get("phone"):
            phone_numbers.append({"type": "mobile", "value": data["phone"]})
        
        social_links = {}
        if data.get("linkedin_url"):
            social_links["linkedin"] = data["linkedin_url"]
        
        name_parts = data.get("name", "").split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        stackone_data: Dict[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "emails": emails,
            "phone_numbers": phone_numbers,
        }
        
        if social_links:
            stackone_data["social_links"] = social_links
        
        if data.get("location"):
            stackone_data["location"] = {"city": data["location"]}
        
        if data.get("job_id"):
            stackone_data["job_id"] = data["job_id"]
        
        custom_fields = {}
        if data.get("wsi_score") is not None:
            custom_fields["wsi_score"] = data["wsi_score"]
        if custom_fields:
            stackone_data["custom_fields"] = custom_fields
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/ats/candidates",
                    headers=self._get_headers(),
                    json=stackone_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                resp_data = response.json()
                result = self._parse_candidate(resp_data.get("data", resp_data))
                logger.info(f"✅ Created candidate {result.ats_id} in StackOne")
                return result
        except Exception as e:
            logger.error(f"Failed to create StackOne candidate: {e}")
            raise
    
    async def update_candidate(
        self,
        candidate_id: str,
        data: Dict[str, Any]
    ) -> ATSCandidate:
        """Update candidate in StackOne."""
        stackone_data: Dict[str, Any] = {}
        
        if "status" in data or "stage" in data:
            stackone_data["stage"] = data.get("status") or data.get("stage")
        
        if "notes" in data:
            stackone_data["notes"] = data["notes"]
        
        custom_fields = {}
        if "wsi_score" in data:
            custom_fields["wsi_score"] = data["wsi_score"]
        if "rejection_reason" in data:
            custom_fields["rejection_reason"] = data["rejection_reason"]
        if custom_fields:
            stackone_data["custom_fields"] = custom_fields
        
        if "phone" in data:
            stackone_data["phone_numbers"] = [{"type": "mobile", "value": data["phone"]}]
        
        if "linkedin_url" in data:
            stackone_data["social_links"] = {"linkedin": data["linkedin_url"]}
        
        if not stackone_data:
            current = await self.get_candidate(candidate_id)
            if current:
                return current
            raise ValueError(f"Candidate {candidate_id} not found and no data to update")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.config.base_url}/ats/candidates/{candidate_id}",
                    headers=self._get_headers(),
                    json=stackone_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                resp_data = response.json()
                result = self._parse_candidate(resp_data.get("data", resp_data))
                logger.info(f"✅ Updated candidate {candidate_id} in StackOne: {list(stackone_data.keys())}")
                return result
        except Exception as e:
            logger.error(f"Failed to update StackOne candidate {candidate_id}: {e}")
            raise
    
    async def update_candidate_status(
        self,
        candidate_id: str,
        new_status: str,
        reason: Optional[str] = None
    ) -> bool:
        """Update candidate status in StackOne."""
        data: Dict[str, Any] = {"stage": new_status}
        if reason:
            data["rejection_reason"] = reason
        
        try:
            await self.update_candidate(candidate_id, data)
            logger.info(f"✅ Updated status of candidate {candidate_id} to {new_status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update StackOne candidate status: {e}")
            return False
    
    async def add_note(
        self,
        candidate_id: str,
        note: str,
        author: Optional[str] = None
    ) -> bool:
        """Add note to candidate in StackOne."""
        note_data = {
            "content": note,
            "author": author or "LIA System",
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.base_url}/ats/candidates/{candidate_id}/notes",
                    headers=self._get_headers(),
                    json=note_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                logger.info(f"✅ Added note to candidate {candidate_id} in StackOne")
                return True
        except Exception as e:
            logger.error(f"Failed to add note to StackOne candidate {candidate_id}: {e}")
            return False
    
    def _parse_job(self, data: Dict[str, Any]) -> ATSJob:
        """Parse StackOne job response."""
        location = data.get("location", {})
        location_str = None
        if isinstance(location, dict):
            location_parts = []
            if location.get("city"):
                location_parts.append(location["city"])
            if location.get("state"):
                location_parts.append(location["state"])
            if location.get("country"):
                location_parts.append(location["country"])
            location_str = ", ".join(location_parts) if location_parts else None
        elif isinstance(location, str):
            location_str = location
        
        compensation = data.get("compensation", {})
        salary_range = None
        if isinstance(compensation, dict):
            min_sal = compensation.get("min")
            max_sal = compensation.get("max")
            currency = compensation.get("currency", "BRL")
            if min_sal and max_sal:
                salary_range = f"{currency} {min_sal} - {max_sal}"
            elif min_sal:
                salary_range = f"{currency} {min_sal}+"
        
        return ATSJob(
            ats_id=str(data.get("id", "")),
            title=data.get("title") or data.get("name") or "",
            description=data.get("description"),
            department=data.get("department", {}).get("name") if isinstance(data.get("department"), dict) else data.get("department"),
            location=location_str,
            status=data.get("status"),
            requirements=data.get("requirements"),
            employment_type=data.get("employment_type"),
            salary_range=salary_range,
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
            raw_data=data
        )
    
    async def get_job(self, job_id: str) -> Optional[ATSJob]:
        """Get job from StackOne."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/ats/jobs/{job_id}",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                return self._parse_job(data.get("data", data))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Failed to get StackOne job {job_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get StackOne job {job_id}: {e}")
            raise
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ATSJob]:
        """List jobs from StackOne."""
        params: Dict[str, Any] = {"page_size": limit}
        if status:
            params["status"] = status
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/ats/jobs",
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                data = response.json()
                jobs_data = data.get("data", []) if isinstance(data, dict) else data
                logger.info(f"✅ Fetched {len(jobs_data)} jobs from StackOne")
                return [self._parse_job(j) for j in jobs_data]
        except Exception as e:
            logger.error(f"Failed to list StackOne jobs: {e}")
            raise
