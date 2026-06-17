"""
Audit Timeline API.

GET /api/v1/audit/executions/{execution_id}/timeline
  → Reconstrói passo a passo o que o agente fez e por quê.
  → Consulta metadados no PostgreSQL + payload completo no storage configurado.

GET /api/v1/audit/executions?company_id=&domain=&limit=
  → Lista execuções recentes com metadados leves.

Acesso restrito: apenas usuários autenticados com company_id correspondente.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


class ExecutionMetadataResponse(BaseModel):
    execution_id: str
    session_id: str | None
    company_id: str
    user_id: str | None
    domain: str | None
    agent_type: str | None
    timestamp: str | None
    duration_ms: float | None
    nodes_visited: list | None
    tools_used: list | None
    success: bool | None
    confidence: float | None
    storage_path: str | None
    error: str | None


class TimelineStep(BaseModel):
    step: int
    type: str                       # "llm_call" | "tool_call" | "node_transition"
    timestamp: str
    model: str | None = None
    prompt_preview: str | None = None
    response_preview: str | None = None
    tokens_total: int | None = None
    latency_ms: float | None = None
    tool: str | None = None
    input_preview: str | None = None
    output_preview: str | None = None
    success: bool | None = None
    error: str | None = None
    from_node: str | None = None
    to_node: str | None = None


class TimelineResponse(BaseModel):
    execution_id: str
    domain: str | None
    user_id: str | None
    company_id: str
    timestamp: str | None
    duration_ms: float | None
    confidence: float | None
    success: bool | None
    steps: list[TimelineStep]
    total_steps: int
    storage_path: str | None


@router.get("/executions/{execution_id}/timeline", response_model=TimelineResponse)
# TODO(phase2): extract to repository — audit timeline queries
async def get_execution_timeline(
    execution_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Reconstrói a timeline completa de uma execução de agente.

    Carrega metadados do PostgreSQL e payload completo do storage.
    Multi-tenant: valida que execution_id pertence à empresa do usuário autenticado.
    """
    from sqlalchemy import text

    # 1. Buscar metadados no PostgreSQL com filtro tenant.
    # Onda 4.2d-P0-14 (2026-05-23): SQL inline agora inclui company_id filter.
    # Antes bypass `if user_company and ...` skipava check quando JWT sem
    # company_id = vazamento cross-tenant de audit trail interno.
    user_company = current_user.get("company_id") or current_user.get("organization_id")
    if not user_company:
        # Fail-closed: sem company_id no JWT, nega acesso (REGRA 6 CLAUDE.md).
        raise HTTPException(status_code=401, detail="company_id required")

    row = await db.execute(
        text(
            "SELECT * FROM audit_execution_metadata "
            "WHERE execution_id = :eid AND company_id = :company_id"
        ),
        {"eid": execution_id, "company_id": str(user_company)},
    )
    meta = row.mappings().first()

    if not meta:
        # 404 (no enumeration leak — inexistente OU cross-tenant).
        raise HTTPException(status_code=404, detail="Execução não encontrada")

    # 3. Carregar payload completo do storage
    steps: list[TimelineStep] = []
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


@router.get("/executions", response_model=list[ExecutionMetadataResponse])
async def list_executions(
    domain: str | None = Query(None),
    agent_type: str | None = Query(None),
    success: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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

reorder_collection_before_item(router)
