"""
Guardrails API — Fase 3

Endpoints para gestão de guardrails de agentes via interface admin.
Guardrails são regras de comportamento editáveis em produção sem deploy.

Endpoints:
  GET    /guardrails               — listar (com filtros)
  POST   /guardrails               — criar
  GET    /guardrails/{id}          — detalhe
  PUT    /guardrails/{id}          — atualizar
  PATCH  /guardrails/{id}/toggle   — ativar/desativar
  DELETE /guardrails/{id}          — soft delete (is_active=False)
  POST   /guardrails/seed-defaults — seed com guardrails primários e secundários padrão
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_user_company_id, require_admin
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.models.guardrail import Guardrail
from app.shared.compliance.guardrail_repository import GuardrailCreate, GuardrailRepository
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guardrails", tags=["guardrails"])


# ---------------------------------------------------------------------------
# Schemas de resposta
# ---------------------------------------------------------------------------

class GuardrailResponse(BaseModel):
    id: str
    level: str
    domain: str | None
    node: str | None
    tool: str | None
    rule: str
    blocking_message: str
    is_active: bool
    company_id: str | None
    updated_by: str
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj: Guardrail) -> "GuardrailResponse":
        return cls(
            id=str(obj.id),
            level=obj.level,
            domain=obj.domain,
            node=obj.node,
            tool=obj.tool,
            rule=obj.rule,
            blocking_message=obj.blocking_message,
            is_active=obj.is_active,
            company_id=obj.company_id,
            updated_by=obj.updated_by,
            updated_at=obj.updated_at,
        )


class GuardrailUpdateRequest(WeDoBaseModel):
    level: str | None = None
    domain: str | None = None
    node: str | None = None
    tool: str | None = None
    rule: str | None = None
    blocking_message: str | None = None
    is_active: bool | None = None
    updated_by: str = "admin"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[GuardrailResponse])
# TODO(phase2): extract to repository — guardrail policy management
async def list_guardrails(
    domain: str | None = Query(None, description="Filtrar por domínio"),
    company_id: str | None = Query(None, description="Filtrar por tenant"),
    is_active: bool | None = Query(None, description="Filtrar por status ativo"),
    level: str | None = Query(None, description="Filtrar por nível: primary | secondary"),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Lista guardrails com filtros opcionais."""
    guardrails = await GuardrailRepository.list_filtered(
        db,
        domain=domain,
        company_id=company_id,
        is_active=is_active,
        level=level,
    )
    return [GuardrailResponse.from_orm(g) for g in guardrails]


