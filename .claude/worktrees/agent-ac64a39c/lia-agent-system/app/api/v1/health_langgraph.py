"""
Health endpoint — status da migração LangGraph nativa.

GET /api/v1/health/langgraph

Retorna:
- flag USE_LANGGRAPH_NATIVE e tipo de checkpointer ativo
- status de compilação dos 3 graph agents migrados
- latência de cada compilação (lazy — compilado no primeiro request)

Acesso restrito a admins (header X-Admin-Key ou role admin no JWT).
Não expõe PII nem estado de sessões.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class GraphHealthItem(BaseModel):
    name: str
    status: str          # "ok" | "error" | "skipped"
    checkpointer: str
    compile_ms: Optional[float] = None
    error: Optional[str] = None


class LangGraphHealthResponse(BaseModel):
    use_langgraph_native: bool
    checkpointer_type: str
    graphs: List[GraphHealthItem]
    overall: str         # "ok" | "degraded" | "error"


def _probe_graph(name: str, factory) -> GraphHealthItem:
    """Tenta compilar um graph e retorna o resultado."""
    t0 = time.perf_counter()
    try:
        from app.shared.agents.checkpointer import get_checkpointer
        cp = get_checkpointer()
        cp_type = type(cp).__name__ if cp is not None else "MemorySaver(default)"

        graph = factory()
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
    summary="Status da migração LangGraph nativa",
    description=(
        "Verifica o estado do feature flag USE_LANGGRAPH_NATIVE e tenta compilar "
        "os 3 graph agents migrados. Acesso restrito a administradores."
    ),
)
async def langgraph_health(
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> LangGraphHealthResponse:
    """
    Health check da camada LangGraph nativa.

    Segurança: requer header X-Admin-Key configurado em settings.ADMIN_API_KEY,
    ou o endpoint estará desabilitado em produção (settings.DEBUG=False).
    """
    # --- Auth guard ---
    admin_key = getattr(settings, "ADMIN_API_KEY", None)
    debug_mode = getattr(settings, "DEBUG", False)

    if not debug_mode:
        if not admin_key or x_admin_key != admin_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin key required for this endpoint.",
            )

    # --- Checkpointer type ---
    try:
        from app.shared.agents.checkpointer import get_checkpointer
        cp = get_checkpointer()
        cp_type = type(cp).__name__ if cp is not None else "MemorySaver(default)"
    except Exception as exc:
        cp_type = f"error:{exc}"

    # --- Probe each graph ---
    graphs: List[GraphHealthItem] = []

    if settings.USE_LANGGRAPH_NATIVE:
        # InterviewGraph
        def _interview_factory():
            from app.domains.interview_scheduling.agents.interview_graph import InterviewGraph
            g = InterviewGraph()
            return g._build_langgraph()

        graphs.append(_probe_graph("InterviewGraph", _interview_factory))

        # WSIInterviewGraph
        def _wsi_factory():
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewGraph
            g = WSIInterviewGraph()
            return g._build_langgraph()

        graphs.append(_probe_graph("WSIInterviewGraph", _wsi_factory))

        # JobWizardGraph
        def _wizard_factory():
            from app.domains.job_management.agents.job_wizard_graph import JobWizardGraph
            g = JobWizardGraph()
            return g._build_langgraph()

        graphs.append(_probe_graph("JobWizardGraph", _wizard_factory))
    else:
        # Flag desativado — graphs não são compilados, retornar como skipped
        for name in ("InterviewGraph", "WSIInterviewGraph", "JobWizardGraph"):
            graphs.append(GraphHealthItem(
                name=name,
                status="skipped",
                checkpointer=cp_type,
                error="USE_LANGGRAPH_NATIVE=False — LangGraph path not active",
            ))

    # --- Overall status ---
    error_count = sum(1 for g in graphs if g.status == "error")
    if error_count == 0:
        overall = "ok"
    elif error_count < len(graphs):
        overall = "degraded"
    else:
        overall = "error"

    return LangGraphHealthResponse(
        use_langgraph_native=settings.USE_LANGGRAPH_NATIVE,
        checkpointer_type=cp_type,
        graphs=graphs,
        overall=overall,
    )
