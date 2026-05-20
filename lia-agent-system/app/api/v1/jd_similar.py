"""JD Similar History endpoints — Sprint B Phase 1.

Endpoints REST consumidos pelo frontend (plataforma-lia) para:
- Buscar JDs similares no histórico (GET /lookup)
- Registrar JD ao publicar vaga (POST /record)
- Incrementar contador de reuso (POST /{id}/reuse)
- Marcar vaga como preenchida (POST /mark-filled)

Multi-tenancy: company_id obrigatório (vem do JWT em produção; aqui via param explícito).
ADR-006: nenhum log inclui PII.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_user_company_id
from app.core.database import get_db
from app.domains.job_creation.repositories.jd_similar_history_repository import (
    JdSimilarHistoryRepository,
)
from app.domains.job_creation.services.jd_similar_service import JdSimilarService
from app.auth.models import User
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/jd-similar", tags=["jd-similar", "sprint-b"])


def _enforce_tenant(supplied: str, current_user: User) -> str:
    """UC-P0-08: company_id MUST match the authenticated user's tenant.

    Restored as part of import #963 hardening: imported endpoints accepted
    company_id directly from query/body without checking it against the JWT
    context. This helper rejects cross-tenant access fail-closed.
    """
    jwt_company = get_user_company_id(current_user)
    if not supplied or str(supplied) != str(jwt_company):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="company_id does not match authenticated tenant",
        )
    return str(jwt_company)


# ── Pydantic schemas ────────────────────────────────────────────────────────


class JdSimilarItem(BaseModel):
    id: str
    title: str
    department: str | None = None
    seniority_level: str | None = None
    was_filled: bool
    time_to_fill_days: int | None = None
    candidates_count: int
    similarity: float | None = None


class JdSimilarLookupResponse(BaseModel):
    items: list[JdSimilarItem]
    total_company_jds: int
    threshold_met: bool


class JdRecordRequest(WeDoBaseModel):
    job_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    jd_enriched: dict[str, Any]
    seniority_level: str | None = None
    department: str | None = None


class MarkFilledRequest(WeDoBaseModel):
    job_id: str = Field(..., min_length=1)
    time_to_fill_days: int = Field(..., ge=0)
    candidates_count: int = Field(..., ge=0)


class ReuseRequest(WeDoBaseModel):
    pass


class GenericResponse(BaseModel):
    ok: bool
    message: str | None = None


# ── DI helpers ──────────────────────────────────────────────────────────────


async def _get_service(db: AsyncSession = Depends(get_db)) -> JdSimilarService:
    """Builds JdSimilarService with default dependencies.

    EmbeddingService é resolvido lazy via factory (não import top-level pra
    evitar cycle no startup).
    """
    from app.shared.intelligence.embedding_service import EmbeddingService

    repo = JdSimilarHistoryRepository(db)
    embedding_service = EmbeddingService()
    return JdSimilarService(repository=repo, embedding_service=embedding_service)


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.get("/lookup", response_model=JdSimilarLookupResponse)
async def lookup_similar(
    company_id: str = Query(..., min_length=1),
    title: str = Query(..., min_length=1),
    department: str | None = Query(None),
    toggle_enabled: bool = Query(True),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))) -> JdSimilarLookupResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    company_id = _enforce_tenant(company_id, current_user)
    """Busca JDs similares no histórico da empresa.

    Returns empty list if:
    - toggle desligado
    - empresa tem < 10 JDs em histórico (threshold)
    - nenhuma JD bate min_similarity
    """
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_id is required",
        )

    repo = JdSimilarHistoryRepository(db)
    total = await repo.count_for_company(company_id)

    from app.shared.intelligence.embedding_service import EmbeddingService
    svc = JdSimilarService(repository=repo, embedding_service=EmbeddingService())

    items_raw = await svc.find_similar(
        company_id=company_id,
        title=title,
        department=department,
        toggle_enabled=toggle_enabled,
        min_similarity=min_similarity,
        limit=limit,
    )
    items = [JdSimilarItem(**item) for item in items_raw]

    return JdSimilarLookupResponse(
        items=items,
        total_company_jds=total,
        threshold_met=total >= 10,
    )


@router.post("/record", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def record_jd(
    body: JdRecordRequest,
    svc: JdSimilarService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
company_id: str = Depends(require_company_id)) -> GenericResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Registra JD enriquecida no histórico (chamado após publish bem-sucedido)."""
    try:
        await svc.record_jd(
            company_id=company_id,
            job_id=body.job_id,
            title=body.title,
            jd_enriched=body.jd_enriched,
            seniority_level=body.seniority_level,
            department=body.department,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return GenericResponse(ok=True, message="recorded")


@router.post("/{record_id}/reuse", response_model=GenericResponse)
async def increment_reuse(
    record_id: str,
    body: ReuseRequest,
    svc: JdSimilarService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
company_id: str = Depends(require_company_id)) -> GenericResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Incrementa contador de reuso quando recruiter usa JD do histórico como base."""
    try:
        await svc.increment_reuse(company_id=company_id, record_id=record_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return GenericResponse(ok=True)


@router.post("/mark-filled", response_model=GenericResponse)
async def mark_filled(
    body: MarkFilledRequest,
    svc: JdSimilarService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
company_id: str = Depends(require_company_id)) -> GenericResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Marca JD como preenchida (vaga fechou)."""
    try:
        await svc.mark_filled(
            company_id=company_id,
            job_id=body.job_id,
            time_to_fill_days=body.time_to_fill_days,
            candidates_count=body.candidates_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return GenericResponse(ok=True)
