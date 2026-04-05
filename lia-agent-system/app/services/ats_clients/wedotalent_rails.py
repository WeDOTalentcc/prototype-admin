"""
WeDOTalent Rails ATS Client — HTTP client to call ats_api (Rails) endpoints.

Based on contracts read from WeDOTalent/ats_api GitHub:
- Base URL: configurable via RAILS_API_URL env var
- Auth: Bearer JWT (Rails-issued or service token)
- Format: JSONAPI (jsonapi-serializer gem)
- Search: Searchkick via ?search=term&page=1&limit=30
- Tenant: Apartment gem (schema-based) — tenant set server-side via user's account

Endpoints:
  POST   /v1/sessions          — Login (email + password → JWT)
  GET    /v1/me                — Current user info
  GET    /v1/users/jobs        — List/search jobs
  GET    /v1/users/jobs/:id    — Get job
  GET    /v1/users/candidates  — List/search candidates
  GET    /v1/users/candidates/:id — Get candidate
  GET    /v1/users/applies     — List/search applies
  GET    /v1/users/applies/:id — Get apply
  GET    /v1/users/selective_processes — List processes
  POST   /v1/users/applies     — Create apply
  PUT    /v1/users/applies/:id — Update apply
"""
import logging
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import httpx

from app.services.ats_clients.base import (
    ATSClientConfig,
    ATSCandidate,
    ATSJob,
)

logger = logging.getLogger(__name__)

RAILS_API_URL = os.environ.get("RAILS_API_URL", "http://localhost:8080")
RAILS_API_TIMEOUT = int(os.environ.get("RAILS_API_TIMEOUT", "30"))


@dataclass
class RailsAPIResponse:
    """Parsed JSONAPI response from Rails."""
    data: Any = None
    meta: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    status_code: int = 0
    success: bool = False


