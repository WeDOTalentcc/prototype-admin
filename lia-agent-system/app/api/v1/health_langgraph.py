"""
Health endpoint — status da camada LangGraph nativa.

GET /api/v1/health/langgraph

Retorna:
- tipo de checkpointer ativo
- status de compilação dos 3 graph agents migrados
- latência de cada compilação (lazy — compilado no primeiro request)

Acesso restrito a admins (header X-Admin-Key ou role admin no JWT).
Não expõe PII nem estado de sessões.
"""
import logging
import time

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from fastapi import Depends

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class GraphHealthItem(BaseModel):
    name: str
    status: str          # "ok" | "error"
    checkpointer: str
    compile_ms: float | None = None
    error: str | None = None


class LangGraphHealthResponse(BaseModel):
    checkpointer_type: str
    graphs: list[GraphHealthItem]
    overall: str         # "ok" | "degraded" | "error"
    status: str          # alias for overall, for schema compatibility


def _probe_graph(name: str, factory) -> GraphHealthItem:
    """Tenta compilar um graph e retorna o resultado."""
    t0 = time.perf_counter()
    try:
        from lia_agents_core.checkpointer import get_checkpointer
        cp = get_checkpointer()
        cp_type = type(cp).__name__ if cp is not None else "MemorySaver(default)"

        factory()
        compile_ms = (time.perf_counter() - t0) * 1000
        return GraphHealthItem(
            name=name,
            status="ok",
            checkpointer=cp_type,
            compile_ms=round(compile_ms, 1),
        )
    except Exception as exc:
        compile_ms = (time.perf_counter() - t0) * 1000
        logger.warning("[health_langgraph] %s compile error: %s", name, exc)
        return GraphHealthItem(
            name=name,
            status="error",
            checkpointer="unknown",
            compile_ms=round(compile_ms, 1),
            error=str(exc)[:200],
        )


@router.get(
    "/health/langgraph",
    response_model=LangGraphHealthResponse,
    summary="Status da camada LangGraph nativa",
    description=(
        "Verifica o tipo de checkpointer ativo e tenta compilar "
        "os 3 graph agents migrados. Acesso restrito a administradores."
    ),
)
async def langgraph_health(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> LangGraphHealthResponse:
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    Health check da camada LangGraph nativa.

    Segurança: requer header X-Admin-Key configurado em settings.ADMIN_API_KEY,
    ou o endpoint estará desabilitado em produção (settings.DEBUG=False).
    """
    admin_key = getattr(settings, "ADMIN_API_KEY", None)
    debug_mode = getattr(settings, "DEBUG", False)

    if not debug_mode:
        if not admin_key or x_admin_key != admin_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin key required for this endpoint.",
            )

    try:
        from lia_agents_core.checkpointer import get_checkpointer
        cp = get_checkpointer()
        cp_type = type(cp).__name__ if cp is not None else "MemorySaver(default)"
    except Exception as exc:
        cp_type = f"error:{exc}"

    graphs: list[GraphHealthItem] = []

    def _interview_factory():
        from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
        g = InterviewGraph()
        return g._build_langgraph()

    graphs.append(_probe_graph("InterviewGraph", _interview_factory))

    def _wsi_factory():
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
        g = WSIInterviewGraph()
        return g._build_langgraph()

    graphs.append(_probe_graph("WSIInterviewGraph", _wsi_factory))

    error_count = sum(1 for g in graphs if g.status == "error")
    if error_count == 0:
        overall = "ok"
    elif error_count < len(graphs):
        overall = "degraded"
    else:
        overall = "error"

    # P2-L (Onda 1, PLAN_FIX_wizard_memory_loss 2026-05-10): fail-closed sensor.
    # Em production/staging, MemorySaver in-process e inadequado (wipa em
    # restart). Retornar HTTP 503 para alertar load balancer / canary.
    app_env = getattr(settings, "APP_ENV", "development")
    is_production_like = app_env in {"production", "staging"}
    memory_saver_names = {"MemorySaver", "MemorySaver(default)", "InMemorySaver"}
    if is_production_like and cp_type in memory_saver_names:
        logger.error(
            "[health_langgraph] FAIL-CLOSED: MemorySaver detectado em APP_ENV=%r — "
            "checkpoints nao persistem entre restarts. Investigar PostgresSaver/DATABASE_URL.",
            app_env,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "reason": "memory_saver_in_production",
                "checkpointer_type": cp_type,
                "app_env": app_env,
                "action": "investigar PostgresSaver + DATABASE_URL; ver lia_agents_core.checkpointer",
            },
        )

    return LangGraphHealthResponse(
        checkpointer_type=cp_type,
        graphs=graphs,
        overall=overall,
        status=overall,
    )
