"""
JobCreationAPIClient — Rails API client for job creation wizard.

Handles: create job, update job, publish, unpublish, get screening config,
get calibration candidates, submit calibration feedback.

Follows same pattern as JobsAPIClient (httpx, OTT auth, context tracking).
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

import httpx

from app.core.config import settings  # LIA-D01: Fix import path (was app.config.settings)
from app.services.ott_service import get_ott_service

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    success: bool
    data: Any = None
    meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class JobCreationAPIClient:

    def __init__(self, context=None):
        self.settings = settings  # LIA-D01: settings is a singleton, not a function
        self.base_url = self.settings.ats_api.base_url
        self.timeout = self.settings.rails_api.timeout
        self._ott_service = get_ott_service()
        self._context = context

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._context and self._context.auth_token:
            headers["Authorization"] = f"Bearer {self._context.auth_token}"
        else:
            headers.update(self._ott_service.get_auth_header())
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        url = f"{self.base_url}{path}"
        start = time.time()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method, url,
                    headers=self._get_headers(),
                    params=params,
                    json=json_body,
                )

                if response.status_code == 401:
                    self._ott_service.invalidate()
                    response = client.request(
                        method, url,
                        headers=self._get_headers(),
                        params=params,
                        json=json_body,
                    )

                duration = (time.time() - start) * 1000

                if response.status_code >= 400:
                    error_body = response.text[:500] if response.text else "No body"
                    logger.error("[JobCreationAPI] HTTP %d %s %s: %s", response.status_code, method, path, error_body)
                    return APIResponse(success=False, error=f"HTTP {response.status_code}: {error_body[:200]}")

                data = response.json()
                logger.info("[JobCreationAPI] %s %s completed in %.0fms", method, path, duration)

                if self._context:
                    self._context.track_api_call(
                        endpoint=path, method=method, path=path,
                        params=params or json_body or {},
                        duration_ms=duration, status_code=response.status_code,
                    )

                return APIResponse(success=True, data=data)

        except httpx.TimeoutException:
            logger.error("[JobCreationAPI] Timeout %s %s", method, path)
            return APIResponse(success=False, error="Request timeout")
        except Exception as e:
            logger.error("[JobCreationAPI] Error %s %s: %s", method, path, e)
            return APIResponse(success=False, error=str(e))

    # -------------------------------------------------------------------
    # Job CRUD
    # -------------------------------------------------------------------

    def create_job(self, job_data: Dict[str, Any]) -> APIResponse:
        """Create a new job via Rails API.

        Args:
            job_data: Dict with title, description, department, seniority,
                     location, salary_range, benefits, etc.
        """
        return self._request("POST", "/api/v1/jobs", json_body={"job": job_data})

    def update_job(self, job_id: int, updates: Dict[str, Any]) -> APIResponse:
        """Update an existing job."""
        return self._request("PATCH", f"/api/v1/jobs/{job_id}", json_body={"job": updates})

    def get_job(self, job_id: int) -> APIResponse:
        """Get job details."""
        return self._request("GET", f"/api/v1/jobs/{job_id}")

    # -------------------------------------------------------------------
    # Publishing
    # -------------------------------------------------------------------

    def publish_job(self, job_id: int, platforms: List[str], sourcing_mode: str = "local") -> APIResponse:
        """Publish job to specified platforms."""
        return self._request("POST", f"/api/v1/jobs/{job_id}/publish", json_body={
            "platforms": platforms,
            "sourcing_mode": sourcing_mode,
        })

    def unpublish_job(self, job_id: int) -> APIResponse:
        """Unpublish a job."""
        return self._request("POST", f"/api/v1/jobs/{job_id}/unpublish")

    # -------------------------------------------------------------------
    # Screening configuration
    # -------------------------------------------------------------------

    def save_screening_config(
        self,
        job_id: int,
        questions: List[Dict[str, Any]],
        mode: str = "compact",
        eligibility_questions: Optional[List[Dict[str, Any]]] = None,
    ) -> APIResponse:
        """Save WSI screening questions for a job."""
        return self._request("POST", f"/api/v1/jobs/{job_id}/screening_config", json_body={
            "screening_questions": questions,
            "screening_mode": mode,
            "eligibility_questions": eligibility_questions or [],
        })

    # -------------------------------------------------------------------
    # Calibration
    # -------------------------------------------------------------------

    def get_calibration_candidates(self, job_id: int, limit: int = 5) -> APIResponse:
        """Get candidate profiles for calibration."""
        return self._request("GET", f"/api/v1/jobs/{job_id}/calibration_candidates", params={
            "limit": limit,
        })

    def submit_calibration_feedback(
        self,
        job_id: int,
        candidate_id: str,
        decision: str,
        reason: Optional[str] = None,
    ) -> APIResponse:
        """Submit calibration decision for a candidate."""
        return self._request("POST", f"/api/v1/jobs/{job_id}/calibration_feedback", json_body={
            "candidate_id": candidate_id,
            "decision": decision,
            "reason": reason,
        })

    # -------------------------------------------------------------------
    # Company configuration
    # -------------------------------------------------------------------

    def get_company_defaults(self, workspace_id: int) -> APIResponse:
        """Get company configuration defaults (recruitment policies, eligibility, etc.)."""
        return self._request("GET", f"/api/v1/workspaces/{workspace_id}/recruitment_config")

    # -------------------------------------------------------------------
    # JD Enrichment (delegates to Python backend WSI service)
    # -------------------------------------------------------------------

    def evaluate_jd(self, jd_text: str, title: str = "", seniority: str = "") -> APIResponse:
        """Call WSI JD evaluation endpoint."""
        return self._request("POST", "/api/v1/wsi/jd-evaluate", json_body={
            "job_description": jd_text,
            "title": title,
            "seniority": seniority,
        })

    # -------------------------------------------------------------------
    # Share link
    # -------------------------------------------------------------------

    def get_share_link(self, job_id: int) -> APIResponse:
        """Get the public share link for a published job."""
        return self._request("GET", f"/api/v1/jobs/{job_id}/share_link")
