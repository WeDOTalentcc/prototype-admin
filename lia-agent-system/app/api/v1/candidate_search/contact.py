"""
Contact reveal (reveal/cost, reveal) and filter suggestions routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ._shared import (
    logger, get_db, get_current_user_or_demo, get_user_company_id, assert_resource_ownership,
    User, ImportUser, cv_parser_service, search_analytics_service,
    extract_tags_from_search_spec, build_archetype_from_search,
    ArchetypeFromSearchCreate, ArchetypeFromSearchResponse, ArchetypeResponse,
    rubric_evaluation_service, JobRequirement, JobRequirementCreate, RequirementPriorityEnum,
    pearch_service, HybridSearchRequest, PearchSearchRequest, SearchType,
    _normalize_priority, _normalize_name, _generate_fingerprint,
    _get_job_requirements, _get_match_label, _build_candidate_data_from_dto,
    _evaluate_candidates_with_rubrics, _recruiter_agent,
    ExperienceDTO, EducationDTO, LanguageDTO, CandidateSearchResultDTO, SearchResponseDTO,
    SearchRequestDTO, ImportCandidateExperienceDTO, ImportCandidateDTO,
    ImportCandidatesRequest, IdMapping, ImportCandidatesResponse,
    CreditEstimateDTO, EvaluateForJobRequest, EvaluateForJobResult, EvaluateForJobResponse,
)

router = APIRouter()

class RevealType(str):
    EMAIL = "email"
    PHONE = "phone"


class RevealContactRequest(BaseModel):
    """Request para revelar email ou telefone de um candidato Pearch."""
    candidate_id: str = Field(..., description="ID do candidato (docid do Pearch)")
    candidate_name: str = Field(..., description="Nome do candidato para busca")
    reveal_type: str = Field(..., description="Tipo: 'email' ou 'phone'", pattern="^(email|phone)$")
    linkedin_slug: Optional[str] = Field(None, description="LinkedIn slug para busca mais precisa")


class RevealContactResponse(BaseModel):
    """Response com dados de contato revelados."""
    success: bool
    candidate_id: str
    reveal_type: str
    
    # Dados revelados
    email: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    phones: List[str] = Field(default_factory=list)
    
    # Custos
    credits_used: int = 0
    credits_remaining: Optional[int] = None
    
    # Mensagem
    message: str = ""


class RevealCostEstimate(BaseModel):
    """Estimativa de custo para reveal."""
    reveal_type: str
    credits_required: int
    description: str


@router.get("/reveal/cost")
async def get_reveal_cost(
    reveal_type: str = Query(..., description="Tipo: 'email' ou 'phone'")
) -> RevealCostEstimate:
    """
    Retorna o custo em créditos para revelar email ou telefone.
    
    Custos:
    - Email: 2 créditos
    - Telefone: 14 créditos
    """
    if reveal_type == "email":
        return RevealCostEstimate(
            reveal_type="email",
            credits_required=2,
            description="Revelar email do candidato"
        )
    elif reveal_type == "phone":
        return RevealCostEstimate(
            reveal_type="phone",
            credits_required=14,
            description="Revelar telefone do candidato"
        )
    else:
        raise HTTPException(status_code=400, detail="reveal_type deve ser 'email' ou 'phone'")


@router.post("/reveal", response_model=RevealContactResponse)
async def reveal_contact(
    request: RevealContactRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Revela email ou telefone de um candidato Pearch.
    
    Custos:
    - Email: 2 créditos por candidato (só cobra se tiver email)
    - Telefone: 14 créditos por candidato (só cobra se tiver telefone)
    
    Fluxo:
    1. Faz busca específica no Pearch com show_emails ou show_phone_numbers
    2. Retorna os dados de contato encontrados
    3. Opcionalmente atualiza o candidato no banco local
    """
    try:
        # Configura busca específica
        search_query = request.candidate_name
        if request.linkedin_slug:
            search_query = f"{request.candidate_name} linkedin:{request.linkedin_slug}"
        
        # Define flags baseado no tipo de reveal
        show_emails = request.reveal_type == "email"
        show_phone_numbers = request.reveal_type == "phone"
        
        # Cria request para Pearch
        pearch_request = PearchSearchRequest(
            query=search_query,
            type=SearchType.FAST,  # Usar fast para reveal individual
            limit=1,
            insights=False,
            profile_scoring=False,
            high_freshness=False,
            require_emails=show_emails,
            show_emails=show_emails,
            require_phone_numbers=show_phone_numbers,
            show_phone_numbers=show_phone_numbers
        )
        
        # Executa busca
        result = await pearch_service.search_candidates(pearch_request, timeout=30)
        
        if not result.search_results:
            return RevealContactResponse(
                success=False,
                candidate_id=request.candidate_id,
                reveal_type=request.reveal_type,
                message=f"Candidato não encontrado ou sem {request.reveal_type} disponível",
                credits_remaining=result.credits_remaining
            )
        
        # Pega primeiro resultado
        profile = result.search_results[0].profile
        
        if request.reveal_type == "email":
            emails = profile.emails or []
            primary_email = profile.best_personal_email or profile.best_business_email or (emails[0] if emails else None)
            
            if not emails and not primary_email:
                return RevealContactResponse(
                    success=False,
                    candidate_id=request.candidate_id,
                    reveal_type=request.reveal_type,
                    message="Este candidato não possui email disponível",
                    credits_used=0,
                    credits_remaining=result.credits_remaining
                )
            
            return RevealContactResponse(
                success=True,
                candidate_id=request.candidate_id,
                reveal_type=request.reveal_type,
                email=primary_email,
                emails=emails,
                credits_used=2,
                credits_remaining=result.credits_remaining,
                message="Email revelado com sucesso"
            )
        
        elif request.reveal_type == "phone":
            phones = profile.phone_numbers or []
            primary_phone = phones[0] if phones else None
            
            if not phones:
                return RevealContactResponse(
                    success=False,
                    candidate_id=request.candidate_id,
                    reveal_type=request.reveal_type,
                    message="Este candidato não possui telefone disponível",
                    credits_used=0,
                    credits_remaining=result.credits_remaining
                )
            
            return RevealContactResponse(
                success=True,
                candidate_id=request.candidate_id,
                reveal_type=request.reveal_type,
                phone=primary_phone,
                phones=phones,
                credits_used=14,
                credits_remaining=result.credits_remaining,
                message="Telefone revelado com sucesso"
            )
        
        return RevealContactResponse(
            success=False,
            candidate_id=request.candidate_id,
            reveal_type=request.reveal_type,
            message="Tipo de reveal inválido"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao revelar contato: {str(e)}")


# ============================================================================
# FILTER SUGGESTIONS ENDPOINT - Autocomplete com contagens
# ============================================================================

class SuggestionCategory(str):
    """Categorias disponíveis para sugestões."""
    TITLES = "titles"
    COMPANIES = "companies"
    SKILLS = "skills"
    UNIVERSITIES = "universities"
    FIELDS_OF_STUDY = "fields_of_study"
    LOCATIONS = "locations"
    COUNTRIES = "countries"
    INDUSTRIES = "industries"
    LANGUAGES = "languages"


class FilterSuggestion(BaseModel):
    """Uma sugestão de filtro com contagem de candidatos."""
    value: str = Field(..., description="Valor canônico para o filtro")
    label: str = Field(..., description="Label para exibição")
    local_count: int = Field(0, description="Contagem de candidatos na base local")
    global_count: Optional[int] = Field(None, description="Contagem estimada na busca global (se disponível)")
    aliases: List[str] = Field(default_factory=list, description="Variações do mesmo termo")
    source: str = Field("local", description="Fonte da sugestão: local ou global")


class FilterSuggestionsRequest(BaseModel):
    """Request para buscar sugestões de filtros."""
    category: str = Field(..., description="Categoria: titles, companies, skills, universities, fields_of_study, locations, countries, industries, languages")
    query: str = Field(..., description="Termo de busca parcial")
    limit: int = Field(10, ge=1, le=50, description="Número máximo de sugestões")
    include_global: bool = Field(False, description="Incluir estimativa global (assíncrono)")


class FilterSuggestionsResponse(BaseModel):
    """Response com sugestões de filtros."""
    category: str
    query: str
    suggestions: List[FilterSuggestion]
    has_more: bool = Field(False, description="Indica se há mais resultados")
    global_pending: bool = Field(False, description="Indica se contagem global está sendo processada")


@router.post("/suggestions", response_model=FilterSuggestionsResponse)
async def get_filter_suggestions(
    request: FilterSuggestionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna sugestões de filtros com contagem de candidatos.
    
    Suporta categorias:
    - titles: Cargos/títulos profissionais
    - companies: Empresas
    - skills: Habilidades técnicas
    - universities: Universidades
    - fields_of_study: Áreas de estudo
    - locations: Cidades/Estados
    - countries: Países
    - industries: Setores/Indústrias
    - languages: Idiomas
    
    Retorna contagem local imediata. Contagem global pode ser solicitada
    via include_global=true (processada de forma assíncrona).
    """
    from sqlalchemy import text, func
    from app.models.candidate import Candidate
    from sqlalchemy.future import select
    from collections import Counter
    
    query_lower = request.query.lower().strip()
    suggestions: List[FilterSuggestion] = []
    
    try:
        # Definir aliases comuns para termos de busca
        COMMON_ALIASES = {
            "titles": {
                "product manager": ["gerente de produto", "pm", "head de produto"],
                "gerente de produto": ["product manager", "pm"],
                "software engineer": ["engenheiro de software", "desenvolvedor", "developer"],
                "desenvolvedor": ["developer", "programador", "software engineer"],
                "tech lead": ["líder técnico", "technical lead"],
                "data scientist": ["cientista de dados"],
                "ux designer": ["designer ux", "product designer"],
                "devops": ["devops engineer", "sre", "site reliability engineer"],
                "backend": ["backend developer", "desenvolvedor backend"],
                "frontend": ["frontend developer", "desenvolvedor frontend"],
                "fullstack": ["full stack", "desenvolvedor fullstack"],
            },
            "skills": {
                "python": ["py"],
                "javascript": ["js", "ecmascript"],
                "typescript": ["ts"],
                "react": ["reactjs", "react.js"],
                "node": ["nodejs", "node.js"],
                "aws": ["amazon web services"],
                "gcp": ["google cloud", "google cloud platform"],
                "azure": ["microsoft azure"],
                "sql": ["mysql", "postgresql", "postgres"],
                "machine learning": ["ml", "aprendizado de máquina"],
            },
            "locations": {
                "sp": ["são paulo", "sao paulo"],
                "são paulo": ["sp", "sao paulo"],
                "rj": ["rio de janeiro"],
                "rio de janeiro": ["rj"],
                "bh": ["belo horizonte"],
                "belo horizonte": ["bh"],
                "poa": ["porto alegre"],
            },
            "languages": {
                "english": ["inglês", "ingles"],
                "inglês": ["english", "ingles"],
                "spanish": ["espanhol"],
                "espanhol": ["spanish"],
                "portuguese": ["português", "portugues"],
                "português": ["portuguese", "portugues"],
            }
        }
        
        # Buscar dados do banco baseado na categoria
        if request.category == "titles":
            # Buscar títulos únicos com contagem
            result = await db.execute(
                text("""
                    SELECT current_title, COUNT(*) as count
                    FROM candidates
                    WHERE current_title IS NOT NULL 
                    AND current_title != ''
                    AND is_active = true
                    AND LOWER(current_title) LIKE :query
                    GROUP BY current_title
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit * 2}
            )
            rows = result.fetchall()
            
            # Agrupar títulos similares
            title_counts = {}
            for row in rows:
                title = row[0]
                count = row[1]
                title_lower = title.lower()
                
                # Verificar se é alias de outro já encontrado
                found_canonical = None
                for canonical in title_counts:
                    if title_lower == canonical.lower():
                        found_canonical = canonical
                        break
                    aliases = COMMON_ALIASES.get("titles", {}).get(canonical.lower(), [])
                    if title_lower in [a.lower() for a in aliases]:
                        found_canonical = canonical
                        break
                
                if found_canonical:
                    title_counts[found_canonical]["count"] += count
                    if title not in title_counts[found_canonical]["aliases"]:
                        title_counts[found_canonical]["aliases"].append(title)
                else:
                    title_counts[title] = {
                        "count": count,
                        "aliases": COMMON_ALIASES.get("titles", {}).get(title_lower, [])
                    }
            
            # Criar sugestões
            for title, data in sorted(title_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:request.limit]:
                suggestions.append(FilterSuggestion(
                    value=title,
                    label=title,
                    local_count=data["count"],
                    aliases=data["aliases"][:3]
                ))
        
        elif request.category == "companies":
            result = await db.execute(
                text("""
                    SELECT current_company, COUNT(*) as count
                    FROM candidates
                    WHERE current_company IS NOT NULL 
                    AND current_company != ''
                    AND is_active = true
                    AND LOWER(current_company) LIKE :query
                    GROUP BY current_company
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                suggestions.append(FilterSuggestion(
                    value=row[0],
                    label=row[0],
                    local_count=row[1]
                ))
        
        elif request.category == "skills":
            # Buscar skills do array technical_skills
            result = await db.execute(
                text("""
                    SELECT skill, COUNT(*) as count
                    FROM (
                        SELECT UNNEST(technical_skills) as skill
                        FROM candidates
                        WHERE is_active = true
                        AND technical_skills IS NOT NULL
                    ) skills_expanded
                    WHERE LOWER(skill) LIKE :query
                    GROUP BY skill
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                skill = row[0]
                skill_lower = skill.lower()
                aliases = COMMON_ALIASES.get("skills", {}).get(skill_lower, [])
                suggestions.append(FilterSuggestion(
                    value=skill,
                    label=skill,
                    local_count=row[1],
                    aliases=aliases[:3]
                ))
        
        elif request.category == "locations":
            # Combinar cidade e estado
            result = await db.execute(
                text("""
                    SELECT 
                        CASE 
                            WHEN location_state IS NOT NULL AND location_state != ''
                            THEN CONCAT(location_city, ', ', location_state)
                            ELSE location_city
                        END as location,
                        COUNT(*) as count
                    FROM candidates
                    WHERE location_city IS NOT NULL 
                    AND location_city != ''
                    AND is_active = true
                    AND (
                        LOWER(location_city) LIKE :query
                        OR LOWER(location_state) LIKE :query
                    )
                    GROUP BY location_city, location_state
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                location = row[0]
                location_lower = (location or "").lower()
                aliases = []
                for key, vals in COMMON_ALIASES.get("locations", {}).items():
                    if key in location_lower or location_lower in key:
                        aliases.extend(vals)
                
                suggestions.append(FilterSuggestion(
                    value=location or "",
                    label=location or "",
                    local_count=row[1],
                    aliases=aliases[:3]
                ))
        
        elif request.category == "countries":
            result = await db.execute(
                text("""
                    SELECT location_country, COUNT(*) as count
                    FROM candidates
                    WHERE location_country IS NOT NULL 
                    AND location_country != ''
                    AND is_active = true
                    AND LOWER(location_country) LIKE :query
                    GROUP BY location_country
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                suggestions.append(FilterSuggestion(
                    value=row[0],
                    label=row[0],
                    local_count=row[1]
                ))
        
        elif request.category == "universities":
            # Universities would be in additional_data or a dedicated field
            # For now, search in resume_text with common university patterns
            result = await db.execute(
                text("""
                    SELECT 
                        COALESCE(additional_data->>'university', 'Não especificado') as university,
                        COUNT(*) as count
                    FROM candidates
                    WHERE is_active = true
                    AND additional_data->>'university' IS NOT NULL
                    AND LOWER(additional_data->>'university') LIKE :query
                    GROUP BY additional_data->>'university'
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                if row[0] and row[0] != 'Não especificado':
                    suggestions.append(FilterSuggestion(
                        value=row[0],
                        label=row[0],
                        local_count=row[1]
                    ))
            
            # Se não encontrou, retornar universidades comuns como sugestão
            if not suggestions and query_lower:
                common_universities = [
                    "USP - Universidade de São Paulo",
                    "UNICAMP - Universidade Estadual de Campinas",
                    "UFRJ - Universidade Federal do Rio de Janeiro",
                    "UFMG - Universidade Federal de Minas Gerais",
                    "PUC-SP",
                    "PUC-RJ",
                    "FGV - Fundação Getúlio Vargas",
                    "UNESP",
                    "UFSC - Universidade Federal de Santa Catarina",
                    "UFRGS - Universidade Federal do Rio Grande do Sul"
                ]
                for uni in common_universities:
                    if query_lower in uni.lower():
                        suggestions.append(FilterSuggestion(
                            value=uni,
                            label=uni,
                            local_count=0,
                            source="suggested"
                        ))
                        if len(suggestions) >= request.limit:
                            break
        
        elif request.category == "languages":
            # Languages is a JSON field
            result = await db.execute(
                text("""
                    SELECT key as language, COUNT(*) as count
                    FROM candidates, jsonb_object_keys(COALESCE(languages, '{}'::jsonb)) as key
                    WHERE is_active = true
                    AND LOWER(key) LIKE :query
                    GROUP BY key
                    ORDER BY count DESC
                    LIMIT :limit
                """),
                {"query": f"%{query_lower}%", "limit": request.limit}
            )
            rows = result.fetchall()
            
            for row in rows:
                lang = row[0]
                lang_lower = lang.lower()
                aliases = COMMON_ALIASES.get("languages", {}).get(lang_lower, [])
                suggestions.append(FilterSuggestion(
                    value=lang,
                    label=lang,
                    local_count=row[1],
                    aliases=aliases[:3]
                ))
            
            # Se não encontrou, retornar idiomas comuns
            if not suggestions and query_lower:
                common_languages = ["Português", "Inglês", "Espanhol", "Francês", "Alemão", "Italiano", "Mandarim"]
                for lang in common_languages:
                    if query_lower in lang.lower():
                        aliases = COMMON_ALIASES.get("languages", {}).get(lang.lower(), [])
                        suggestions.append(FilterSuggestion(
                            value=lang,
                            label=lang,
                            local_count=0,
                            aliases=aliases[:3],
                            source="suggested"
                        ))
                        if len(suggestions) >= request.limit:
                            break
        
        elif request.category == "industries":
            # Industries from additional_data or inferred from company
            common_industries = [
                "Tecnologia",
                "Fintech",
                "E-commerce",
                "Saúde",
                "Educação",
                "Consultoria",
                "Varejo",
                "Agronegócio",
                "Logística",
                "Telecom",
                "Energia",
                "Startups",
                "Banking",
                "Insurance"
            ]
            
            for industry in common_industries:
                if query_lower in industry.lower():
                    suggestions.append(FilterSuggestion(
                        value=industry,
                        label=industry,
                        local_count=0,  # Would need industry mapping
                        source="suggested"
                    ))
                    if len(suggestions) >= request.limit:
                        break
        
        elif request.category == "fields_of_study":
            common_fields = [
                "Ciência da Computação",
                "Engenharia de Software",
                "Sistemas de Informação",
                "Administração",
                "Economia",
                "Engenharia Elétrica",
                "Engenharia Mecânica",
                "Engenharia de Produção",
                "Design",
                "Marketing",
                "Psicologia",
                "Direito",
                "Matemática",
                "Estatística",
                "Física"
            ]
            
            for field in common_fields:
                if query_lower in field.lower():
                    suggestions.append(FilterSuggestion(
                        value=field,
                        label=field,
                        local_count=0,
                        source="suggested"
                    ))
                    if len(suggestions) >= request.limit:
                        break
        
        return FilterSuggestionsResponse(
            category=request.category,
            query=request.query,
            suggestions=suggestions[:request.limit],
            has_more=len(suggestions) > request.limit,
            global_pending=request.include_global
        )
    
    except Exception as e:
        import traceback
        print(f"Error in get_filter_suggestions: {str(e)}")
        print(traceback.format_exc())
        # Return empty suggestions on error
        return FilterSuggestionsResponse(
            category=request.category,
            query=request.query,
            suggestions=[],
            has_more=False,
            global_pending=False
        )


# ============================================================================
# ARCHETYPE ENDPOINTS - Pre-configured search profiles
# ============================================================================

class ArchetypeDTO(BaseModel):
    """DTO for archetype data in API responses."""
    id: str
    name: str
    description: Optional[str] = None
    emoji: str = "🎯"
    query: str
    filters: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    seniority: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    created_at: Optional[str] = None


class ArchetypeListResponse(BaseModel):
    """Response for listing archetypes."""
    archetypes: List[ArchetypeDTO]
    total: int
    default_count: int


class ArchetypeCreateRequest(BaseModel):
    """Request to create a new archetype."""
    id: Optional[str] = Field(None, description="ID único, gerado automaticamente se não fornecido")
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    emoji: str = Field("🎯", max_length=10)
    query: str = Field(..., min_length=5)
    filters: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    seniority: Optional[str] = None


class ArchetypeUpdateRequest(BaseModel):
    """Request to update an existing archetype."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    emoji: Optional[str] = Field(None, max_length=10)
    query: Optional[str] = Field(None, min_length=5)
    filters: Optional[dict] = None
    tags: Optional[List[str]] = None
    industry: Optional[str] = None
    seniority: Optional[str] = None
    is_active: Optional[bool] = None


class ArchetypeSearchRequest(BaseModel):
    """Request to search using an archetype."""
    search_local: bool = Field(True, description="Buscar no banco local")
    search_pearch: bool = Field(True, description="Buscar na Pearch AI")
    pearch_type: str = Field("fast", pattern="^(fast|pro)$")
    local_limit: int = Field(20, ge=1, le=100)
    pearch_limit: int = Field(15, ge=1, le=50)
    show_emails: bool = False
    show_phone_numbers: bool = False
    calculate_lia_score: bool = Field(True, description="Calcular score LIA para cada candidato")


class ArchetypeSearchResultDTO(CandidateSearchResultDTO):
    """Extended search result with LIA score."""
    lia_score: Optional[float] = None
    lia_reasoning: Optional[str] = None
    lia_breakdown: Optional[dict] = None
    lia_strengths: List[str] = Field(default_factory=list)
    lia_concerns: List[str] = Field(default_factory=list)


class ArchetypeSearchResponse(BaseModel):
    """Response for archetype-based search."""
    archetype: ArchetypeDTO
    query: str
    thread_id: Optional[str] = None
    candidates: List[ArchetypeSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: Optional[int] = None
    search_time_seconds: Optional[float] = None
    warning_message: Optional[str] = None

