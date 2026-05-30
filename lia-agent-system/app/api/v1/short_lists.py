"""
Short List API — gerenciamento de short lists de candidatos por vaga.

Uma short list é uma CandidateList especializada com:
  - list_type = "shortlist"
  - job_id associado
  - candidatos ranqueados para uma vaga específica

Reutiliza CandidateList + CandidateListMember (sem nova tabela).
Migration necessária: adicionar coluna `list_type` e `job_id` em candidate_lists
(ou usar campo `color` como type discriminador — veja nota abaixo).

Nota de implementação: enquanto a migration 033 não existe, `list_type` é
armazenado no campo `description` com prefixo "shortlist:" para compatibilidade.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.candidates.repositories.short_list_repository import ShortListRepository
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/short-lists", tags=["short-lists"])

_SHORTLIST_PREFIX = "shortlist:"


# ── Schemas ──────────────────────────────────────────────────────────────────

class ShortListCreate(WeDoBaseModel):
    job_id: str
    name: str
    description: str | None = None


class ShortListCandidateAdd(BaseModel):
    candidate_id: str
    notes: str | None = None


class ShortListResponse(BaseModel):
    id: str
    job_id: str
    name: str
    description: str | None
    created_by: str
    created_at: str
    candidate_count: int


class ShortListCandidateResponse(BaseModel):
    id: str
    candidate_id: str
    added_at: str
    notes: str | None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_shortlist(record) -> bool:
    # Returns True if the record is a short list (description starts with shortlist: prefix).
    return bool(record.description and record.description.startswith(_SHORTLIST_PREFIX))


def _encode_meta(job_id: str, description: str | None = None) -> str:
    """Encoda job_id no campo description com prefixo shortlist:."""
    base = f"{_SHORTLIST_PREFIX}{job_id}"
    if description:
        base += f"|{description}"
    return base


def _decode_meta(description: str | None) -> tuple[str, str]:
    """Retorna (job_id, description) a partir do campo description."""
    if not description or not description.startswith(_SHORTLIST_PREFIX):
        return "", description or ""
    rest = description[len(_SHORTLIST_PREFIX):]
    if "|" in rest:
        job_id, desc = rest.split("|", 1)
    else:
        job_id, desc = rest, ""
    return job_id, desc


def _to_short_list_response(record) -> ShortListResponse:
    from app.models.candidate_list import CandidateList
    job_id, desc = _decode_meta(record.description)
    return ShortListResponse(
        id=str(record.id),
        job_id=job_id,
        name=record.name,
        description=desc or None,
        created_by=record.created_by,
        created_at=record.created_at.isoformat() if record.created_at else "",
        candidate_count=len(record.members) if record.members else 0,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ShortListResponse, status_code=201)
async def create_short_list(
    body: ShortListCreate,
    company_id: str = Query(..., description="Company ID (multi-tenant)"),
    user_id: str = Query("system"),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Cria uma short list para uma vaga."""
    repo = ShortListRepository(db)
    record = await repo.create(
        company_id=company_id,
        name=body.name,
        description_encoded=_encode_meta(body.job_id, body.description),
        created_by=user_id,
    )
    logger.info("[ShortList] Criada list_id=%s job_id=%s company=%s", record.id, body.job_id, company_id)
    return _to_short_list_response(record)


@router.get("", response_model=list[ShortListResponse])
async def list_short_lists(
    company_id: str = Query(...),
    job_id: str | None = Query(None, description="Filtrar por vaga"),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Lista short lists da empresa, opcionalmente filtradas por vaga."""
    repo = ShortListRepository(db)
    records = await repo.list_for_company(company_id, job_id=job_id)
    return [_to_short_list_response(r) for r in records]


@router.get("/{list_id}", response_model=ShortListResponse)
async def get_short_list(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Retorna uma short list pelo ID."""
    repo = ShortListRepository(db)
    record = await repo.get_by_id(list_id, company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Short list não encontrada")
    return _to_short_list_response(record)


@router.post("/{list_id}/candidates", response_model=ShortListCandidateResponse, status_code=201)
async def add_candidate(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: ShortListCandidateAdd,
    company_id: str = Query(...),
    db: AsyncSession = Depends(get_tenant_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Adiciona um candidato à short list."""
    repo = ShortListRepository(db)
    record = await repo.get_by_id(list_id, company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Short list não encontrada")

    # Evitar duplicatas
    existing = await repo.get_member(list_id, body.candidate_id)
    if existing:
        raise HTTPException(status_code=409, detail="Candidato já está na short list")

    member = await repo.add_member(list_id, body.candidate_id, body.notes)
    return ShortListCandidateResponse(
        id=str(member.id),
        candidate_id=str(member.candidate_id),
        added_at=member.added_at.isoformat() if hasattr(member, "added_at") and member.added_at else "",
        notes=body.notes,
    )


@router.delete("/{list_id}/candidates/{candidate_id}", status_code=204, response_model=None)
async def remove_candidate(
    list_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Remove um candidato da short list."""
    repo = ShortListRepository(db)
    record = await repo.get_by_id(list_id, company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Short list não encontrada")

    member = await repo.get_member(list_id, candidate_id)
    if not member:
        raise HTTPException(status_code=404, detail="Candidato não encontrado na short list")

    await repo.remove_member(member)

reorder_collection_before_item(router)
