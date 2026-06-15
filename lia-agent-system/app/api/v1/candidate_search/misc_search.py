"""
CV-based search, search analytics, and prompt enhancement routes.
"""
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    CVParserService,
    CandidateSearchResultDTO,
    HybridSearchRequest,
    PearchService,
    SearchType,
    get_cv_parser_service,
    get_db,
    get_pearch_service,
    logger,
    search_analytics_service,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter()

# Sprint F.3 #25 canonical-fix: CVSearchResultDTO moved to api/v1/candidate_search/archetypes.py
from app.api.v1.candidate_search.archetypes import CVSearchResultDTO  # noqa: F401  (re-export for backward compat)
from app.shared.types import WeDoBaseModel


@router.post("/from-cv", response_model=CVSearchResultDTO)
async def search_from_cv(
    file: UploadFile = File(..., description="CV file (PDF, DOCX, DOC, or TXT)"),
    limit: int = Query(20, ge=1, le=50, description="Number of results"),
    search_pearch: bool = Query(True, description="Include Pearch AI search"),
    pearch_type: str = Query("fast", description="Search type (always fast)"),
    db: AsyncSession = Depends(get_db)
,
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
    pearch_svc: PearchService = Depends(get_pearch_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Upload a CV file and search for similar candidates.
    
    Flow:
    1. Parse CV using AI to extract structured data
    2. Build search query from extracted title, skills, and experience
    3. Search for similar candidates in local database and optionally Pearch AI
    4. Return parsed CV data along with matching candidates
    
    Supported formats: PDF, DOCX, DOC, TXT
    Maximum file size: 5MB
    """
    import time
    start_time = time.time()
    
    try:
        parsed_cv = await cv_parser_svc.parse_cv(file)
        
        query_parts = []
        extracted_title = None
        extracted_skills = parsed_cv.skills[:10] if parsed_cv.skills else []
        
        if parsed_cv.experiences and len(parsed_cv.experiences) > 0:
            current_exp = parsed_cv.experiences[0]
            if current_exp.title:
                extracted_title = current_exp.title
                query_parts.append(current_exp.title)
        
        if parsed_cv.skills:
            top_skills = parsed_cv.skills[:5]
            query_parts.append(f"com experiência em {', '.join(top_skills)}")
        
        if parsed_cv.location:
            query_parts.append(f"em {parsed_cv.location}")
        
        generated_query = " ".join(query_parts) if query_parts else "profissional experiente"
        
        hybrid_request = HybridSearchRequest(
            query=generated_query,
            search_local_first=True,
            include_pearch=search_pearch,
            pearch_type=SearchType.FAST,
            local_limit=limit,
            pearch_limit=limit
        )
        
        result = await pearch_svc.hybrid_search(db, hybrid_request)
        
        candidates = []
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        search_time = time.time() - start_time
        
        parsed_cv_dict = {
            "full_name": parsed_cv.full_name,
            "email": parsed_cv.email,
            "phone": parsed_cv.phone,
            "linkedin": parsed_cv.linkedin,
            "github": parsed_cv.github,
            "portfolio": parsed_cv.portfolio,
            "location": parsed_cv.location,
            "summary": parsed_cv.summary,
            "skills": parsed_cv.skills,
            "languages": parsed_cv.languages,
            "certifications": parsed_cv.certifications,
            "confidence_score": parsed_cv.confidence_score,
            "extraction_notes": parsed_cv.extraction_notes,
            "experiences_count": len(parsed_cv.experiences) if parsed_cv.experiences else 0,
            "education_count": len(parsed_cv.education) if parsed_cv.education else 0,
        }
        
        return CVSearchResultDTO(
            parsed_cv=parsed_cv_dict,
            query_generated=generated_query,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=result.total_count,
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=search_time,
            extracted_skills=extracted_skills,
            extracted_title=extracted_title
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# SEARCH ANALYTICS ENDPOINT - Proactive analysis of search results
# ============================================================================

class AnalyzeSearchRequest(WeDoBaseModel):
    """Request para análise de resultados de busca."""
    candidates: list[dict[str, Any]] = Field(..., description="Lista de candidatos para analisar")
    search_criteria: dict[str, Any] | None = Field(None, description="Critérios de busca opcionais")
    generate_narrative: bool = Field(True, description="Gerar narrativa textual")


class SearchAnalyticsSummary(BaseModel):
    """Summary metrics."""
    total_candidates: int
    local_count: int
    global_count: int
    average_lia_score: float


class ContactQuality(BaseModel):
    """Contact quality metrics."""
    with_valid_phone: int
    with_valid_email: int
    with_linkedin: int
    phone_percentage: float
    email_percentage: float


class SkillMetric(BaseModel):
    """Skill distribution metric."""
    skill: str
    count: int
    percentage: float


class CompanyMetric(BaseModel):
    """Company distribution metric."""
    company: str
    count: int


class ExperienceRange(BaseModel):
    """Experience years range."""
    min: int
    max: int
    average: float
    median: float


class Alert(BaseModel):
    """Alert message."""
    type: str
    message: str


class SuggestedAction(BaseModel):
    """Suggested action."""
    id: str
    label: str
    icon: str
    description: str
    action_type: str


class AnalyzeSearchResponse(BaseModel):
    """Response da análise de busca."""
    summary: SearchAnalyticsSummary
    contact_quality: ContactQuality
    distributions: dict[str, dict[str, int]]
    top_skills: list[SkillMetric]
    top_companies: list[CompanyMetric]
    experience_range: ExperienceRange
    alerts: list[Alert]
    suggested_actions: list[SuggestedAction]
    narrative: str | None = None


@router.post("/analyze", response_model=AnalyzeSearchResponse)
async def analyze_search_results(request: AnalyzeSearchRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analisa resultados de busca e retorna métricas proativas.
    
    Este endpoint fornece:
    - Summary: Total de candidatos, divisão local/global, score médio
    - Contact Quality: Percentual com telefone, email, LinkedIn
    - Distributions: Senioridade, localização, modelo de trabalho
    - Top Skills: Skills mais comuns nos candidatos
    - Top Companies: Empresas mais comuns
    - Experience Range: Estatísticas de experiência
    - Alerts: Alertas contextuais (ex: concentração em empresas concorrentes)
    - Suggested Actions: Ações sugeridas para o pool de candidatos
    - Narrative: Descrição textual proativa (se generate_narrative=True)
    """
    try:
        analytics = search_analytics_service.analyze_search_results(
            candidates=request.candidates,
            search_criteria=request.search_criteria
        )
        
        if request.generate_narrative:
            narrative = search_analytics_service.generate_proactive_narrative(analytics)
            analytics["narrative"] = narrative
        
        summary = SearchAnalyticsSummary(**analytics["summary"])
        contact_quality = ContactQuality(**analytics["contact_quality"])
        experience_range = ExperienceRange(**analytics["experience_range"])
        
        top_skills = [SkillMetric(**s) for s in analytics["top_skills"]]
        top_companies = [CompanyMetric(**c) for c in analytics["top_companies"]]
        alerts = [Alert(**a) for a in analytics["alerts"]]
        suggested_actions = [SuggestedAction(**a) for a in analytics["suggested_actions"]]
        
        return AnalyzeSearchResponse(
            summary=summary,
            contact_quality=contact_quality,
            distributions=analytics["distributions"],
            top_skills=top_skills,
            top_companies=top_companies,
            experience_range=experience_range,
            alerts=alerts,
            suggested_actions=suggested_actions,
            narrative=analytics.get("narrative")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


class EnhancePromptRequest(WeDoBaseModel):
    """Request para aprimorar prompt de busca."""
    query: str = Field(..., description="Query original do usuário")
    context: dict[str, Any] | None = Field(None, description="Contexto adicional (vaga, filtros, etc)")


class EnhancePromptSuggestion(BaseModel):
    """Sugestão de melhoria para o prompt."""
    label: str = Field(..., description="Label curto da sugestão")
    value: str = Field(..., description="Valor a adicionar ao prompt")
    category: str = Field(..., description="Categoria: location, experience, skills, industry, salary")


class EnhancePromptResponse(BaseModel):
    """Response com prompt aprimorado."""
    original_query: str
    enhanced_query: str
    explanation: str
    suggestions: list[EnhancePromptSuggestion]
    confidence: float = Field(ge=0, le=1, description="Confiança da sugestão (0-1)")


@router.post("/enhance-prompt", response_model=EnhancePromptResponse)
async def enhance_search_prompt(
    request: EnhancePromptRequest,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analisa e aprimora um prompt de busca de candidatos.
    
    A LIA analisa o prompt original e sugere melhorias baseadas em:
    - Critérios faltantes (localização, experiência, skills, etc)
    - Melhores práticas de busca booleana
    - Contexto da vaga (se fornecido)
    
    Retorna:
    - enhanced_query: Versão otimizada do prompt
    - explanation: Explicação das melhorias
    - suggestions: Sugestões adicionais que o usuário pode aplicar
    """
    from app.domains.ai.services.llm import llm_service
    
    try:
        from app.shared.prompts.persona_aware_prompt import (
            build_system_prompt_with_persona,
        )
        _persona = await build_system_prompt_with_persona(
            company_id=company_id,
            db=db,
            agent_type="sourcing",
            extra_instructions="Otimize a busca de candidatos com critérios completos.",
        )
        prompt = f"""{_persona}

Otimize a busca de candidatos para recrutamento.

PROMPT ORIGINAL DO RECRUTADOR:
"{request.query}"

{f'CONTEXTO ADICIONAL: {request.context}' if request.context else ''}

CRITÉRIOS ESSENCIAIS PARA UMA BUSCA COMPLETA:
1. CARGO: Título da posição (ex: Desenvolvedor Backend, Product Manager)
2. SENIORIDADE: Nível de experiência (ex: Júnior, Pleno, Sênior, Tech Lead)
3. LOCALIZAÇÃO: Cidade/Estado específico ou modelo de trabalho (ex: São Paulo Capital, Remoto Brasil)
4. HABILIDADES: Skills técnicas específicas (ex: Python, React, AWS)
5. SETOR/INDÚSTRIA: Área de atuação preferida (ex: Fintech, E-commerce, Saúde)
6. EXPERIÊNCIA: Tempo mínimo em anos (ex: 5+ anos de experiência)

REGRAS DE OTIMIZAÇÃO:
1. Mantenha a intenção original mas COMPLETE os critérios faltantes de forma inteligente
2. DESAMBIGUE localizações vagas (ex: "São Paulo" → "São Paulo Capital, SP")
3. Se mencionar tecnologias, sugira nível de proficiência
4. Adicione senioridade se não especificada baseado no contexto
5. O enhanced_query deve ser uma versão MELHOR e MAIS COMPLETA do original
6. Máximo de 200 caracteres para o prompt otimizado
7. Use linguagem natural em português brasileiro

IMPORTANTE: Analise o que FALTA no prompt e sugira completar. Cada sugestão deve indicar um critério específico que melhoraria a busca.

FORMATO DE RESPOSTA (JSON):
{{
  "enhanced_query": "prompt otimizado e mais completo aqui",
  "explanation": "O que foi adicionado: senioridade, localização precisa, etc",
  "suggestions": [
    {{"label": "Nível de experiência", "value": "Sênior 5+ anos", "category": "experience"}},
    {{"label": "Setor preferido", "value": "Fintech ou Startup", "category": "industry"}},
    {{"label": "Modelo de trabalho", "value": "Remoto ou Híbrido SP", "category": "work_model"}}
  ],
  "confidence": 0.85
}}

CATEGORIAS VÁLIDAS: experience, industry, work_model, location, seniority, skills, salary, education, languages

Responda APENAS com o JSON, sem texto adicional."""

        from app.shared.tenant_llm_context import get_tenant_llm_config as _get_tc
        _tc = await _get_tc(company_id)
        _provider = _tc.get("primary_provider", "gemini") if _tc else "gemini"
        llm_service._current_tenant = company_id
        response = await llm_service.generate(prompt, provider=_provider)
        
        import json
        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            result = json.loads(clean_response.strip())
        except json.JSONDecodeError:
            result = {
                "enhanced_query": request.query,
                "explanation": "Prompt mantido como original",
                "suggestions": [],
                "confidence": 0.5
            }
        
        suggestions = []
        for s in result.get("suggestions", []):
            if isinstance(s, dict) and all(k in s for k in ["label", "value", "category"]):
                suggestions.append(EnhancePromptSuggestion(**s))
        
        return EnhancePromptResponse(
            original_query=request.query,
            enhanced_query=result.get("enhanced_query", request.query),
            explanation=result.get("explanation", ""),
            suggestions=suggestions,
            confidence=min(1.0, max(0.0, float(result.get("confidence", 0.7))))
        )
    
    except Exception as e:
        logger.error(f"Prompt enhancement failed: {e}", exc_info=True)
        return EnhancePromptResponse(
            original_query=request.query,
            enhanced_query=request.query,
            explanation="Não foi possível analisar o prompt",
            suggestions=[],
            confidence=0.0
        )


# Sprint F.3 #25 canonical-fix: VacancyGoalRequest moved to api/v1/candidate_search/calibration.py
from app.api.v1.candidate_search.calibration import VacancyGoalRequest  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: VacancyGoalResponse moved to api/v1/candidate_search/calibration.py
from app.api.v1.candidate_search.calibration import VacancyGoalResponse  # noqa: F401  (re-export for backward compat)



