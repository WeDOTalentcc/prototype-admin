"""
Rails API Health Check — validates connectivity and circuit breaker status.

Endpoints:
  GET /api/v1/rails/health    — probe Rails API reachability + circuit state
  GET /api/v1/rails/status    — detailed circuit breaker stats for rails_api

Does NOT require authentication so that infrastructure monitoring tools
can call it without user credentials. The probe uses the service token
(RAILS_API_TOKEN) when configured.
"""
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends

from app.domains.integrations_hub.services.rails_adapter import RailsAdapter
from app.domains.integrations_hub.services.rails_adapter_dependency import get_rails_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rails", tags=["rails-integration"])

RAILS_API_URL = os.environ.get("RAILS_API_URL", "")
RAILS_API_TOKEN_SET = bool(os.environ.get("RAILS_API_TOKEN", ""))


@router.get("/health", summary="Rails API health check")
async def rails_health(adapter: RailsAdapter = Depends(get_rails_adapter)) -> dict[str, Any]:
    """
    Probe the Rails API for connectivity.

    Returns:
      - rails_enabled: whether RAILS_API_URL is configured
      - status: ok | degraded | unreachable | disabled
      - latency_ms: round-trip time in milliseconds
      - circuit_breaker: current state of the rails_api circuit
    """
    result = await adapter.health_check()
    result["rails_url"] = RAILS_API_URL or "(not configured)"
    result["service_token_configured"] = RAILS_API_TOKEN_SET
    return result


@router.get("/status", summary="Rails circuit breaker status")
async def rails_circuit_status() -> dict[str, Any]:
    """
    Return detailed circuit breaker statistics for the rails_api circuit.

    Does not make an HTTP call to Rails — reads local circuit state only.
    """
    from app.shared.resilience.circuit_breaker import RAILS_CIRCUIT, CIRCUIT_BREAKER_SLOS
    stats = RAILS_CIRCUIT.get_stats()
    slo = CIRCUIT_BREAKER_SLOS.get("rails_api", {})
    return {
        "circuit": stats,
        "slo": slo,
        "rails_url": RAILS_API_URL or "(not configured)",
        "rails_enabled": bool(RAILS_API_URL),
        "service_token_configured": RAILS_API_TOKEN_SET,
    }
