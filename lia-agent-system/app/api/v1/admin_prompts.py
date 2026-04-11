"""
Admin — PromptVersionRegistry endpoints (Sprint B / André P3/R3).

GET /api/v1/admin/prompts/versions          → lista todos os prompts registrados
GET /api/v1/admin/prompts/versions/{name}   → versões de um nome específico

Requer autenticação de admin.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.shared.services.prompt_version_registry import prompt_version_registry

router = APIRouter(prefix="/admin/prompts", tags=["admin-prompts"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PromptVersionResponse(BaseModel):
    name: str
    version: str
    hash_prefix: str
    hash_sha256: str
    created_at: str


class PromptVersionListResponse(BaseModel):
    total: int
    versions: list[PromptVersionResponse]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_response(entry: dict) -> PromptVersionResponse:
    return PromptVersionResponse(
        name=entry["name"],
        version=entry["version"],
        hash_prefix=entry["hash_prefix"],
        hash_sha256=entry["hash_sha256"],
        created_at=entry["created_at"],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/versions", response_model=PromptVersionListResponse)
async def list_all_versions(
    current_user=Depends(get_current_user),
):
    """
    Lista todos os prompts registrados no PromptVersionRegistry.

    Retorna todas as versões de todos os nomes, ordenadas por (name, created_at).
    """
    all_entries = prompt_version_registry.list_all()
    return PromptVersionListResponse(
        total=len(all_entries),
        versions=[_to_response(e) for e in all_entries],
    )


@router.get("/versions/{name}", response_model=PromptVersionListResponse)
async def list_versions_by_name(
    name: str,
    current_user=Depends(get_current_user),
):
    """
    Lista todas as versões registradas para um nome de prompt específico.

    Retorna 404 se o nome não estiver registrado.
    """
    entries = prompt_version_registry.list_versions(name)
    if not entries:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhuma versão encontrada para o prompt '{name}'.",
        )
    return PromptVersionListResponse(
        total=len(entries),
        versions=[_to_response(e) for e in entries],
    )
