"""
Prometheus metrics endpoint — C4.

GET /api/v1/metrics → generate_latest() do prometheus_client.
Formato: text/plain; version=0.0.4 (padrão Prometheus).
"""
from fastapi import APIRouter, Response

router = APIRouter(prefix="/api/v1", tags=["observability"])


@router.get("/metrics", response_class=Response)
async def prometheus_metrics() -> Response:
    """Expõe métricas Prometheus coletadas pelos agentes LIA."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return Response(
            content="# prometheus_client not available\n",
            media_type="text/plain",
            status_code=200,
        )
