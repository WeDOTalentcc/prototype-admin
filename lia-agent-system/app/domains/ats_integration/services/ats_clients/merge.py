"""
Merge.dev ATS Client

Implements the ATSClient interface for Merge.dev's Unified ATS API.
Merge provides a single API to integrate with 40+ ATS platforms including
Greenhouse, Lever, Workable, BambooHR, iCIMS, and more.
"""
import logging
from datetime import datetime
from typing import Any

import httpx

from app.shared.resilience.circuit_breaker import MERGE_CIRCUIT, circuit_breaker_decorator

from .base import ATSCandidate, ATSClient, ATSClientConfig, ATSJob, SyncResult

logger = logging.getLogger(__name__)


class MergeClient(ATSClient):
    """
    Merge.dev ATS Client implementation.
    
    Uses Merge's Unified API to sync with 40+ ATS platforms through a single interface.
    Requires both an API key and per-account X-Account-Token for requests.
    """
    
    def __init__(self, config: ATSClientConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.merge.dev/api/ats/v1"
        self._http_client: httpx.AsyncClient | None = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._http_client
    
    def _headers(self, account_token: str | None = None) -> dict[str, str]:
        """Get headers for Merge API requests."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        if account_token or self.config.company_id:
            headers["X-Account-Token"] = account_token or self.config.company_id or ""
        return headers
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def test_connection(self) -> bool:
        """Test connection to Merge API."""
        try:
            client = await self._get_http_client()
            response = await client.get(
                f"{self.base_url}/sync-status",
                headers=self._headers()
            )
            return response.status_code in [200, 401]
        except Exception as e:
            logger.error(f"[MERGE] Connection test failed: {e}")
            return False
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def get_candidate(self, ats_candidate_id: str) -> ATSCandidate | None:
        """Get candidate from Merge."""
        try:
            client = await self._get_http_client()
            response = await client.get(
                f"{self.base_url}/candidates/{ats_candidate_id}",
                headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_candidate(data)
        except Exception as e:
            logger.error(f"[MERGE] Failed to get candidate {ats_candidate_id}: {e}")
            return None
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def get_candidates(
        self,
        job_id: str | None = None,
        stage: str | None = None,
        modified_after: datetime | None = None,
        limit: int = 100
    ) -> list[ATSCandidate]:
        """Get candidates from Merge with optional filters."""
        try:
            client = await self._get_http_client()
            params: dict[str, Any] = {"page_size": limit}
            
            if modified_after:
                params["modified_after"] = modified_after.isoformat()
            
            response = await client.get(
                f"{self.base_url}/candidates",
                headers=self._headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            candidates = []
            for item in data.get("results", []):
                candidate = self._parse_candidate(item)
                if candidate:
                    candidates.append(candidate)
            
            return candidates
        except Exception as e:
            logger.error(f"[MERGE] Failed to get candidates: {e}")
            return []
    
    def _parse_candidate(self, data: dict[str, Any]) -> ATSCandidate | None:
        """Parse Merge candidate response to ATSCandidate."""
        try:
            emails = data.get("email_addresses", [])
            email = emails[0].get("value", "") if emails else ""
            
            phones = data.get("phone_numbers", [])
            phone = phones[0].get("value", "") if phones else None
            
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            name = f"{first_name} {last_name}".strip()
            
            attachments = data.get("attachments", [])
            cv_url = None
            for att in attachments:
                if att.get("attachment_type") == "RESUME":
                    cv_url = att.get("file_url")
                    break
            
            urls = data.get("urls", [])
            linkedin_url = None
            for url in urls:
                if "linkedin" in url.get("value", "").lower():
                    linkedin_url = url.get("value")
                    break
            
            locations = data.get("locations", [])
            location = locations[0] if locations else None
            
            return ATSCandidate(
                ats_id=data.get("id", ""),
                name=name,
                email=email,
                phone=phone,
                cv_url=cv_url,
                linkedin_url=linkedin_url,
                location=location,
                custom_fields=data.get("custom_fields"),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else None,
                updated_at=datetime.fromisoformat(data["modified_at"].replace("Z", "+00:00")) if data.get("modified_at") else None,
                raw_data=data
            )
        except Exception as e:
            logger.error(f"[MERGE] Failed to parse candidate: {e}")
            return None
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def create_candidate(self, candidate_data: dict[str, Any]) -> SyncResult:
        """Create candidate in Merge/linked ATS."""
        try:
            client = await self._get_http_client()
            
            emails = []
            if candidate_data.get("email"):
                emails.append({
                    "value": candidate_data["email"],
                    "email_address_type": "PERSONAL"
                })
            
            phones = []
            if candidate_data.get("phone"):
                phones.append({
                    "value": candidate_data["phone"],
                    "phone_number_type": "MOBILE"
                })
            
            name_parts = candidate_data.get("name", "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            payload = {
                "model": {
                    "first_name": candidate_data.get("first_name", first_name),
                    "last_name": candidate_data.get("last_name", last_name),
                    "email_addresses": emails,
                    "phone_numbers": phones,
                    "company": candidate_data.get("company"),
                    "title": candidate_data.get("title")
                }
            }
            
            response = await client.post(
                f"{self.base_url}/candidates",
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return SyncResult(
                success=True,
                action="created",
                ats_id=data.get("model", {}).get("id"),
                wedotalent_id=candidate_data.get("wedotalent_id"),
                changes=["created"]
            )
        except Exception as e:
            logger.error(f"[MERGE] Failed to create candidate: {e}")
            return SyncResult(
                success=False,
                action="create",
                error=str(e)
            )
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def update_candidate(
        self,
        ats_candidate_id: str,
        updates: dict[str, Any]
    ) -> SyncResult:
        """Update candidate in Merge/linked ATS."""
        try:
            client = await self._get_http_client()
            
            payload = {"model": updates}
            
            response = await client.patch(
                f"{self.base_url}/candidates/{ats_candidate_id}",
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            
            return SyncResult(
                success=True,
                action="updated",
                ats_id=ats_candidate_id,
                changes=list(updates.keys())
            )
        except Exception as e:
            logger.error(f"[MERGE] Failed to update candidate {ats_candidate_id}: {e}")
            return SyncResult(
                success=False,
                action="update",
                ats_id=ats_candidate_id,
                error=str(e)
            )
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def update_candidate_stage(
        self,
        ats_candidate_id: str,
        application_id: str,
        new_stage: str,
        stage_id: str | None = None
    ) -> SyncResult:
        """Update candidate's application stage."""
        try:
            client = await self._get_http_client()
            
            payload = {
                "model": {
                    "current_stage": stage_id or new_stage
                }
            }
            
            response = await client.patch(
                f"{self.base_url}/applications/{application_id}",
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            
            return SyncResult(
                success=True,
                action="stage_updated",
                ats_id=application_id,
                changes=[f"stage -> {new_stage}"]
            )
        except Exception as e:
            logger.error(f"[MERGE] Failed to update stage for application {application_id}: {e}")
            return SyncResult(
                success=False,
                action="stage_update",
                ats_id=application_id,
                error=str(e)
            )
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def add_note(
        self,
        ats_candidate_id: str,
        note_content: str,
        note_type: str = "general"
    ) -> SyncResult:
        """Add note to candidate."""
        try:
            client = await self._get_http_client()
            
            payload = {
                "model": {
                    "candidate": ats_candidate_id,
                    "body": note_content
                }
            }
            
            response = await client.post(
                f"{self.base_url}/notes",
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return SyncResult(
                success=True,
                action="note_added",
                ats_id=data.get("model", {}).get("id"),
                changes=["note"]
            )
        except Exception as e:
            logger.error(f"[MERGE] Failed to add note for candidate {ats_candidate_id}: {e}")
            return SyncResult(
                success=False,
                action="add_note",
                error=str(e)
            )
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def get_job(self, ats_job_id: str) -> ATSJob | None:
        """Get job from Merge."""
        try:
            client = await self._get_http_client()
            response = await client.get(
                f"{self.base_url}/jobs/{ats_job_id}",
                headers=self._headers()
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_job(data)
        except Exception as e:
            logger.error(f"[MERGE] Failed to get job {ats_job_id}: {e}")
            return None
    
    @circuit_breaker_decorator(MERGE_CIRCUIT)
    async def list_jobs(
        self,
        page: int = 1,
        size: int = 100,
        status: str | None = None,
    ) -> list[dict]:
        """Phase G.1 — list jobs in the (page, size) signature the
        BulkImportModal ATS tab expects.

        Wraps the existing get_jobs() call, then unwraps each ATSJob into
        a plain dict shaped for the /ats/connections/{id}/jobs endpoint
        normalizer in app/api/v1/ats.py. Page is implemented via
        offset (Merge supports cursor pagination internally; for the
        UI's modest needs page * size offsetting is fine).

        Returns plain dicts (not ATSJob) so the endpoint's normalizer
        can read with .get() — Merge_id maps to id, name maps to title,
        etc. (see _parse_job for the full mapping).
        """
        # Merge supports limit but not page directly. For simplicity we
        # request page * size and slice client-side; Merge instances this
        # endpoint hits typically have <500 jobs so this is acceptable.
        effective_limit = min(page * size, 500)
        jobs = await self.get_jobs(status=status, limit=effective_limit)
        start = (page - 1) * size
        end = start + size
        sliced = jobs[start:end]
        # Convert ATSJob -> plain dict shape the endpoint normalizer
        # expects.
        return [
            {
                "id": j.ats_id,
                "title": j.title,
                "department": j.department,
                "location": j.location,
                "status": j.status,
                "posted_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in sliced
        ]

    async def get_jobs(
        self,
        status: str | None = None,
        modified_after: datetime | None = None,
        limit: int = 100
    ) -> list[ATSJob]:
        """Get jobs from Merge."""
        try:
            client = await self._get_http_client()
            params: dict[str, Any] = {"page_size": limit}
            
            if status:
                params["status"] = status
            if modified_after:
                params["modified_after"] = modified_after.isoformat()
            
            response = await client.get(
                f"{self.base_url}/jobs",
                headers=self._headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for item in data.get("results", []):
                job = self._parse_job(item)
                if job:
                    jobs.append(job)
            
            return jobs
        except Exception as e:
            logger.error(f"[MERGE] Failed to get jobs: {e}")
            return []
    
    def _parse_job(self, data: dict[str, Any]) -> ATSJob | None:
        """Parse Merge job response to ATSJob."""
        try:
            departments = data.get("departments", [])
            department = departments[0].get("name") if departments else None
            
            offices = data.get("offices", [])
            location = offices[0].get("location") if offices else None
            
            return ATSJob(
                ats_id=data.get("id", ""),
                title=data.get("name", ""),
                description=data.get("description"),
                department=department,
                location=location,
                status=data.get("status"),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else None,
                updated_at=datetime.fromisoformat(data["modified_at"].replace("Z", "+00:00")) if data.get("modified_at") else None,
                raw_data=data
            )
        except Exception as e:
            logger.error(f"[MERGE] Failed to parse job: {e}")
            return None
    
    async def get_stages(self, job_id: str | None = None) -> list[dict[str, Any]]:
        """Get interview stages from Merge."""
        try:
            client = await self._get_http_client()
            params = {}
            if job_id:
                params["job_id"] = job_id
            
            response = await client.get(
                f"{self.base_url}/job-interview-stages",
                headers=self._headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("results", [])
        except Exception as e:
            logger.error(f"[MERGE] Failed to get stages: {e}")
            return []
    
    def get_stage_mapping(self) -> dict[str, str]:
        """Get mapping between LIA stages and Merge/ATS stages."""
        return {
            "triagem": "Application Review",
            "screening": "Phone Screen",
            "entrevista": "Interview",
            "avaliacao": "Assessment",
            "oferta": "Offer",
            "contratado": "Hired",
            "reprovado": "Rejected",
            "desistencia": "Withdrawn"
        }
    
    def get_reverse_stage_mapping(self) -> dict[str, str]:
        """Get mapping from Merge/ATS stages to LIA stages."""
        return {v.lower(): k for k, v in self.get_stage_mapping().items()}
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
