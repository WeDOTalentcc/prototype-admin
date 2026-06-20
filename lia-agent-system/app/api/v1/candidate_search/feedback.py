"""Endpoints de feedback de busca (like/dislike do recrutador sobre resultados).

Bug corrigido: o frontend (SearchFeedbackButtons) chamava POST /search/feedback e
GET /search/feedback/by-search, mas esses endpoints NUNCA existiram no backend (so
/calibration/feedback existia). Resultado: clique no like/dislike -> 404 -> o componente
revertia o estado otimista -> "nada acontece".

Persiste no modelo SearchFeedback (tabela search_feedbacks ja existente, com RLS por
company_id). Ancorado por search_fingerprint (criterios da busca) para re-hidratar ao
re-executar/resgatar a busca.
"""
import uuid as _uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.shared.security.require_company_id import require_company_id
from lia_models.search_feedback import SearchFeedback

from ._shared import User, get_current_user_or_demo, logger

router = APIRouter()


class SearchFeedbackRequest(BaseModel):
    # Canonical (CLAUDE.md REGRA 2): extra='forbid'; company_id NUNCA no payload (vem do JWT)
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    feedback_type: str  # 'like' | 'dislike'
    job_id: str | None = None
    search_query: str | None = None
    candidate_score: float | None = None
    candidate_name: str | None = None
    search_fingerprint: str | None = None


class SearchFeedbackResponse(BaseModel):
    success: bool
    feedback_type: str | None = None


async def _persist_search_feedback_internal(
    db: AsyncSession,
    *,
    company_id: str,
    user_id: str,
    candidate_id: str,
    feedback_type: str,
    job_id: str | None = None,
    search_query: str | None = None,
    candidate_score: float | None = None,
    candidate_name: str | None = None,
    search_fingerprint: str | None = None,
    reason: str | None = None,
) -> None:
    """Fonte unica de escrita em SearchFeedback (endpoint HTTP + wizard handler).

    Upsert por (company_id, candidate_id, user_id[, search_fingerprint]).
    NAO commita — caller decide (FastAPI: auto via get_tenant_db;
    wizard handler: commit explicito apos esta chamada).
    updated_at: delegado ao onupdate do modelo, sem atribuicao manual.
    reason: atualizado so quando fornecido (None preserva valor anterior no UPDATE).
    """
    conditions = [
        SearchFeedback.company_id == str(company_id),
        SearchFeedback.candidate_id == candidate_id,
        SearchFeedback.user_id == user_id,  # C1: per-recrutador — nao sobrescrever feedback de outro usuario
    ]
    if search_fingerprint:
        conditions.append(SearchFeedback.search_fingerprint == search_fingerprint)

    existing = (
        await db.execute(select(SearchFeedback).where(*conditions))
    ).scalars().first()

    if existing:
        existing.feedback_type = feedback_type
        existing.candidate_score = candidate_score
        existing.candidate_name = candidate_name
        existing.search_query = search_query
        if reason is not None:  # None preserva reason anterior; str (incl. "") sobrescreve
            existing.reason = reason
        # updated_at: onupdate do modelo dispara no flush — sem atribuicao manual (evita utcnow deprecation)
    else:
        db.add(
            SearchFeedback(
                id=str(_uuid.uuid4()),
                company_id=str(company_id),
                candidate_id=candidate_id,
                job_id=job_id,
                user_id=user_id,
                search_query=search_query,
                search_fingerprint=search_fingerprint,
                feedback_type=feedback_type,
                candidate_score=candidate_score,
                candidate_name=candidate_name,
                reason=reason,
            )
        )

    await db.flush()
    logger.info(
        "[SearchFeedback] %s candidate=%s fingerprint=%s",
        feedback_type, candidate_id, search_fingerprint,
    )


@router.post("/feedback", response_model=SearchFeedbackResponse)
async def submit_search_feedback(
    request: SearchFeedbackRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Persiste like/dislike do recrutador. Upsert por (company_id, candidate_id, fingerprint)."""
    user_id = str(
        getattr(current_user, "id", None)
        or getattr(current_user, "user_id", None)
        or ""
    )
    await _persist_search_feedback_internal(
        db,
        company_id=str(company_id),
        user_id=user_id,
        candidate_id=request.candidate_id,
        feedback_type=request.feedback_type,
        job_id=request.job_id,
        search_query=request.search_query,
        candidate_score=request.candidate_score,
        candidate_name=request.candidate_name,
        search_fingerprint=request.search_fingerprint,
        # reason: nao exposto no HTTP endpoint (campo interno, propagado so via wizard)
    )
    return SearchFeedbackResponse(success=True, feedback_type=request.feedback_type)


@router.get("/feedback/by-search")
async def get_search_feedback_by_fingerprint(
    fingerprint: str = Query(...),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """Re-hidrata os feedbacks de uma busca pelos criterios (fingerprint)."""
    rows = (
        await db.execute(
            select(SearchFeedback).where(
                SearchFeedback.company_id == str(company_id),
                SearchFeedback.search_fingerprint == fingerprint,
            )
        )
    ).scalars().all()
    return {"feedbacks": {r.candidate_id: r.feedback_type for r in rows}}
