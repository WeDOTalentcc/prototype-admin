"""
OTT Service — auth header provider for Rails API calls.

Background (Wave 1.1, 2026-04-13):
  JobCreationAPIClient was importing this module but it did not exist,
  causing JobCreationDomain to be silently disabled in production (wizard
  WSI Phase B unavailable). This stub restores functionality by wrapping
  RAILS_API_TOKEN — the same pattern already used by:
    - app/domains/ats_integration/services/ats_clients/wedotalent_rails.py
    - app/api/v1/rails_sync.py
    - app/api/v1/rails_health.py

Usage:
    from app.services.ott_service import get_ott_service
    svc = get_ott_service()
    headers = svc.get_auth_header()  # {"Authorization": "Bearer <token>"}

Future evolution:
  If the Rails side introduces refreshable one-time tokens (OTT proper),
  this service can cache/refresh them without changing the public API.
"""
from __future__ import annotations

import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

_RAILS_TOKEN_ENV = "RAILS_API_TOKEN"


class OTTService:
    """Auth header provider. Reads RAILS_API_TOKEN at call time.

    Reads the env var on every call so that token rotation (kubectl rollout
    restart, Cloud Run revisions) is picked up without process restart.
    """

    def get_auth_header(self) -> Dict[str, str]:
        """Return Bearer auth header. Empty dict if token not configured
        — caller should degrade gracefully (401 from Rails = retry path)."""
        token = os.environ.get(_RAILS_TOKEN_ENV, "")
        if not token:
            logger.warning(
                "[OTTService] %s not set — returning empty auth header. "
                "Rails calls will likely 401. Set env var to enable.",
                _RAILS_TOKEN_ENV,
            )
            return {}
        return {"Authorization": f"Bearer {token}"}

    def invalidate(self) -> None:
        """Cache invalidation hook. No-op for env-based tokens.

        JobCreationAPIClient calls this on 401 to force refresh. Since
        we read env on every call, this is a no-op but kept for API
        compatibility. If upstream later issues refreshable tokens, the
        caching/refresh logic slots in here.
        """
        logger.debug("[OTTService] invalidate() called (no-op for env-based tokens)")


_instance: OTTService | None = None


def get_ott_service() -> OTTService:
    """Return the singleton OTTService instance (lazy)."""
    global _instance
    if _instance is None:
        _instance = OTTService()
    return _instance
