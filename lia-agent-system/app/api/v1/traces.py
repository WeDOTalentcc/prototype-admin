"""
Traces API — Z6-02: acesso aos spans recentes do LightweightTracer / OTLP.

Endpoints:
  GET /api/v1/traces          → spans recentes (limit=50)
  GET /api/v1/traces/stats    → estatísticas agregadas
  GET /api/v1/traces/status   → status do exporter (OTLP ou lightweight)
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("", response_model=List[Dict[str, Any]])
async def get_recent_traces(
    limit: int = Query(50, ge=1, le=500, description="Máximo de spans retornados"),
    _: None = Depends(require_admin),
):
    """Retorna spans recentes capturados pelo LightweightTracer interno."""
    from app.shared.tracing import get_recent_traces
    return get_recent_traces(limit=limit)


@router.get("/stats", response_model=Dict[str, Any])
async def get_trace_stats(
    _: None = Depends(require_admin),
):
    """Retorna estatísticas agregadas de latência e erros dos spans."""
    from app.shared.tracing import get_trace_stats
    return get_trace_stats()


@router.get("/status", response_model=Dict[str, Any])
async def get_tracer_status(
    _: None = Depends(require_admin),
):
    """Retorna o status atual do exporter de traces."""
    from app.shared.tracing import is_otlp_active, _TRACES_ENABLED
    import os
    otlp = is_otlp_active()
    return {
        "traces_enabled": _TRACES_ENABLED,
        "otlp_active": otlp,
        "otlp_endpoint": os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
        "service_name": os.environ.get("OTEL_SERVICE_NAME", "lia-agent-system"),
        "exporter": "otlp" if otlp else "lightweight_internal",
    }
