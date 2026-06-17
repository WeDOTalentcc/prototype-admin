"""services canonical — PR-17 step 3 extract (2026-05-26 ONDA 3 follow-up).

Service singleton getters movidos de graph.py:
- _get_jd_service (lazy-init JdEnrichmentService)
- _get_wsi_generator (lazy-init WSIQuestionGenerator)
- _get_api_client (per-token JobCreationAPIClient)
"""

from typing import Optional

from app.domains.job_creation.api_client import JobCreationAPIClient
from app.domains.job_creation.services.jd_enrichment import JdEnrichmentService
from app.domains.job_creation.services.wsi_question_generator import WSIQuestionGenerator

# Shared service instances (lazy-initialized)
_jd_service: Optional[JdEnrichmentService] = None
_wsi_generator: Optional[WSIQuestionGenerator] = None
_api_client: Optional[JobCreationAPIClient] = None


def _get_jd_service() -> JdEnrichmentService:
    global _jd_service
    if _jd_service is None:
        _jd_service = JdEnrichmentService()
    return _jd_service


def _get_wsi_generator() -> WSIQuestionGenerator:
    global _wsi_generator
    if _wsi_generator is None:
        _wsi_generator = WSIQuestionGenerator()
    return _wsi_generator


def _get_api_client(state: dict) -> JobCreationAPIClient:
    """Get API client with auth context from state."""
    global _api_client
    # Recreate if auth token changes
    token = state.get("auth_token", "")
    if _api_client is None or getattr(_api_client, "_last_token", "") != token:
        # Build minimal context for auth
        ctx = type("Ctx", (), {
            "auth_token": token,
            "track_api_call": lambda *a, **k: None,
        })()
        _api_client = JobCreationAPIClient(context=ctx)
        _api_client._last_token = token
    return _api_client
