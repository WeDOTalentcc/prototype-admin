"""LIA Profile Analysis API - Generates AI-powered candidate summaries in different formats."""

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
# sqlalchemy ORM imports moved to ProfileAnalysisRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.cv_screening.repositories.profile_analysis_repository import ProfileAnalysisRepository
from app.models.lia_profile_analysis import LiaProfileAnalysis
from app.schemas.lia_profile_analysis import (
    CandidateAnalysesSummary,
    LiaProfileAnalysisCreate,
    LiaProfileAnalysisResponse,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia/profile-analysis", tags=["LIA Profile Analysis"])

class CandidateData(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str | None = None
    current_role: str | None = None
    current_company: str | None = None
    location: str | None = None
    experience_years: int | None = None
    skills: list[str] | None = []
    education: list[dict[str, Any]] | None = []
    experiences: list[dict[str, Any]] | None = []
    summary: str | None = None

class ProfileAnalysisRequest(WeDoBaseModel):
    candidate_id: str
    analysis_type: str  # 'bullet_points', 'short_paragraph', 'detailed_bullets'
    candidate_data: CandidateData

class ProfileAnalysisResponse(BaseModel):
    analysis: str
    analysis_type: str
    candidate_id: str


# TODO(phase2): extract to repository — LIA profile analysis storage
def format_candidate_info(data: CandidateData) -> str:
    """Format candidate data for the prompt."""
    info_parts = []
    
    if data.name:
        info_parts.append(f"Name: {data.name}")
    if data.current_role:
        info_parts.append(f"Current Role: {data.current_role}")
    if data.current_company:
        info_parts.append(f"Current Company: {data.current_company}")
    if data.location:
        info_parts.append(f"Location: {data.location}")
    if data.experience_years:
        info_parts.append(f"Years of Experience: {data.experience_years}")
    if data.skills:
        info_parts.append(f"Skills: {', '.join(data.skills[:20])}")
    if data.summary:
        info_parts.append(f"Summary: {data.summary}")
    
    if data.education:
        edu_parts = []
        for edu in data.education[:3]:
            if isinstance(edu, dict):
                edu_str = f"- {edu.get('institution', edu.get('instituicao', 'Unknown'))}: {edu.get('degree', edu.get('curso', ''))} ({edu.get('year', edu.get('ano', ''))})"
                edu_parts.append(edu_str)
        if edu_parts:
            info_parts.append("Education:\n" + "\n".join(edu_parts))
    
    if data.experiences:
        exp_parts = []
        for exp in data.experiences[:5]:
            if isinstance(exp, dict):
                company = exp.get('company', exp.get('empresa', 'Unknown'))
                role = exp.get('role', exp.get('cargo', ''))
                period = exp.get('period', exp.get('periodo', ''))
                exp_str = f"- {company}: {role} ({period})"
                exp_parts.append(exp_str)
        if exp_parts:
            info_parts.append("Work Experience:\n" + "\n".join(exp_parts))
    
    return "\n".join(info_parts)


async def get_system_prompt(analysis_type: str, *, company_id: str, db) -> str:
    """Get the system prompt based on analysis type.

    Now async + tenant-aware (ghost setting fix 2026-05-24): persona name+tone
    custom da UI "Personalidade da IA" agora chega ao CV screening.
    """
    from app.shared.prompts.persona_aware_prompt import (
        build_system_prompt_with_persona,
    )
    base = await build_system_prompt_with_persona(
        company_id=company_id,
        db=db,
        agent_type="cv_screening",
        extra_instructions="Gere um resumo profissional do candidato. Seja conciso, preciso e destaque os pontos fortes. NÃO inclua o nome do candidato no início - ele será adicionado separadamente.",
    )
    
    if analysis_type == 'bullet_points':
        return base + """

Gere um resumo breve com 4-5 bullet points. Foque em:
- Anos de experiência e especialização principal
- Cargo atual ou mais recente
- Destaques da formação acadêmica
- Principais habilidades técnicas

Use formato de bullet points (• ou -). Mantenha cada ponto em 1-2 linhas no máximo. Seja direto e factual."""
    
    elif analysis_type == 'short_paragraph':
        return base + """

Escreva um único parágrafo fluido (4-6 frases) que capture o perfil profissional do candidato. Inclua seu nível de experiência, cargo atual, principais habilidades e formação acadêmica. Escreva em terceira pessoa. Faça com que leia naturalmente como um resumo profissional."""
    
    elif analysis_type == 'detailed_bullets':
        return base + """

Crie um perfil detalhado com as seguintes seções:

Destaques do Perfil:
- 4-5 bullet points sobre a identidade profissional geral

Experiência Profissional:
- Principais cargos e empresas com breves descrições

Formação:
- Histórico acadêmico

Habilidades:
- Competências técnicas e profissionais

Use hífen (-) para bullet points. Seja abrangente mas conciso."""
    
    return base


@router.post("", response_model=ProfileAnalysisResponse)
async def generate_profile_analysis(
    request: ProfileAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Generate an AI-powered profile analysis for a candidate."""
    
    valid_types = ['bullet_points', 'short_paragraph', 'detailed_bullets']
    if request.analysis_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid analysis_type. Must be one of: {valid_types}")
    
    candidate_info = format_candidate_info(request.candidate_data)
    
    if not candidate_info or len(candidate_info) < 20:
        raise HTTPException(status_code=400, detail="Insufficient candidate data to generate analysis")
    
    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant

        container = get_provider_for_tenant()
        # F11 Bug B fix (2026-05-24): pass agent_type="ProfileAnalysisAgent" so
        # the token budget guard applies the 2.5x multiplier (5000 cap instead
        # of 2000 default). System prompt + full candidate data + expected LLM
        # output for "Análise Detalhada" routinely exceeds 4K tokens — was
        # being silently blocked with HTTP 500 "Request excede ceiling".
        analysis_text = await container.generate_with_fallback(
            f"Generate a {request.analysis_type.replace('_', ' ')} profile summary for this candidate:\n\n{candidate_info}",
            system=await get_system_prompt(request.analysis_type, company_id=company_id, db=db),
            agent_type="ProfileAnalysisAgent",
        )
        analysis_text = analysis_text.strip()
        
        return ProfileAnalysisResponse(
            analysis=analysis_text,
            analysis_type=request.analysis_type,
            candidate_id=request.candidate_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating profile analysis: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.post("/save", response_model=LiaProfileAnalysisResponse)
async def save_profile_analysis(
    request: LiaProfileAnalysisCreate,
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Save a generated profile analysis to the database."""
    try:
        repo = ProfileAnalysisRepository(db)
        existing = await repo.get_active_by_candidate_type_company(
            candidate_id=request.candidate_id,
            analysis_type=request.analysis_type,
            company_id=company_id,
        )

        if existing:
            updated = await repo.update_content(existing, request.content, request.candidate_name)
            return LiaProfileAnalysisResponse(
                id=str(updated.id),
                candidate_id=updated.candidate_id,
                analysis_type=updated.analysis_type,
                content=updated.content,
                candidate_name=updated.candidate_name,
                is_active=updated.is_active,
                created_at=updated.created_at,
                created_by=updated.created_by,
                company_id=updated.company_id,
            )

        new_analysis = await repo.create(
            candidate_id=request.candidate_id,
            analysis_type=request.analysis_type,
            content=request.content,
            candidate_name=request.candidate_name,
            created_by=request.created_by,
            company_id=company_id,
        )

        return LiaProfileAnalysisResponse(
            id=str(new_analysis.id),
            candidate_id=new_analysis.candidate_id,
            analysis_type=new_analysis.analysis_type,
            content=new_analysis.content,
            candidate_name=new_analysis.candidate_name,
            is_active=new_analysis.is_active,
            created_at=new_analysis.created_at,
            created_by=new_analysis.created_by,
            company_id=new_analysis.company_id,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving profile analysis: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/candidate/{candidate_id}", response_model=CandidateAnalysesSummary)
async def get_candidate_analyses(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get all saved analyses for a candidate."""
    try:
        repo = ProfileAnalysisRepository(db)
        analyses = await repo.get_all_active_for_candidate(candidate_id, company_id)
        
        has_bullet_points = False
        has_short_paragraph = False
        has_detailed_bullets = False
        
        response_items = []
        for analysis in analyses:
            response_items.append(LiaProfileAnalysisResponse(
                id=str(analysis.id),
                candidate_id=analysis.candidate_id,
                analysis_type=analysis.analysis_type,
                content=analysis.content,
                candidate_name=analysis.candidate_name,
                is_active=analysis.is_active,
                created_at=analysis.created_at,
                created_by=analysis.created_by,
                company_id=analysis.company_id
            ))
            
            if analysis.analysis_type == "bullet_points":
                has_bullet_points = True
            elif analysis.analysis_type == "short_paragraph":
                has_short_paragraph = True
            elif analysis.analysis_type == "detailed_bullets":
                has_detailed_bullets = True
        
        return CandidateAnalysesSummary(
            candidate_id=candidate_id,
            total_analyses=len(analyses),
            analyses=response_items,
            has_bullet_points=has_bullet_points,
            has_short_paragraph=has_short_paragraph,
            has_detailed_bullets=has_detailed_bullets
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candidate analyses: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.delete("/candidate/{candidate_id}/{analysis_type}", response_model=None)
async def delete_candidate_analysis(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    analysis_type: str,
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Delete a specific analysis for a candidate."""
    try:
        repo = ProfileAnalysisRepository(db)
        analysis = await repo.soft_delete(candidate_id, analysis_type, company_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {"success": True, "message": "Analysis deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
