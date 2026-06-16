"""
Endpoint RAG Search — GET /api/v1/candidates/rag-search

Busca híbrida de candidatos combinando pgvector (semântica) + tsvector (BM25).

Query params:
  q          (str, obrigatório) — query em linguagem natural
  company_id (str, obrigatório) — tenant ID
  limit      (int, default=20)  — número máximo de resultados
  alpha      (float, default=0.5) — blend weight: 0=BM25, 1=semântico
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.ai.services.rag_pipeline_service import rag_pipeline_service as _rag_service
from app.domains.ai.services.rag_pipeline_service import RAGSearchResult
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/candidates",
    tags=["rag-search"],
)


# ---------------------------------------------------------------------------
# Schemas de resposta
# ---------------------------------------------------------------------------


class RAGSearchResponse(BaseModel):
    """Resposta da busca RAG híbrida."""

    results: list[dict[str, Any]] = Field(description="Lista de candidatos encontrados")
    query: str = Field(description="Query original")
    total: int = Field(description="Total de resultados retornados")
    source: str = Field(description="Fonte: 'semantic' | 'bm25' | 'hybrid'")
    fairness_ok: bool = Field(description="FairnessGuard: diversidade de gênero no top-10")
    search_time_ms: float = Field(description="Tempo de busca em milissegundos")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadados internos")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/rag-search",
    response_model=RAGSearchResponse,
    summary="Busca RAG híbrida de candidatos",
    description=(
        "Combina pgvector (semântica cosine similarity) + tsvector BM25 "
        "para busca de candidatos em linguagem natural. "
        "Multi-tenant: resultados escopados por company_id."
    ),
)
async def rag_search_candidates(
    q: str = Query(..., min_length=1, description="Query em linguagem natural"),
    company_id: str = Query(..., min_length=1, description="Tenant ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Máximo de resultados"),
    alpha: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Blend weight: 0=BM25, 1=semântico, 0.5=híbrido",
    ),
    job_title: str = Query(default="", description="Título da vaga para LLM classification"),
    job_area: str = Query(default="", description="Área da vaga para LLM classification"),
    job_requirements: str = Query(default="", description="Requisitos da vaga para LLM classification"),
    sector: str = Query(default="", description="Setor para FairnessGuard L3 sector-aware check"),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))) -> RAGSearchResponse:
    # multi-tenancy: public endpoint (rag_search) — no tenant data
    """
    Executa busca híbrida de candidatos.

    - **q**: query em linguagem natural (ex: "desenvolvedor Python com experiência em AWS")
    - **company_id**: tenant ID para escopo multi-tenant
    - **limit**: número máximo de resultados (1-100)
    - **alpha**: peso do score semântico vs BM25
      - `0.0` = apenas BM25 (tsvector)
      - `1.0` = apenas semântico (pgvector)
      - `0.5` = híbrido balanceado (padrão)
    """
    try:
        result: RAGSearchResult = await _rag_service.search(
            query=q,
            company_id=company_id,
            db=db,
            limit=limit,
            alpha=alpha,
            job_title=job_title,
            job_area=job_area,
            job_requirements=job_requirements,
            sector=sector,
        )
        return RAGSearchResponse(
            results=result.results,
            query=result.query,
            total=result.total,
            source=result.source,
            fairness_ok=result.fairness_ok,
            search_time_ms=result.search_time_ms,
            metadata=result.metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "[RAGSearch] Erro inesperado: %s (q=%r, company_id=%r)",
            exc,
            q[:60],
            company_id,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Erro interno na busca RAG") from exc
