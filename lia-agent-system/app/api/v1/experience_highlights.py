"""
Experience Highlights API - AI-generated candidate experience summaries.

This module provides endpoints for generating and caching AI-powered
experience highlights for candidates. Highlights are cached for 30+ days
to optimize LLM costs.
"""
import logging
import os
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_tenant_db
from app.domains.cv_screening.repositories.experience_highlight_repository import ExperienceHighlightRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, CANDIDATE_OR_SOURCING_ID_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experience-highlights", tags=["Experience Highlights"])

CACHE_TTL_DAYS = 35


class ExperienceHighlightResponse(BaseModel):
    """Response schema for experience highlight."""
    id: str
    candidate_id: str
    highlight_text: str
    generated_at: datetime
    expires_at: datetime
    is_cached: bool = True
    model_used: str = "claude-sonnet-4-6"


class GenerateHighlightRequest(WeDoBaseModel):
    """Request schema for generating a new highlight."""
    candidate_id: str
    candidate_name: str
    current_title: str | None = None
    current_company: str | None = None
    location: str | None = None
    years_of_experience: int | None = None
    technical_skills: list[str] = Field(default_factory=list)
    work_history: list[dict] = Field(default_factory=list)
    force_regenerate: bool = False


def generate_highlight_prompt(data: GenerateHighlightRequest) -> str:
    """Generate the prompt for Claude to create the experience highlight."""
    work_history_text = ""
    if data.work_history:
        for i, job in enumerate(data.work_history[:5]):
            title = job.get('title', job.get('position', 'Unknown'))
            company = job.get('company', job.get('company_name', 'Unknown'))
            start = job.get('start_date', job.get('startDate', ''))
            end = job.get('end_date', job.get('endDate', 'Present'))
            description = job.get('description', job.get('summary', ''))
            location = job.get('location', '')

            work_history_text += f"""
Experience {i+1}:
- Title: {title}
- Company: {company}
- Period: {start} - {end}
- Location: {location}
- Description: {description[:300] if description else 'N/A'}
"""

    skills_text = ", ".join(data.technical_skills[:15]) if data.technical_skills else "N/A"

    prompt = f"""Gere um resumo conciso da experiência do candidato para recrutadores entenderem rapidamente seu perfil profissional.

PERFIL DO CANDIDATO:
- Nome: {data.candidate_name}
- Cargo Atual: {data.current_title or 'N/A'}
- Empresa Atual: {data.current_company or 'N/A'}
- Localização: {data.location or 'N/A'}
- Anos de Experiência: {data.years_of_experience or 'N/A'}
- Principais Skills: {skills_text}

HISTÓRICO PROFISSIONAL:
{work_history_text or 'Histórico não disponível'}

INSTRUÇÕES:
1. Escreva 1-2 frases resumindo quem é esta pessoa profissionalmente
2. Destaque sua principal expertise/especialização
3. Mencione sua localização e há quanto tempo trabalha na área
4. Inclua skills ou tecnologias notáveis
5. Se tiver experiência em desenvolvimento mobile, mencione
6. Mantenha em até 50 palavras
7. Escreva em português do Brasil
8. Comece com "[Nome] é um(a) [cargo]..."
9. Seja factual e específico, não genérico

FORMATO DE SAÍDA:
Retorne APENAS o texto do resumo, sem aspas ou formatação extra.

EXEMPLO DE SAÍDA:
Rafael Iga é um Engenheiro de Software com expertise em Ruby on Rails, atuando em São Paulo desde janeiro de 2020. Possui ampla experiência em desenvolvimento web e também desenvolveu aplicações mobile."""

    return prompt


async def generate_highlight_with_ai(data: GenerateHighlightRequest) -> str:
    """Generate experience highlight using LLMProviderFactory (Task #93 migration)."""
    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant

        container = get_provider_for_tenant()
        highlight_text = await container.generate_with_fallback(generate_highlight_prompt(data), agent_type="ExperienceHighlightAgent")
        highlight_text = highlight_text.strip()

        if highlight_text.startswith('"') and highlight_text.endswith('"'):
            highlight_text = highlight_text[1:-1]

        return highlight_text

    except Exception as e:
        logger.error(f"Error generating highlight with AI: {e}")
        return generate_fallback_highlight(data)


def generate_fallback_highlight(data: GenerateHighlightRequest) -> str:
    """Generate a simple fallback highlight without AI."""
    name = data.candidate_name or "Este candidato"
    title = data.current_title or "profissional"
    company = data.current_company
    location = data.location
    years = data.years_of_experience
    skills = data.technical_skills[:3] if data.technical_skills else []

    parts = [f"{name} é um(a) {title}"]

    if company:
        parts[0] += f" na {company}"

    if location:
        parts.append(f"com sede em {location}")

    if years:
        parts.append(f"com {years} anos de experiência")

    if skills:
        skills_text = ", ".join(skills[:3])
        parts.append(f"especializado(a) em {skills_text}")

    return ". ".join(parts) + "."


