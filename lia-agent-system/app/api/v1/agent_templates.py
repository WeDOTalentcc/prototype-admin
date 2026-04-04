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

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from libs.models.lia_models.agent_template import AgentTemplate, AgentTemplateStatus
from sqlalchemy import select, or_

router = APIRouter()

ALLOWED_DOMAINS = [
    "sourcing", "pipeline", "wsi", "lia_assistant", "job_wizard",
    "candidate_search", "automation", "analytics", "compliance",
]


# ── Schemas ───────────────────────────────────────────────────────────────────

class AgentTemplateCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=500)
    domain: str = Field(..., description=f"Um de: {ALLOWED_DOMAINS}")
    system_prompt_yaml: str = Field(..., min_length=50, description="System prompt em formato YAML")
    base_template_id: Optional[str] = None

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
    company_id: Optional[str]
    name: str
    domain: str
    system_prompt_yaml: str
    version: int
    status: str
    base_template_id: Optional[str]
    created_by: str
    created_at: datetime
    published_at: Optional[datetime]
    is_public: bool

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/agent-templates", response_model=List[AgentTemplateResponse])
async def list_templates(
    domain: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista templates disponíveis para a empresa:
    - Templates públicos WeDO (company_id IS NULL, status=published)
    - Templates próprios da empresa (qualquer status)
    """
    from sqlalchemy import or_

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
    db: AsyncSession = Depends(get_db),
):
    """Cria novo template de agente para a empresa. Status inicial: draft."""
    template = AgentTemplate(
        id=str(uuid4()),
        company_id=current_user.company_id,  # sempre escopado ao tenant
        name=body.name,
        domain=body.domain,
        system_prompt_yaml=body.system_prompt_yaml,
        version=1,
        status=AgentTemplateStatus.DRAFT,
        base_template_id=body.base_template_id,
        created_by=str(current_user.id),
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/agent-templates/{template_id}", response_model=AgentTemplateResponse)
async def get_template(
    template_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna um template pelo ID (próprio da empresa ou público WeDO)."""
    result = await db.execute(
        select(AgentTemplate).where(
            AgentTemplate.id == template_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    # Verificar acesso: próprio da empresa ou público WeDO
    if template.company_id and template.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    return template


@router.patch("/agent-templates/{template_id}", response_model=AgentTemplateResponse)
async def update_template(
    template_id: str,
    body: AgentTemplateCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Edita um template draft. Se estiver publicado, cria nova versão (imutabilidade).
    Templates públicos WeDO não podem ser editados diretamente — clonar primeiro.
    """
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

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
        new_version = AgentTemplate(
            id=str(uuid4()),
            company_id=current_user.company_id,
            name=body.name,
            domain=body.domain,
            system_prompt_yaml=body.system_prompt_yaml,
            version=template.version + 1,
            status=AgentTemplateStatus.DRAFT,
            base_template_id=template.base_template_id or template.id,
            created_by=str(current_user.id),
        )
        # Arquivar a versão anterior publicada
        template.status = AgentTemplateStatus.ARCHIVED
        template.archived_at = datetime.now(timezone.utc)

        db.add(new_version)
        await db.commit()
        await db.refresh(new_version)
        return new_version
    else:
        # Draft pode ser editado in-place
        template.name = body.name
        template.domain = body.domain
        template.system_prompt_yaml = body.system_prompt_yaml
        await db.commit()
        await db.refresh(template)
        return template


@router.post("/agent-templates/{template_id}/publish", response_model=AgentTemplateResponse)
async def publish_template(
    template_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Publica um template draft. Após publicar, o template entra em produção
    imediatamente (próxima requisição ao domínio usará este template).
    Templates publicados são imutáveis — editar cria nova versão.
    """
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    if template.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if template.status != AgentTemplateStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Apenas templates em 'draft' podem ser publicados. Status atual: {template.status}",
        )

    template.status = AgentTemplateStatus.PUBLISHED
    template.published_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/agent-templates/{template_id}", status_code=204)
async def archive_template(
    template_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Arquiva um template (soft delete — dados preservados para auditoria)."""
    result = await db.execute(
        select(AgentTemplate).where(AgentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template não encontrado.")

    if template.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    template.status = AgentTemplateStatus.ARCHIVED
    template.archived_at = datetime.now(timezone.utc)
    await db.commit()