class WeDOTalentATSClient:
    """HTTP client for WeDOTalent ats_api (Rails).

    Implements retry with exponential backoff, auto-refresh on 401,
    and JSONAPI response parsing.

    Usage:
        client = WeDOTalentATSClient(token="eyJ...")
        jobs = await client.list_jobs(search="developer", page=1, limit=20)
        candidate = await client.get_candidate(candidate_id=5)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = RAILS_API_TIMEOUT,
    ):
        self.base_url = (base_url or RAILS_API_URL).rstrip("/")
        self.token = token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json_body: Optional[Dict] = None,
        retry: int = 3,
    ) -> RailsAPIResponse:
        """Make HTTP request with retry and JSONAPI parsing."""
        client = await self._get_client()
        last_error = None

        for attempt in range(retry):
            try:
                response = await client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json_body,
                )

                result = RailsAPIResponse(status_code=response.status_code)

                if response.status_code == 401:
                    logger.warning("[RailsClient] 401 Unauthorized on %s %s", method, path)
                    result.errors = ["Unauthorized"]
                    return result

                if response.status_code >= 400:
                    body = response.json() if response.content else {}
                    result.errors = body.get("errors", [str(response.status_code)])
                    return result

                body = response.json() if response.content else {}
                result.data = body.get("data")
                result.meta = body.get("meta", {})
                result.success = True
                return result

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "[RailsClient] Timeout on %s %s (attempt %d/%d)",
                    method, path, attempt + 1, retry,
                )
            except Exception as e:
                last_error = e
                logger.error(
                    "[RailsClient] Error on %s %s: %s (attempt %d/%d)",
                    method, path, e, attempt + 1, retry,
                )

        return RailsAPIResponse(
            errors=[f"All {retry} attempts failed: {last_error}"],
            status_code=0,
        )

    async def get(self, path: str, params: Optional[Dict] = None) -> RailsAPIResponse:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json_body: Optional[Dict] = None) -> RailsAPIResponse:
        return await self._request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body: Optional[Dict] = None) -> RailsAPIResponse:
        return await self._request("PUT", path, json_body=json_body)

    async def delete(self, path: str) -> RailsAPIResponse:
        return await self._request("DELETE", path)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def login(self, email: str, password: str) -> Optional[str]:
        """Authenticate and get JWT token from Rails."""
        resp = await self.post("/v1/sessions", json_body={
            "email": email,
            "password": password,
        })
        if resp.success and isinstance(resp.data, dict):
            token = resp.data.get("token")
            if token:
                self.token = token
                # Refresh client headers
                self._client = None
                return token
        return None

    async def get_current_user(self) -> Optional[Dict]:
        """Get authenticated user info (/v1/me)."""
        resp = await self.get("/v1/me")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    async def list_jobs(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> List[Dict]:
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/jobs", params=params)
        return self._extract_list(resp)

    async def get_job(self, job_id: int) -> Optional[Dict]:
        resp = await self.get(f"/v1/users/jobs/{job_id}")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Candidates
    # ------------------------------------------------------------------

    async def list_candidates(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> List[Dict]:
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/candidates", params=params)
        return self._extract_list(resp)

    async def get_candidate(self, candidate_id: int) -> Optional[Dict]:
        resp = await self.get(f"/v1/users/candidates/{candidate_id}")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Applies (Applications)
    # ------------------------------------------------------------------

    async def list_applies(
        self, search: str = "*", page: int = 1, limit: int = 30, **filters
    ) -> List[Dict]:
        params = {"search": search, "page": page, "limit": limit}
        if filters:
            import json
            params["where"] = json.dumps(filters)
        resp = await self.get("/v1/users/applies", params=params)
        return self._extract_list(resp)

    async def get_apply(self, apply_id: int) -> Optional[Dict]:
        resp = await self.get(f"/v1/users/applies/{apply_id}")
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    async def create_apply(self, candidate_id: int, job_id: int) -> Optional[Dict]:
        resp = await self.post("/v1/users/applies", json_body={
            "candidate_id": candidate_id,
            "job_id": job_id,
        })
        if resp.success:
            return self._extract_attributes(resp.data)
        return None

    # ------------------------------------------------------------------
    # Selective Processes
    # ------------------------------------------------------------------

    async def list_selective_processes(
        self, job_id: Optional[int] = None, **filters
    ) -> List[Dict]:
        params: Dict[str, Any] = {"search": "*"}
        if job_id:
            import json
            params["where"] = json.dumps({"job_id": job_id})
        resp = await self.get("/v1/users/selective_processes", params=params)
        return self._extract_list(resp)

    # ------------------------------------------------------------------
    # JSONAPI Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_attributes(data: Any) -> Optional[Dict]:
        """Extract attributes from JSONAPI data object."""
        if isinstance(data, dict):
            attrs = data.get("attributes", {})
            attrs["id"] = data.get("id")
            attrs["type"] = data.get("type")
            return attrs
        return None

    @staticmethod
    def _extract_list(resp: RailsAPIResponse) -> List[Dict]:
        """Extract list of attributes from JSONAPI data array."""
        if not resp.success or not isinstance(resp.data, list):
            return []
        results = []
        for item in resp.data:
            if isinstance(item, dict):
                attrs = item.get("attributes", {})
                attrs["id"] = item.get("id")
                attrs["type"] = item.get("type")
                results.append(attrs)
        return results

    def to_ats_candidate(self, data: Dict) -> ATSCandidate:
        """Convert Rails candidate data to normalized ATSCandidate."""
        return ATSCandidate(
            ats_id=str(data.get("id", "")),
            name=f"{data.get('name', '')} {data.get('surname', '')}".strip(),
            email=data.get("email", ""),
            phone=data.get("mobile_phone") or data.get("phone"),
            linkedin_url=data.get("linkedin"),
            location=f"{data.get('city', '')}, {data.get('state', '')}".strip(", "),
            notes=data.get("comments"),
            raw_data=data,
        )

    def to_ats_job(self, data: Dict) -> ATSJob:
        """Convert Rails job data to normalized ATSJob."""
        return ATSJob(
            ats_id=str(data.get("id", "")),
            title=data.get("title", ""),
            description=data.get("description"),
            location=f"{data.get('city', '')}, {data.get('state', '')}".strip(", "),
            status="remote" if data.get("is_remote") else data.get("workplace_type", ""),
            raw_data=data,
        )