@router.get("/{candidate_id}", response_model=None)
async def get_experience_highlight(
    candidate_id: Annotated[str, Path(pattern=CANDIDATE_OR_SOURCING_ID_PATTERN)],
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> ExperienceHighlightResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    company_id = current_user.company_id
    """
    Get cached experience highlight for a candidate.
    Returns 404 if no cached highlight exists.
    """
    repo = ExperienceHighlightRepository(db)
    # F11 fix (2026-05-24): ensure_table() removed — table is alembic-managed
    # (migration 138). Calling CREATE TABLE IF NOT EXISTS raises
    # InsufficientPrivilegeError under lia_app role, which forces a rollback
    # that drops the transaction-scoped `app.company_id` GUC from get_tenant_db,
    # making subsequent INSERTs into RLS-protected tables fail with
    # "new row violates row-level security policy".

    row = await repo.get_valid_highlight(candidate_id, company_id)

    if not row:
        raise HTTPException(status_code=404, detail="No cached highlight found")

    return ExperienceHighlightResponse(
        id=str(row[0]),
        candidate_id=str(row[1]),
        highlight_text=row[2],
        model_used=row[3],
        generated_at=row[4],
        expires_at=row[5],
        is_cached=True
    )


@router.post("/generate", response_model=None)
async def generate_experience_highlight(
    request: GenerateHighlightRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> ExperienceHighlightResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    company_id = current_user.company_id
    """
    Generate or retrieve cached experience highlight for a candidate.
    """
    # F11 fix (2026-05-24): manually set RLS tenant context on the session
    # BEFORE the INSERT. get_tenant_db sets it at session setup, but the LLM
    # call (generate_highlight_with_ai) doesn't touch the DB and may not
    # explicitly hold the transaction — and ensure_table() rollback used to
    # drop the GUC. Re-setting here is idempotent and defense-in-depth against
    # RLS "new row violates row-level security policy" on candidate_experience_highlights.
    from app.core.database import set_tenant_context as _set_tenant
    if company_id:
        await _set_tenant(db, str(company_id))
    repo = ExperienceHighlightRepository(db)

    if not request.force_regenerate:
        row = await repo.get_valid_highlight(request.candidate_id, company_id)
        if row:
            return ExperienceHighlightResponse(
                id=str(row[0]),
                candidate_id=str(row[1]),
                highlight_text=row[2],
                model_used=row[3],
                generated_at=row[4],
                expires_at=row[5],
                is_cached=True
            )

    highlight_text = await generate_highlight_with_ai(request)

    now = datetime.utcnow()
    expires_at = now + timedelta(days=CACHE_TTL_DAYS)
    highlight_id = str(uuid4())

    # F11 fix: re-inject tenant context right before INSERT — defense-in-depth.
    # LLM call above may take 5-30s. RLS GUC is transaction-scoped and could
    # have been dropped by any implicit commit/rollback in unrelated code paths
    # (rate-limiter, logging middleware, observability spans).
    if company_id:
        await _set_tenant(db, str(company_id))

    row = await repo.upsert_highlight(
        highlight_id=highlight_id,
        candidate_id=request.candidate_id,
        company_id=company_id,
        highlight_text=highlight_text,
        model_used="claude-sonnet-4-6",
        generated_at=now,
        expires_at=expires_at,
    )

    return ExperienceHighlightResponse(
        id=str(row[0]),
        candidate_id=str(row[1]),
        highlight_text=row[2],
        model_used=row[3],
        generated_at=row[4],
        expires_at=row[5],
        is_cached=False
    )


@router.delete("/{candidate_id}", response_model=None)
async def delete_experience_highlight(
    candidate_id: Annotated[str, Path(pattern=CANDIDATE_OR_SOURCING_ID_PATTERN)],
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    company_id = current_user.company_id
    """Delete cached highlight for a candidate (admin use)."""
    repo = ExperienceHighlightRepository(db)
    # F11 fix (2026-05-24): ensure_table() removed — table is alembic-managed
    # (migration 138). Calling CREATE TABLE IF NOT EXISTS raises
    # InsufficientPrivilegeError under lia_app role, which forces a rollback
    # that drops the transaction-scoped `app.company_id` GUC from get_tenant_db,
    # making subsequent INSERTs into RLS-protected tables fail with
    # "new row violates row-level security policy".

    deleted = await repo.delete_highlight(candidate_id, company_id)
    return {"deleted": deleted > 0, "candidate_id": candidate_id}


@router.post("/batch-generate", response_model=None)
async def batch_generate_highlights(
    candidates: list[GenerateHighlightRequest],
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> list[ExperienceHighlightResponse]:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Generate highlights for multiple candidates at once.
    Limited to 10 candidates per request.
    """
    if len(candidates) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 candidates per batch request"
        )

    results = []
    for candidate_data in candidates:
        try:
            highlight = await generate_experience_highlight(
                request=candidate_data,
                db=db,
                current_user=current_user
            )
            results.append(highlight)
        except Exception as e:
            logger.error(f"Error generating highlight for {candidate_data.candidate_id}: {e}")
            results.append(ExperienceHighlightResponse(
                id=str(uuid4()),
                candidate_id=candidate_data.candidate_id,
                highlight_text=generate_fallback_highlight(candidate_data),
                model_used="fallback",
                generated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=1),
                is_cached=False
            ))

    return results

reorder_collection_before_item(router)