@router.post("", response_model=GuardrailResponse, status_code=201)
async def create_guardrail(
    data: GuardrailCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    """Cria um novo guardrail. Requer role admin."""
    guardrail = await GuardrailRepository.upsert(db, data)
    logger.info(
        "[Guardrail] modified guardrail_id=%s (create) by company_id=%s",
        str(guardrail.id),
        get_user_company_id(current_user),
    )
    return GuardrailResponse.from_orm(guardrail)


@router.get("/{guardrail_id}", response_model=GuardrailResponse)
async def get_guardrail(
    guardrail_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Retorna um guardrail pelo ID."""
    # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
    stmt = select(Guardrail).where(
        Guardrail.id == guardrail_id,
        Guardrail.company_id == company_id,
    )
    result = await db.execute(stmt)
    guardrail = result.scalar_one_or_none()

    if not guardrail:
        raise HTTPException(status_code=404, detail=f"Guardrail {guardrail_id} não encontrado")

    return GuardrailResponse.from_orm(guardrail)


@router.put("/{guardrail_id}", response_model=GuardrailResponse)
async def update_guardrail(
    guardrail_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: GuardrailUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    """Atualiza um guardrail existente."""
    # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
    stmt = select(Guardrail).where(
        Guardrail.id == guardrail_id,
        Guardrail.company_id == company_id,
    )
    result = await db.execute(stmt)
    guardrail = result.scalar_one_or_none()

    if not guardrail:
        raise HTTPException(status_code=404, detail=f"Guardrail {guardrail_id} não encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(guardrail, field, value)

    guardrail.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(guardrail)
    logger.info(
        "[Guardrail] modified guardrail_id=%s (update) by company_id=%s",
        guardrail_id,
        get_user_company_id(current_user),
    )
    return GuardrailResponse.from_orm(guardrail)


@router.patch("/{guardrail_id}/toggle", response_model=GuardrailResponse)
async def toggle_guardrail(
    guardrail_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    """Ativa ou desativa um guardrail sem deletá-lo."""
    guardrail = await GuardrailRepository.toggle_active(db, guardrail_id)

    if not guardrail:
        raise HTTPException(status_code=404, detail=f"Guardrail {guardrail_id} não encontrado")

    logger.info(
        "[Guardrail] modified guardrail_id=%s is_active=%s by company_id=%s",
        guardrail_id,
        guardrail.is_active,
        get_user_company_id(current_user),
    )
    return GuardrailResponse.from_orm(guardrail)


@router.delete("/{guardrail_id}", status_code=204, response_model=None)
async def delete_guardrail(
    guardrail_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    """Soft delete: desativa o guardrail (is_active=False). Dados preservados para auditoria."""
    deleted = await GuardrailRepository.soft_delete(db, guardrail_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Guardrail {guardrail_id} não encontrado")
    logger.info(
        "[Guardrail] modified guardrail_id=%s (soft-delete) by company_id=%s",
        guardrail_id,
        get_user_company_id(current_user),
    )


# ---------------------------------------------------------------------------
# Seed de guardrails padrão (idempotente)
# ---------------------------------------------------------------------------

DEFAULT_PRIMARY_GUARDRAILS: list[dict] = [
    {
        "level": "primary",
        "rule": "Nunca revelar dados pessoais não compartilhados explicitamente pelo usuário.",
        "blocking_message": "Não posso compartilhar dados pessoais sem autorização explícita.",
    },
    {
        "level": "primary",
        "rule": "Nunca discriminar por gênero, raça, idade, religião, estado civil, deficiência ou origem.",
        "blocking_message": "Esta ação viola as diretrizes anti-discriminação da plataforma.",
    },
    {
        "level": "primary",
        "rule": "Sempre identificar interação como gerada por IA quando solicitado.",
        "blocking_message": "Sou uma assistente de IA da WeDOTalent, projetada para apoiar processos de recrutamento de forma transparente.",
    },
    {
        "level": "primary",
        "rule": "Nunca criar perguntas que impliquem vida pessoal, familiar ou religiosa.",
        "blocking_message": "Esta pergunta não é apropriada para um processo seletivo.",
    },
    {
        "level": "primary",
        "rule": "Nunca confirmar ou negar existência de dados de usuário sem verificação de identidade.",
        "blocking_message": "Não posso confirmar informações de conta sem verificação adequada.",
    },
]

DEFAULT_SECONDARY_GUARDRAILS: list[dict] = [
    {
        "level": "secondary",
        "domain": "cv_screening",
        "rule": "Perguntas WSI exclusivamente sobre competências profissionais relevantes à vaga.",
        "blocking_message": "Esta pergunta está fora do escopo da avaliação profissional.",
    },
    {
        "level": "secondary",
        "domain": "communication",
        "rule": "Todo email gerado por IA inclui identificação de IA no rodapé.",
        "blocking_message": "Emails devem identificar conteúdo gerado por IA.",
    },
    {
        "level": "secondary",
        "domain": "sourcing",
        "rule": "Nunca inferir atributos protegidos a partir de nome, localização ou foto de perfil.",
        "blocking_message": "Não é permitido inferir atributos protegidos de candidatos.",
    },
    {
        "level": "secondary",
        "domain": "job_management",
        "rule": "Requisitos de vaga não podem incluir características físicas ou atributos protegidos.",
        "blocking_message": "Este requisito viola as diretrizes de equidade na contratação.",
    },
]


class SeedDefaultsResponse(BaseModel):
    created: int
    skipped: int
    total: int


@router.post("/seed-defaults", response_model=SeedDefaultsResponse, status_code=200)
async def seed_default_guardrails(
    company_id: str | None = Query(None, description="Tenant específico. None = global"),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    """
    Seed idempotente de guardrails padrão (primários e secundários).
    Usa upsert — não duplica se já existir com mesma rule + domain + company_id.
    """
    all_defaults = DEFAULT_PRIMARY_GUARDRAILS + DEFAULT_SECONDARY_GUARDRAILS
    created = 0
    skipped = 0

    for item in all_defaults:
        # Verificar se já existe guardrail com mesma rule e domain
        existing = await GuardrailRepository.find_by_rule_domain_company(
            db,
            rule=item["rule"],
            domain=item.get("domain"),
            company_id=company_id,
        )

        if existing:
            skipped += 1
            continue

        data = GuardrailCreate(
            level=item["level"],
            domain=item.get("domain"),
            rule=item["rule"],
            blocking_message=item["blocking_message"],
            company_id=company_id,
            updated_by="seed-defaults",
        )
        await GuardrailRepository.upsert(db, data)
        created += 1

    _actor = None
    try:
        _actor = get_user_company_id(current_user) if hasattr(current_user, "company_id") else None
    except Exception:
        pass
    logger.info(
        "[Guardrail] seed-defaults: criados=%s ignorados=%s company_id=%s by user_company=%s",
        created, skipped, company_id, _actor,
    )
    return SeedDefaultsResponse(created=created, skipped=skipped, total=len(all_defaults))

reorder_collection_before_item(router)
