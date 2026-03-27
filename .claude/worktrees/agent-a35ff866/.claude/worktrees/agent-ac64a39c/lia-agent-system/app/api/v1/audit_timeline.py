"""
Audit Timeline — endpoint de reconstrução de raciocínio de agentes.

GET /api/v1/audit/executions/{execution_id}/timeline
  → Reconstrói passo a passo o que o agente fez e por quê.
  → Consulta metadados no PostgreSQL + payload completo no storage configurado.

GET /api/v1/audit/executions?company_id=&domain=&limit=
  → Lista execuções recentes com metadados leves.

Acesso restrito: apenas usuários autenticados com company_id correspondente.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


class ExecutionMetadataResponse(BaseModel):
    execution_id: str
    session_id: Optional[str]
    company_id: str
    user_id: Optional[str]
    domain: Optional[str]
    agent_type: Optional[str]
    timestamp: Optional[str]
    duration_ms: Optional[float]
    nodes_visited: Optional[list]
    tools_used: Optional[list]
    success: Optional[bool]
    confidence: Optional[float]
    storage_path: Optional[str]
    error: Optional[str]


class TimelineStep(BaseModel):
    step: int
    type: str                       # "llm_call" | "tool_call" | "node_transition"
    timestamp: str
    model: Optional[str] = None
    prompt_preview: Optional[str] = None
    response_preview: Optional[str] = None
    tokens_total: Optional[int] = None
    latency_ms: Optional[float] = None
    tool: Optional[str] = None
    input_preview: Optional[str] = None
    output_preview: Optional[str] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    from_node: Optional[str] = None
    to_node: Optional[str] = None


class TimelineResponse(BaseModel):
    execution_id: str
    domain: Optional[str]
    user_id: Optional[str]
    company_id: str
    timestamp: Optional[str]
    duration_ms: Optional[float]
    confidence: Optional[float]
    success: Optional[bool]
    steps: List[TimelineStep]
    total_steps: int
    storage_path: Optional[str]


@router.get("/executions/{execution_id}/timeline", response_model=TimelineResponse)
async def get_execution_timeline(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Reconstrói a timeline completa de uma execução de agente.

    Carrega metadados do PostgreSQL e payload completo do storage.
    Multi-tenant: valida que execution_id pertence à empresa do usuário autenticado.
    """
    from sqlalchemy import text

    # 1. Buscar metadados no PostgreSQL
    row = await db.execute(
        text("SELECT * FROM audit_execution_metadata WHERE execution_id = :eid"),
        {"eid": execution_id},
    )
    meta = row.mappings().first()

    if not meta:
        raise HTTPException(status_code=404, detail="Execução não encontrada")

    # 2. Validar multi-tenancy
    user_company = current_user.get("company_id") or current_user.get("organization_id")
    if user_company and str(meta["company_id"]) != str(user_company):
        raise HTTPException(status_code=403, detail="Acesso negado")

    # 3. Carregar payload completo do storage
    steps: List[TimelineStep] = []
    storage_path = meta.get("storage_path")

    if storage_path:
        from app.shared.compliance.audit_storage import get_audit_storage
        storage = get_audit_storage()
        full_payload = await storage.load(storage_path)
        if full_payload:
            entries = full_payload.get("entries", [])
            for i, entry in enumerate(entries, start=1):
                steps.append(TimelineStep(
                    step=i,
                    type=entry.get("type", "unknown"),
                    timestamp=entry.get("timestamp", ""),
                    model=entry.get("model"),
                    prompt_preview=entry.get("prompt_preview"),
                    response_preview=entry.get("response_preview"),
                    tokens_total=entry.get("tokens_total"),
                    latency_ms=entry.get("latency_ms"),
                    tool=entry.get("tool"),
                    input_preview=entry.get("input_preview"),
                    output_preview=entry.get("output_preview"),
                    success=entry.get("success"),
                    error=entry.get("error"),
                    from_node=entry.get("from_node"),
                    to_node=entry.get("to_node"),
                ))

    timestamp_val = meta.get("timestamp")
    return TimelineResponse(
        execution_id=execution_id,
        domain=meta.get("domain"),
        user_id=meta.get("user_id"),
        company_id=str(meta["company_id"]),
        timestamp=timestamp_val.isoformat() if hasattr(timestamp_val, "isoformat") else str(timestamp_val) if timestamp_val else None,
        duration_ms=meta.get("duration_ms"),
        confidence=meta.get("confidence"),
        success=meta.get("success"),
        steps=steps,
        total_steps=len(steps),
        storage_path=storage_path,
    )


@router.get("/executions", response_model=List[ExecutionMetadataResponse])
async def list_executions(
    domain: Optional[str] = Query(None),
    agent_type: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lista execuções recentes com metadados leves.
    Filtros: domain, agent_type, success. Paginação: limit/offset.
    """
    from sqlalchemy import text

    company_id = current_user.get("company_id") or current_user.get("organization_id")
    if not company_id:
        raise HTTPException(status_code=401, detail="company_id não encontrado no token")

    where_clauses = ["company_id = :company_id"]
    params: dict = {"company_id": company_id, "limit": limit, "offset": offset}

    if domain:
        where_clauses.append("domain = :domain")
        params["domain"] = domain
    if agent_type:
        where_clauses.append("agent_type = :agent_type")
        params["agent_type"] = agent_type
    if success is not None:
        where_clauses.append("success = :success")
        params["success"] = success

    where_sql = " AND ".join(where_clauses)
    query = text(f"""
        SELECT * FROM audit_execution_metadata
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()

    def _fmt_ts(val):
        if val is None:
            return None
        return val.isoformat() if hasattr(val, "isoformat") else str(val)

    return [
        ExecutionMetadataResponse(
            execution_id=str(row["execution_id"]),
            session_id=row.get("session_id"),
            company_id=str(row["company_id"]),
            user_id=row.get("user_id"),
            domain=row.get("domain"),
            agent_type=row.get("agent_type"),
            timestamp=_fmt_ts(row.get("timestamp")),
            duration_ms=row.get("duration_ms"),
            nodes_visited=row.get("nodes_visited") or [],
            tools_used=row.get("tools_used") or [],
            success=row.get("success"),
            confidence=row.get("confidence"),
            storage_path=row.get("storage_path"),
            error=row.get("error"),
        )
        for row in rows
    ]
