"""LIA Profile Analysis API - Generates AI-powered candidate summaries in different formats."""

import logging
import os
from typing import Any

from anthropic import Anthropic
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lia_profile_analysis import LiaProfileAnalysis
from app.schemas.lia_profile_analysis import (
    CandidateAnalysesSummary,
    LiaProfileAnalysisCreate,
    LiaProfileAnalysisResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia/profile-analysis", tags=["LIA Profile Analysis"])

AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

client = Anthropic(
    api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
    base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
)

class CandidateData(BaseModel):
    name: str | None = None
    current_role: str | None = None
    current_company: str | None = None
    location: str | None = None
    experience_years: int | None = None
    skills: list[str] | None = []
    education: list[dict[str, Any]] | None = []
    experiences: list[dict[str, Any]] | None = []
    summary: str | None = None

class ProfileAnalysisRequest(BaseModel):
    candidate_id: str
    analysis_type: str  # 'bullet_points', 'short_paragraph', 'detailed_bullets'
    candidate_data: CandidateData

class ProfileAnalysisResponse(BaseModel):
    analysis: str
    analysis_type: str
    candidate_id: str


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


def get_system_prompt(analysis_type: str) -> str:
    """Get the system prompt based on analysis type."""
    
    base = """Você é a LIA, uma assistente de recrutamento com IA. Gere um resumo profissional do candidato com base nas informações fornecidas. Seja conciso, preciso e destaque os pontos fortes. NÃO inclua o nome do candidato no início - ele será adicionado separadamente. Responda sempre em português do Brasil."""
    
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
async def generate_profile_analysis(request: ProfileAnalysisRequest):
    """Generate an AI-powered profile analysis for a candidate."""
    
    valid_types = ['bullet_points', 'short_paragraph', 'detailed_bullets']
    if request.analysis_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid analysis_type. Must be one of: {valid_types}")
    
    candidate_info = format_candidate_info(request.candidate_data)
    
    if not candidate_info or len(candidate_info) < 20:
        raise HTTPException(status_code=400, detail="Insufficient candidate data to generate analysis")
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=get_system_prompt(request.analysis_type),
            messages=[
                {
                    "role": "user",
                    "content": f"Generate a {request.analysis_type.replace('_', ' ')} profile summary for this candidate:\n\n{candidate_info}"
                }
            ]
        )
        
        analysis_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                analysis_text = block.text.strip()
                break
        
        return ProfileAnalysisResponse(
            analysis=analysis_text,
            analysis_type=request.analysis_type,
            candidate_id=request.candidate_id
        )
        
    except Exception as e:
        print(f"Error generating profile analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")


@router.post("/save", response_model=LiaProfileAnalysisResponse)
async def save_profile_analysis(
    request: LiaProfileAnalysisCreate,
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    db: AsyncSession = Depends(get_db)
):
    """Save a generated profile analysis to the database."""
    try:
        existing_query = select(LiaProfileAnalysis).where(
            and_(
                LiaProfileAnalysis.candidate_id == request.candidate_id,
                LiaProfileAnalysis.analysis_type == request.analysis_type,
                LiaProfileAnalysis.company_id == company_id,
                LiaProfileAnalysis.is_active == True
            )
        )
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.content = request.content
            existing.candidate_name = request.candidate_name
            await db.commit()
            await db.refresh(existing)
            return LiaProfileAnalysisResponse(
                id=str(existing.id),
                candidate_id=existing.candidate_id,
                analysis_type=existing.analysis_type,
                content=existing.content,
                candidate_name=existing.candidate_name,
                is_active=existing.is_active,
                created_at=existing.created_at,
                created_by=existing.created_by,
                company_id=existing.company_id
            )
        
        new_analysis = LiaProfileAnalysis(
            candidate_id=request.candidate_id,
            analysis_type=request.analysis_type,
            content=request.content,
            candidate_name=request.candidate_name,
            created_by=request.created_by,
            company_id=company_id
        )
        
        db.add(new_analysis)
        await db.commit()
        await db.refresh(new_analysis)
        
        return LiaProfileAnalysisResponse(
            id=str(new_analysis.id),
            candidate_id=new_analysis.candidate_id,
            analysis_type=new_analysis.analysis_type,
            content=new_analysis.content,
            candidate_name=new_analysis.candidate_name,
            is_active=new_analysis.is_active,
            created_at=new_analysis.created_at,
            created_by=new_analysis.created_by,
            company_id=new_analysis.company_id
        )
        
    except Exception as e:
        logger.error(f"Error saving profile analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save analysis: {str(e)}")


@router.get("/candidate/{candidate_id}", response_model=CandidateAnalysesSummary)
async def get_candidate_analyses(
    candidate_id: str,
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    db: AsyncSession = Depends(get_db)
):
    """Get all saved analyses for a candidate."""
    try:
        query = select(LiaProfileAnalysis).where(
            and_(
                LiaProfileAnalysis.candidate_id == candidate_id,
                LiaProfileAnalysis.company_id == company_id,
                LiaProfileAnalysis.is_active == True
            )
        ).order_by(desc(LiaProfileAnalysis.created_at))
        
        result = await db.execute(query)
        analyses = result.scalars().all()
        
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
        
    except Exception as e:
        logger.error(f"Error fetching candidate analyses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analyses: {str(e)}")


@router.delete("/candidate/{candidate_id}/{analysis_type}", response_model=None)
async def delete_candidate_analysis(
    candidate_id: str,
    analysis_type: str,
    company_id: str = Query(..., description="Company ID for multi-tenancy"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific analysis for a candidate."""
    try:
        query = select(LiaProfileAnalysis).where(
            and_(
                LiaProfileAnalysis.candidate_id == candidate_id,
                LiaProfileAnalysis.analysis_type == analysis_type,
                LiaProfileAnalysis.company_id == company_id,
                LiaProfileAnalysis.is_active == True
            )
        )
        result = await db.execute(query)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        analysis.is_active = False
        await db.commit()
        
        return {"success": True, "message": "Analysis deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")
