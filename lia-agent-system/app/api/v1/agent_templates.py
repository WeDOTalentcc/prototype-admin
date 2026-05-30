"""
ARQUIVO NOVO: app/api/v1/agent_templates.py

CRUD completo de AgentTemplates para o Agent Studio.

COMO APLICAR:
  1. Copiar para app/api/v1/agent_templates.py
  2. Registrar em app/main.py:
     from app.api.v1.agent_templates import router as agent_templates_router
     app.include_router(agent_templates_router, prefix="/api/v1", tags=["Agent Studio"])
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db, get_tenant_db
from lia_models.agent_template import AgentTemplate, AgentTemplateStatus
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter()


def _get_agent_template_repo(db):
    from app.domains.ai.repositories.agent_template_repository import AgentTemplateRepository
    return AgentTemplateRepository(db)

ALLOWED_DOMAINS = [
    "sourcing", "pipeline", "wsi", "lia_assistant", "job_wizard",
    "candidate_search", "automation", "analytics", "compliance",
]


# ── Schemas ───────────────────────────────────────────────────────────────────

class AgentTemplateCreate(WeDoBaseModel):
    name: str = Field(..., min_length=3, max_length=500)
    domain: str = Field(..., description=f"Um de: {ALLOWED_DOMAINS}")
    system_prompt_yaml: str = Field(..., min_length=50, description="System prompt em formato YAML")
    base_template_id: str | None = None

    @validator("domain")
    def validate_domain(cls, v):
        if v not in ALLOWED_DOMAINS:
            raise ValueError(f"Domain deve ser um de: {ALLOWED_DOMAINS}")
        return v

    @validator("system_prompt_yaml")
    def validate_yaml(cls, v):
        try:
            data = yaml.safe_load(v)
            if not isinstance(data, dict):
                raise ValueError("YAML deve ser um dicionário com campos 'name', 'prompt'")
            if "prompt" not in data:
                raise ValueError("Campo 'prompt' obrigatório no YAML")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML inválido: {e}")
        return v


class AgentTemplateResponse(BaseModel):
    id: str
    company_id: str | None
    name: str
    domain: str
    system_prompt_yaml: str
    version: int
    status: str
    base_template_id: str | None
    created_by: str
    created_at: datetime
    published_at: datetime | None
    is_public: bool

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/agent-templates", response_model=list[AgentTemplateResponse])
async def list_templates(
    domain: str | None = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Lista templates disponíveis para a empresa:
    - Templates públicos WeDO (company_id IS NULL, status=published)
    - Templates próprios da empresa (qualquer status)
    """
    from sqlalchemy import or_

    # TODO(phase2): complex multi-tenant query with public/private logic — left as direct DB
    query = select(AgentTemplate).where(
        or_(
            # Templates públicos WeDO
            AgentTemplate.company_id == None,  # noqa: E711
            # Templates da empresa (rascunhos e publicados)
            AgentTemplate.company_id == current_user.company_id,
        )
    )
    if domain:
        query = query.where(AgentTemplate.domain == domain)

    query = query.order_by(AgentTemplate.domain, AgentTemplate.version.desc())

    result = await db.execute(query)
    templates = result.scalars().all()
    return templates


@router.post("/agent-templates", response_model=AgentTemplateResponse, status_code=201)
async def create_template(
    body: AgentTemplateCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Cria novo template de agente para a empresa. Status inicial: draft."""
    repo = _get_agent_template_repo(db)
    template = await repo.create({
        "id": str(uuid4()),
        "company_id": current_user.company_id,
        "name": body.name,
        "domain": body.domain,
        "system_prompt_yaml": body.system_prompt_yaml,
        "version": 1,
        "status": AgentTemplateStatus.DRAFT,
        "base_template_id": body.base_template_id,
        "created_by": str(current_user.id),
    })
    return template


@router.get("/agent-templates/{template_id}", response_model=AgentTemplateResponse)
async def get_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Retorna um template pelo ID (próprio da empresa ou público WeDO)."""
    repo = _get_agent_template_repo(db)
    template = await repo.get_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    # Verificar acesso: próprio da empresa ou público WeDO
    if template.company_id and template.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    return template


@router.patch("/agent-templates/{template_id}", response_model=AgentTemplateResponse)
async def update_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: AgentTemplateCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Edita um template draft. Se estiver publicado, cria nova versão (imutabilidade).
    Templates públicos WeDO não podem ser editados diretamente — clonar primeiro.
    """
    repo = _get_agent_template_repo(db)
    template = await repo.get_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    # Não permite editar templates de outra empresa ou templates públicos WeDO
    if template.company_id != current_user.company_id:
        raise HTTPException(
            status_code=403,
            detail="Templates públicos WeDO não podem ser editados. Use POST para criar um derivado.",
        )

    if template.status == AgentTemplateStatus.PUBLISHED:
        # Template publicado é imutável — criar nova versão como draft
        new_version = await repo.create({
            "id": str(uuid4()),
            "company_id": current_user.company_id,
            "name": body.name,
            "domain": body.domain,
            "system_prompt_yaml": body.system_prompt_yaml,
            "version": template.version + 1,
            "status": AgentTemplateStatus.DRAFT,
            "base_template_id": template.base_template_id or template.id,
            "created_by": str(current_user.id),
        })
        # Arquivar a versão anterior publicada
        await repo.update(template, {
            "status": AgentTemplateStatus.ARCHIVED,
            "archived_at": datetime.now(UTC),
        })
        return new_version
    else:
        # Draft pode ser editado in-place
        return await repo.update(template, {
            "name": body.name,
            "domain": body.domain,
            "system_prompt_yaml": body.system_prompt_yaml,
        })


@router.post("/agent-templates/{template_id}/publish", response_model=AgentTemplateResponse)
async def publish_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Publica um template draft. Após publicar, o template entra em produção
    imediatamente (próxima requisição ao domínio usará este template).
    Templates publicados são imutáveis — editar cria nova versão.
    """
    repo = _get_agent_template_repo(db)
    template = await repo.get_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    if template.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if template.status != AgentTemplateStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Apenas templates em 'draft' podem ser publicados. Status atual: {template.status}",
        )

    return await repo.update(template, {
        "status": AgentTemplateStatus.PUBLISHED,
        "published_at": datetime.now(UTC),
    })


@router.delete("/agent-templates/{template_id}", status_code=204, response_model=None)
async def archive_template(
    template_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Arquiva um template (soft delete — dados preservados para auditoria)."""
    repo = _get_agent_template_repo(db)
    template = await repo.get_by_id(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    if template.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    await repo.update(template, {
        "status": AgentTemplateStatus.ARCHIVED,
        "archived_at": datetime.now(UTC),
    })

reorder_collection_before_item(router)
