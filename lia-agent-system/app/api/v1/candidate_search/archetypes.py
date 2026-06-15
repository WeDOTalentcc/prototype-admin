"""
Archetype CRUD, generation (from-search, from-job, from-description), and search routes.
"""
from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    ArchetypeFromSearchCreate,
    ArchetypeFromSearchResponse,
    ArchetypeResponse,
    CandidateSearchResultDTO,
    HybridSearchRequest,
    PearchService,
    SearchType,
    User,
    build_archetype_from_search,
    enrich_and_filter_candidates,
    extract_tags_from_search_spec,
    get_current_user_or_demo,
    get_db,
    get_pearch_service,
    logger,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

class ArchetypeFromDescriptionRequest(WeDoBaseModel):
    """Request to generate an archetype from a text description."""
    description: str = Field(..., min_length=20, description="Descrição textual do perfil ideal")
    name: str | None = Field(None, description="Nome personalizado para o arquétipo")
    emoji: str = Field("🎯", max_length=10)




router = APIRouter()
# FairnessGuard — bloqueio de queries discriminatórias (LGPD/CLT canonical)
from app.shared.compliance.fairness_guard import FairnessGuard as _FairnessGuard
_fairness_guard = _FairnessGuard()


class ArchetypeDTO(BaseModel):
    """DTO for archetype data in API responses."""
    id: str
    name: str
    description: str | None = None
    emoji: str = "🎯"
    query: str
    filters: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    industry: str | None = None
    seniority: str | None = None
    is_default: bool = False
    is_active: bool = True
    usage_count: int = 0
    created_at: str | None = None


class ArchetypeListResponse(BaseModel):
    """Response for listing archetypes."""
    archetypes: list[ArchetypeDTO]
    total: int
    default_count: int


class ArchetypeCreateRequest(WeDoBaseModel):
    """Request to create a new archetype."""
    id: str | None = Field(None, description="ID único, gerado automaticamente se não fornecido")
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    emoji: str = Field("🎯", max_length=10)
    query: str = Field(..., min_length=5)
    filters: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    industry: str | None = None
    seniority: str | None = None


class ArchetypeUpdateRequest(WeDoBaseModel):
    """Request to update an existing archetype."""
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None
    emoji: str | None = Field(None, max_length=10)
    query: str | None = Field(None, min_length=5)
    filters: dict | None = None
    tags: list[str] | None = None
    industry: str | None = None
    seniority: str | None = None
    is_active: bool | None = None


class ArchetypeSearchRequest(WeDoBaseModel):
    """Request to search using an archetype."""
    search_local: bool = Field(True, description="Buscar no banco local")
    search_pearch: bool = Field(True, description="Buscar na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo de busca (sempre fast)")
    local_limit: int = Field(20, ge=1, le=100)
    pearch_limit: int = Field(15, ge=0, le=50)
    show_emails: bool = False
    show_phone_numbers: bool = False
    calculate_lia_score: bool = Field(True, description="Calcular score LIA para cada candidato")


class ArchetypeSearchResultDTO(CandidateSearchResultDTO):
    """Extended search result with LIA score."""
    lia_score: float | None = None
    lia_reasoning: str | None = None
    lia_breakdown: dict | None = None
    lia_strengths: list[str] = Field(default_factory=list)
    lia_concerns: list[str] = Field(default_factory=list)


class ArchetypeSearchResponse(BaseModel):
    """Response for archetype-based search."""
    archetype: ArchetypeDTO
    query: str
    thread_id: str | None = None
    candidates: list[ArchetypeSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: int | None = None
    search_time_seconds: float | None = None
    warning_message: str | None = None


@router.get("/archetypes", response_model=ArchetypeListResponse)
async def list_archetypes(
    include_inactive: bool = Query(False, description="Incluir arquétipos inativos"),
    industry: str | None = Query(None, description="Filtrar por indústria"),
    seniority: str | None = Query(None, description="Filtrar por senioridade"),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Lista todos os arquétipos disponíveis.
    
    Arquétipos são templates de busca pré-configurados que facilitam
    encontrar perfis específicos sem precisar construir queries complexas.
    """
    from sqlalchemy import select

    from app.models.archetype import SearchArchetype, seed_default_archetypes
    
    try:
        # Seed default archetypes if needed
        created = await seed_default_archetypes(db)
        if created > 0:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Seeded {created} default archetypes")
        
        # Build query — canonical multi-tenancy:
        # marketplace archetypes (company_id IS NULL, publicos, lia_models/archetype.py:43-44)
        # + private archetypes do tenant atual (company_id == company_id do JWT)
        # explicit filter > TENANT-EXEMPT marker (previne private leak entre tenants P1)
        from sqlalchemy import or_
        query = select(SearchArchetype).where(
            or_(
                SearchArchetype.company_id == company_id,
                SearchArchetype.company_id.is_(None),  # marketplace publico
            )
        )
        
        if not include_inactive:
            query = query.where(SearchArchetype.is_active)
        
        if industry:
            query = query.where(SearchArchetype.industry == industry)
        
        if seniority:
            query = query.where(SearchArchetype.seniority == seniority)
        
        query = query.order_by(SearchArchetype.is_default.desc(), SearchArchetype.usage_count.desc())
        
        result = await db.execute(query)
        archetypes = result.scalars().all()
        
        archetype_dtos = []
        default_count = 0
        
        for arch in archetypes:
            if arch.is_default:
                default_count += 1
            
            archetype_dtos.append(ArchetypeDTO(
                id=arch.id,
                name=arch.name,
                description=arch.description,
                emoji=arch.emoji or "🎯",
                query=arch.query,
                filters=arch.filters or {},
                tags=arch.tags or [],
                industry=arch.industry,
                seniority=arch.seniority,
                is_default=arch.is_default,
                is_active=arch.is_active,
                usage_count=arch.usage_count or 0,
                created_at=arch.created_at.isoformat() if arch.created_at else None
            ))
        
        return ArchetypeListResponse(
            archetypes=archetype_dtos,
            total=len(archetype_dtos),
            default_count=default_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error listing archetypes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/archetypes", response_model=ArchetypeDTO)
async def create_archetype(
    request: ArchetypeCreateRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cria um novo arquétipo personalizado.
    
    Arquétipos criados pelo usuário não são marcados como 'default'
    e podem ser modificados ou excluídos posteriormente.
    """
    import uuid as uuid_lib

    from sqlalchemy import select

    from app.models.archetype import SearchArchetype
    
    try:
        # Generate ID if not provided
        archetype_id = request.id or f"custom-{uuid_lib.uuid4().hex[:8]}"
        
        # Check if ID already exists
        existing = await db.execute(
            # TENANT-EXEMPT: SearchArchetype.company_id NULLABLE para marketplace templates publicos (lia_models/archetype.py:43-44); endpoint require_company_id valida JWT pra contexto cliente; sensor AST nao infere nullable+marketplace
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Archetype with ID '{archetype_id}' already exists")
        
        # Create archetype
        archetype = SearchArchetype(
            id=archetype_id,
            name=request.name,
            description=request.description,
            emoji=request.emoji,
            query=request.query,
            filters=request.filters,
            tags=request.tags,
            industry=request.industry,
            seniority=request.seniority,
            is_default=False,
            is_active=True,
            usage_count=0
        )
        
        db.add(archetype)
        await db.flush()
        await db.refresh(archetype)
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error creating archetype: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/archetypes/from-search", response_model=ArchetypeFromSearchResponse)
async def create_archetype_from_search(
    data: ArchetypeFromSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Cria um novo arquétipo a partir de um SearchSpec.
    
    Extrai automaticamente tags, filtros e query do search_spec fornecido,
    criando um template reutilizável de busca.
    
    Args:
        data: SearchSpec + nome + descrição + emoji opcional
        
    Returns:
        O arquétipo criado com as tags extraídas
    """
    
    try:
        company_id = current_user.company_id or None
        user_id = str(current_user.id) if current_user.id else None
        if not company_id:
            raise HTTPException(status_code=400, detail="company_id is required to create an archetype")
        
        extracted_tags = extract_tags_from_search_spec(data.search_spec)
        
        archetype = build_archetype_from_search(
            search_spec=data.search_spec,
            name=data.name,
            description=data.description,
            emoji=data.emoji,
            company_id=company_id,
            user_id=user_id
        )
        
        db.add(archetype)
        await db.flush()
        await db.refresh(archetype)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Created archetype '{archetype.name}' (id={archetype.id}) from search spec")
        
        return ArchetypeFromSearchResponse(
            archetype=ArchetypeResponse(
                id=archetype.id,
                name=archetype.name,
                description=archetype.description,
                emoji=archetype.emoji or "🎯",
                query=archetype.query,
                filters=archetype.filters or {},
                tags=archetype.tags or [],
                industry=archetype.industry,
                seniority=archetype.seniority,
                is_default=archetype.is_default,
                is_active=archetype.is_active,
                usage_count=archetype.usage_count or 0,
                company_id=archetype.company_id,
                created_by=archetype.created_by,
                created_at=archetype.created_at,
                updated_at=archetype.updated_at
            ),
            extracted_tags=extracted_tags,
            message=f"Arquétipo '{archetype.name}' criado com sucesso com {len(extracted_tags)} tags extraídas"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error creating archetype from search: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ARCHETYPE AUTO-GENERATION ENDPOINTS
# ============================================================================

class ClosedJobSuggestion(BaseModel):
    """Sugestão de vaga fechada para criar arquétipo."""
    job_id: str
    title: str
    department: str | None = None
    seniority: str | None = None
    closed_at: str | None = None
    hired_count: int = 0
    suggested_archetype_name: str
    suggested_emoji: str = "🎯"


class ClosedJobSuggestionsResponse(BaseModel):
    """Response com sugestões de vagas fechadas."""
    suggestions: list[ClosedJobSuggestion] = Field(default_factory=list)
    total: int = 0


@router.get("/archetypes/suggestions/closed-jobs", response_model=ClosedJobSuggestionsResponse)
async def get_closed_job_suggestions(
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Lista sugestões de vagas fechadas para criar arquétipos.
    
    Retorna as últimas vagas concluídas com contratação bem-sucedida,
    sugerindo nomes e emojis para os arquétipos.
    """
    from sqlalchemy import desc, or_, select

    from app.models.job_vacancy import JobVacancy
    
    try:
        result = await db.execute(
            select(JobVacancy)
            .where(
                or_(
                    JobVacancy.status == "Concluída",
                    JobVacancy.status == "Fechada",
                    JobVacancy.closed_at.isnot(None)
                ),
                JobVacancy.company_id == company_id,
            )
            .order_by(desc(JobVacancy.closed_at), desc(JobVacancy.updated_at))
            .limit(limit)
        )
        jobs = result.scalars().all()
        
        suggestions = []
        emoji_map = {
            "tecnologia": "💻", "ti": "💻", "tech": "💻", "desenvolvimento": "🚀",
            "financeiro": "💰", "finanças": "📊", "contabilidade": "📑",
            "rh": "👥", "recursos humanos": "🤝", "people": "👥",
            "comercial": "🎯", "vendas": "💼", "sales": "📈",
            "marketing": "📣", "comunicação": "📢",
            "operações": "⚙️", "logística": "🚚", "supply": "📦",
            "jurídico": "⚖️", "legal": "📜",
            "produto": "🎨", "design": "✨", "ux": "🎨"
        }
        
        for job in jobs:
            dept_lower = (job.department or "").lower()
            emoji = "🎯"
            for key, value in emoji_map.items():
                if key in dept_lower or key in (job.title or "").lower():
                    emoji = value
                    break
            
            seniority_prefix = ""
            if job.seniority_level:
                seniority_prefix = f"{job.seniority_level} "
            
            suggestions.append(ClosedJobSuggestion(
                job_id=str(job.id),
                title=job.title,
                department=job.department,
                seniority=job.seniority_level,
                closed_at=job.closed_at.isoformat() if job.closed_at else None,
                hired_count=1,
                suggested_archetype_name=f"{seniority_prefix}{job.title}",
                suggested_emoji=emoji
            ))
        
        return ClosedJobSuggestionsResponse(
            suggestions=suggestions,
            total=len(suggestions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting closed job suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/archetypes/from-job/{job_id}", response_model=ArchetypeDTO)
async def create_archetype_from_job(
    job_id: str,
    custom_name: str | None = Query(None, description="Nome customizado para o arquétipo"),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Cria um arquétipo automaticamente a partir de uma vaga fechada.
    
    Extrai título, senioridade, requisitos técnicos, competências
    comportamentais e outras informações da vaga para criar um
    arquétipo reutilizável.
    """
    import uuid as uuid_lib

    from sqlalchemy import select

    from app.models.archetype import SearchArchetype
    from app.models.job_vacancy import JobVacancy
    
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job vacancy '{job_id}' not found")
        
        skills = []
        if job.technical_requirements:
            for req in job.technical_requirements:
                if isinstance(req, dict) and req.get("technology"):
                    skills.append(req["technology"])
        if job.requirements:
            skills.extend(job.requirements[:5])
        
        behavioral = []
        if job.behavioral_competencies:
            for comp in job.behavioral_competencies:
                if isinstance(comp, dict) and comp.get("competency"):
                    behavioral.append(comp["competency"])
        
        query_parts = []
        if job.seniority_level:
            query_parts.append(job.seniority_level)
        query_parts.append(job.title)
        if skills[:3]:
            query_parts.append(f"com experiência em {', '.join(skills[:3])}")
        if job.location:
            query_parts.append(f"em {job.location}")
        
        query = " ".join(query_parts)
        
        emoji_map = {
            "tecnologia": "💻", "ti": "💻", "tech": "💻", "dev": "🚀",
            "financeiro": "💰", "finanças": "📊", "fp&a": "📈",
            "rh": "👥", "recursos humanos": "🤝", "recruiter": "🎯",
            "comercial": "🎯", "vendas": "💼", "sales": "📈",
            "marketing": "📣", "produto": "🎨", "design": "✨",
            "operações": "⚙️", "logística": "🚚", "compras": "🛒"
        }
        
        emoji = "🎯"
        search_text = f"{job.department or ''} {job.title}".lower()
        for key, value in emoji_map.items():
            if key in search_text:
                emoji = value
                break
        
        seniority_map = {
            "júnior": "junior", "junior": "junior", "jr": "junior",
            "pleno": "pleno", "mid": "pleno",
            "sênior": "senior", "senior": "senior", "sr": "senior",
            "especialista": "senior", "lead": "senior", "líder": "senior"
        }
        seniority = None
        if job.seniority_level:
            seniority = seniority_map.get(job.seniority_level.lower(), "pleno")
        
        industry = None
        dept_lower = (job.department or "").lower()
        title_lower = (job.title or "").lower()
        if any(k in dept_lower or k in title_lower for k in ["tech", "ti", "dev", "software", "dados"]):
            industry = "tecnologia"
        elif any(k in dept_lower or k in title_lower for k in ["financ", "contab", "fiscal", "tribut"]):
            industry = "financas"
        elif any(k in dept_lower or k in title_lower for k in ["rh", "recursos", "people", "gente"]):
            industry = "rh"
        elif any(k in dept_lower or k in title_lower for k in ["compras", "supply", "logist", "procurement"]):
            industry = "compras"
        elif any(k in dept_lower or k in title_lower for k in ["comercial", "vendas", "sales"]):
            industry = "comercial"
        
        archetype_name = custom_name or f"{job.seniority_level or ''} {job.title}".strip()
        archetype_id = f"job-{uuid_lib.uuid4().hex[:8]}"
        
        archetype = SearchArchetype(
            id=archetype_id,
            name=archetype_name,
            description=f"Arquétipo baseado na vaga: {job.title}. {job.description[:200] if job.description else ''}",
            emoji=emoji,
            query=query,
            filters={
                "seniority": seniority,
                "skills": skills[:10],
                "behavioral_competencies": behavioral[:5],
                "location": job.location,
                "work_model": job.work_model
            },
            tags=skills[:5] + behavioral[:3],
            industry=industry,
            seniority=seniority,
            is_default=False,
            is_active=True,
            usage_count=0
        )
        
        db.add(archetype)
        await db.flush()
        await db.refresh(archetype)
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error creating archetype from job: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/archetypes/{archetype_id}", response_model=ArchetypeDTO)
async def get_archetype(
    archetype_id: str,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Obtém detalhes de um arquétipo específico."""
    from sqlalchemy import select

    from app.models.archetype import SearchArchetype
    
    try:
        result = await db.execute(
            # TENANT-EXEMPT: SearchArchetype.company_id NULLABLE para marketplace templates publicos (lia_models/archetype.py:43-44); endpoint require_company_id valida JWT pra contexto cliente; sensor AST nao infere nullable+marketplace
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error getting archetype: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/archetypes/{archetype_id}", response_model=None)
async def delete_archetype(
    archetype_id: str,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Deleta um arquétipo personalizado.
    
    Arquétipos padrão do sistema não podem ser deletados.
    """
    from sqlalchemy import delete, select

    from app.models.archetype import SearchArchetype
    
    try:
        result = await db.execute(
            # TENANT-EXEMPT: SearchArchetype.company_id NULLABLE para marketplace templates publicos (lia_models/archetype.py:43-44); endpoint require_company_id valida JWT pra contexto cliente; sensor AST nao infere nullable+marketplace
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        if archetype.is_default:
            raise HTTPException(
                status_code=403, 
                detail="Cannot delete default system archetypes. You can deactivate them instead."
            )
        
        await db.execute(
            # TENANT-EXEMPT: SearchArchetype.company_id NULLABLE para marketplace templates publicos (lia_models/archetype.py:43-44); endpoint require_company_id valida JWT pra contexto cliente; sensor AST nao infere nullable+marketplace
            delete(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        
        return {"message": f"Archetype '{archetype_id}' deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error deleting archetype: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/archetypes/{archetype_id}", response_model=ArchetypeDTO)
async def update_archetype(
    archetype_id: str,
    request: ArchetypeUpdateRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Atualiza um arquétipo existente.
    
    Arquétipos padrão do sistema podem ter apenas alguns campos atualizados.
    """
    from sqlalchemy import select

    from app.models.archetype import SearchArchetype
    
    try:
        result = await db.execute(
            # TENANT-EXEMPT: SearchArchetype.company_id NULLABLE para marketplace templates publicos (lia_models/archetype.py:43-44); endpoint require_company_id valida JWT pra contexto cliente; sensor AST nao infere nullable+marketplace
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        # Default archetypes can now be fully edited by users
        
        if request.name is not None:
            archetype.name = request.name
        if request.description is not None:
            archetype.description = request.description
        if request.emoji is not None:
            archetype.emoji = request.emoji
        if request.query is not None:
            archetype.query = request.query
        if request.filters is not None:
            archetype.filters = request.filters
        if request.tags is not None:
            archetype.tags = request.tags
        if request.industry is not None:
            archetype.industry = request.industry
        if request.seniority is not None:
            archetype.seniority = request.seniority
        if request.is_active is not None:
            archetype.is_active = request.is_active
        
        await db.flush()
        await db.refresh(archetype)
        
        return ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=archetype.usage_count or 0,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error updating archetype: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/archetypes/{archetype_id}/search", response_model=ArchetypeSearchResponse)
async def search_by_archetype(
    archetype_id: str,
    request: ArchetypeSearchRequest,
    db: AsyncSession = Depends(get_db)
,
    pearch_svc: PearchService = Depends(get_pearch_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Executa busca de candidatos usando um arquétipo específico.
    
    O arquétipo define a query e filtros pré-configurados.
    Opcionalmente calcula o score LIA para cada candidato encontrado.
    """
    import logging

    from sqlalchemy import select, update

    from app.models.archetype import SearchArchetype
    from app.shared.services.lia_score_service import lia_score_service
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get archetype
        result = await db.execute(
            # TENANT-EXEMPT: SearchArchetype.company_id NULLABLE para marketplace templates publicos (lia_models/archetype.py:43-44); endpoint require_company_id valida JWT pra contexto cliente; sensor AST nao infere nullable+marketplace
            select(SearchArchetype).where(SearchArchetype.id == archetype_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            raise HTTPException(status_code=404, detail=f"Archetype '{archetype_id}' not found")
        
        if not archetype.is_active:
            raise HTTPException(status_code=400, detail=f"Archetype '{archetype_id}' is inactive")
        
        # Increment usage count
        await db.execute(
            # TENANT-EXEMPT: SearchArchetype.company_id NULLABLE para marketplace templates publicos (lia_models/archetype.py:43-44); endpoint require_company_id valida JWT pra contexto cliente; sensor AST nao infere nullable+marketplace
            update(SearchArchetype)
            .where(SearchArchetype.id == archetype_id)
            .values(usage_count=(archetype.usage_count or 0) + 1)
        )
        
        # Build hybrid search request
        hybrid_request = HybridSearchRequest(
            query=archetype.query,
            search_local_first=request.search_local,
            include_pearch=request.search_pearch,
            pearch_type=SearchType.FAST,
            local_limit=request.local_limit,
            pearch_limit=request.pearch_limit,
            show_emails=request.show_emails,
            show_phone_numbers=request.show_phone_numbers
        )
        
        # Execute search
        search_result = await pearch_svc.hybrid_search(db, hybrid_request)
        
        # Prepare criteria for LIA score calculation
        criteria = {
            "query": archetype.query,
            "filters": archetype.filters or {}
        }
        
        # Convert results and calculate LIA scores
        candidates = []
        
        for profile in search_result.local_candidates:
            candidate_dto = ArchetypeSearchResultDTO(
                id=profile.docid or "",
                name=profile.get_full_name(),
                first_name=profile.first_name,
                last_name=profile.last_name,
                picture_url=profile.picture_url,
                headline=profile.headline,
                current_title=profile.current_title,
                current_company=profile.current_company,
                location=profile.location,
                total_experience_years=profile.total_experience_years,
                skills=profile.skills[:10] if profile.skills else [],
                score=profile.get_score_percentage(),
                match_summary=profile.insights.overall_summary if profile.insights else profile.match_reasoning,
                linkedin_url=profile.get_linkedin_url(),
                has_email=profile.has_emails or False,
                has_phone=profile.has_phone_numbers or False,
                email=profile.best_personal_email or (profile.emails[0] if profile.emails else None),
                phone=profile.phone_numbers[0] if profile.phone_numbers else None,
                source="local",
                is_open_to_work=profile.is_opentowork
            )
            
            # Calculate LIA score if requested
            if request.calculate_lia_score:
                try:
                    candidate_data = {
                        "skills": profile.skills,
                        "total_experience_years": profile.total_experience_years,
                        "seniority_level": getattr(profile, 'seniority', None),
                        "location": profile.location,
                        "current_title": profile.current_title,
                        "is_opentowork": profile.is_opentowork,
                    }
                    lia_result = lia_score_service.calculate_score(candidate_data, criteria, industry=archetype.industry)
                    candidate_dto.lia_score = lia_result.score
                    candidate_dto.lia_reasoning = lia_result.reasoning
                    candidate_dto.lia_breakdown = lia_result.breakdown.to_dict()
                    candidate_dto.lia_strengths = lia_result.strengths
                    candidate_dto.lia_concerns = lia_result.concerns
                except Exception as e:
                    logger.warning(f"Failed to calculate LIA score: {e}")
            
            candidates.append(candidate_dto)
        
        for profile in search_result.pearch_candidates:
            candidate_dto = ArchetypeSearchResultDTO(
                id=profile.docid or "",
                name=profile.get_full_name(),
                first_name=profile.first_name,
                last_name=profile.last_name,
                picture_url=profile.picture_url,
                headline=profile.headline,
                current_title=profile.current_title,
                current_company=profile.current_company,
                location=profile.location,
                total_experience_years=profile.total_experience_years,
                skills=profile.skills[:10] if profile.skills else [],
                score=profile.get_score_percentage(),
                match_summary=profile.insights.overall_summary if profile.insights else profile.match_reasoning,
                linkedin_url=profile.get_linkedin_url(),
                has_email=profile.has_emails or False,
                has_phone=profile.has_phone_numbers or False,
                email=profile.best_personal_email or (profile.emails[0] if profile.emails else None),
                phone=profile.phone_numbers[0] if profile.phone_numbers else None,
                source="pearch",
                is_open_to_work=profile.is_opentowork
            )
            
            # Calculate LIA score if requested
            if request.calculate_lia_score:
                try:
                    candidate_data = {
                        "skills": profile.skills,
                        "total_experience_years": profile.total_experience_years,
                        "seniority_level": getattr(profile, 'seniority', None),
                        "location": profile.location,
                        "current_title": profile.current_title,
                        "is_opentowork": profile.is_opentowork,
                    }
                    lia_result = lia_score_service.calculate_score(candidate_data, criteria, industry=archetype.industry)
                    candidate_dto.lia_score = lia_result.score
                    candidate_dto.lia_reasoning = lia_result.reasoning
                    candidate_dto.lia_breakdown = lia_result.breakdown.to_dict()
                    candidate_dto.lia_strengths = lia_result.strengths
                    candidate_dto.lia_concerns = lia_result.concerns
                except Exception as e:
                    logger.warning(f"Failed to calculate LIA score: {e}")
            
            candidates.append(candidate_dto)
        
        candidates = await enrich_and_filter_candidates(db, candidates, company_id=company_id)
        if request.calculate_lia_score:
            candidates.sort(key=lambda x: x.lia_score or 0, reverse=True)

            # WT-2022 P0.C: LGPD Art. 20 — log uma decisao por candidato rankeado.
            # AITransparencyPanel le e exibe ao recrutador/candidato pra direito de
            # revisao. fail-safe (no-op em DB error). Limita pra top 50 pra evitar
            # custo db excessivo em buscas muito grandes (>1k candidatos).
            try:
                from app.shared.services.automated_decision_logger import (
                    log_automated_decision,
                    PROTECTED_CRITERIA_PT,
                )
                _archetype_id = str(getattr(archetype, "id", "")) or "unknown"
                _top_n_for_log = candidates[:50]
                for _rank_pos, _c in enumerate(_top_n_for_log, start=1):
                    try:
                        _c_id = getattr(_c, "id", None)
                        _c_score = getattr(_c, "lia_score", None)
                        _c_reasoning = getattr(_c, "lia_reasoning", None) or ""
                        _explanation = (
                            "Candidato classificado posicao " + str(_rank_pos)
                            + " com LIA score " + str(_c_score)
                            + ". Reasoning: " + _c_reasoning[:500]
                        )
                        _confidence = (float(_c_score) / 100.0) if _c_score else None
                        await log_automated_decision(
                            db=db,
                            company_id=str(company_id),
                            candidate_id=str(_c_id) if _c_id else None,
                            job_id=_archetype_id,
                            decision_type="candidate_ranking_lia_score",
                            ai_model_used="lia_score_service",
                            explanation_text=_explanation,
                            criteria_used=["skills_match", "experience_years", "seniority_match", "location_match", "title_match"],
                            criteria_ignored=PROTECTED_CRITERIA_PT,
                            confidence_score=_confidence,
                            review_eligible=True,
                            extra_metadata={"archetype_id": _archetype_id, "rank_position": _rank_pos, "source": getattr(_c, "source", None)},
                        )
                    except ValueError:
                        raise
                    except Exception as _adl_loop_exc:
                        logger.debug("[archetypes] log_automated_decision per-candidate skipped: %s", _adl_loop_exc)
            except Exception as _adl_exc:
                logger.warning("[archetypes] log_automated_decision batch failed (fail-safe): %s", _adl_exc)

        archetype_dto = ArchetypeDTO(
            id=archetype.id,
            name=archetype.name,
            description=archetype.description,
            emoji=archetype.emoji or "🎯",
            query=archetype.query,
            filters=archetype.filters or {},
            tags=archetype.tags or [],
            industry=archetype.industry,
            seniority=archetype.seniority,
            is_default=archetype.is_default,
            is_active=archetype.is_active,
            usage_count=(archetype.usage_count or 0) + 1,
            created_at=archetype.created_at.isoformat() if archetype.created_at else None
        )
        
        return ArchetypeSearchResponse(
            archetype=archetype_dto,
            query=archetype.query,
            thread_id=search_result.thread_id,
            candidates=candidates,
            local_count=search_result.local_count,
            pearch_count=search_result.pearch_count,
            total_count=len(candidates),
            credits_remaining=search_result.pearch_credits_remaining,
            search_time_seconds=(search_result.local_search_time or 0) + (search_result.pearch_search_time or 0),
            warning_message=search_result.warning_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error searching by archetype: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ARCHETYPE GENERATION FROM JOB VACANCY - Create archetype from closed job
# ============================================================================

class ArchetypeGenerationRequest(WeDoBaseModel):
    """Request to generate an archetype from a closed job vacancy."""
    job_id: int = Field(..., description="ID da vaga fechada")
    name: str | None = Field(None, description="Nome personalizado para o arquétipo (opcional, será gerado se não fornecido)")
    emoji: str = Field("🎯", max_length=10, description="Emoji para o arquétipo")


class ArchetypeGenerationResponse(BaseModel):
    """Response with generated archetype."""
    success: bool
    archetype: ArchetypeDTO | None = None
    job_title: str
    hired_candidate_name: str | None = None
    message: str


@router.post("/archetypes/from-job", response_model=ArchetypeGenerationResponse)
async def generate_archetype_from_job(
    request: ArchetypeGenerationRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Gera um arquétipo de busca a partir de uma vaga fechada com candidato contratado.
    
    Usa IA (Claude) para analisar:
    - Descrição da vaga (JD)
    - Perfil do candidato contratado
    - Requisitos técnicos e comportamentais
    
    E gerar:
    - Query otimizada para buscar candidatos similares
    - Filtros pré-configurados
    - Tags relevantes
    """
    import json
    import uuid as uuid_lib

    from sqlalchemy import select

    from app.models.archetype import SearchArchetype
    from app.models.job_vacancy import JobVacancy
    from app.shared.providers.llm_factory import get_provider_for_tenant

    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.id == request.job_id, JobVacancy.company_id == company_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {request.job_id}")
        
        if job.status not in ["Concluída", "Fechada", "Preenchida"]:
            raise HTTPException(
                status_code=400, 
                detail=f"A vaga deve estar concluída para gerar arquétipo. Status atual: {job.status}"
            )
        
        hired_data = job.additional_data.get("hired_candidate") if job.additional_data else None
        hired_name = hired_data.get("name") if hired_data else None
        
        jd_info = {
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "work_model": job.work_model,
            "seniority_level": job.seniority_level,
            "description": job.description,
            "requirements": job.requirements or [],
            "technical_requirements": job.technical_requirements or [],
            "behavioral_competencies": job.behavioral_competencies or [],
            "languages": job.languages or [],
        }
        
        candidate_info = None
        if hired_data:
            candidate_info = {
                "name": hired_data.get("name"),
                "current_title": hired_data.get("current_title"),
                "years_experience": hired_data.get("years_experience"),
                "skills": hired_data.get("skills", []),
                "location": hired_data.get("location"),
                "seniority": hired_data.get("seniority"),
            }
        
        container = get_provider_for_tenant()
        
        prompt = f"""Você é um especialista em recrutamento. Analise a vaga e o perfil do candidato contratado para criar um arquétipo de busca.

DADOS DA VAGA:
{json.dumps(jd_info, ensure_ascii=False, indent=2)}

{"PERFIL DO CANDIDATO CONTRATADO:" if candidate_info else ""}
{json.dumps(candidate_info, ensure_ascii=False, indent=2) if candidate_info else "Não disponível"}

Gere um arquétipo de busca no formato JSON com:
1. name: Nome curto e descritivo do arquétipo (ex: "Product Manager B2B SaaS")
2. description: Descrição de 1-2 linhas do perfil ideal
3. query: Query em linguagem natural para buscar candidatos similares (incluir cargo, experiência, skills principais)
4. filters: Objeto com filtros:
   - seniority: "junior" | "pleno" | "senior" | "lead"
   - experience_years_min: número
   - skills: array de skills principais (máximo 5)
5. tags: Array de tags relevantes (máximo 5)
6. industry: Indústria/setor (ex: "tecnologia", "financas", "rh", "compras")
7. seniority: Senioridade principal do perfil

Responda APENAS com o JSON, sem explicações adicionais."""

        response_text = await container.generate_with_fallback(prompt, agent_type="ArchetypeGenerationAgent")
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        archetype_data = json.loads(response_text)
        
        archetype_id = f"custom-{uuid_lib.uuid4().hex[:8]}"
        name = request.name or archetype_data.get("name", f"Similar a {job.title}")
        
        new_archetype = SearchArchetype(
            id=archetype_id,
            name=name,
            description=archetype_data.get("description"),
            emoji=request.emoji,
            query=archetype_data.get("query", ""),
            filters=archetype_data.get("filters", {}),
            tags=archetype_data.get("tags", []),
            industry=archetype_data.get("industry"),
            seniority=archetype_data.get("seniority"),
            is_default=False,
            is_active=True,
            usage_count=0,
            company_id=job.company_id,
            created_by="lia-system"
        )
        
        db.add(new_archetype)
        await db.flush()
        await db.refresh(new_archetype)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Created archetype '{name}' from job '{job.title}'")
        
        return ArchetypeGenerationResponse(
            success=True,
            archetype=ArchetypeDTO(
                id=new_archetype.id,
                name=new_archetype.name,
                description=new_archetype.description,
                emoji=new_archetype.emoji or "🎯",
                query=new_archetype.query,
                filters=new_archetype.filters or {},
                tags=new_archetype.tags or [],
                industry=new_archetype.industry,
                seniority=new_archetype.seniority,
                is_default=False,
                is_active=True,
                usage_count=0,
                created_at=new_archetype.created_at.isoformat() if new_archetype.created_at else None
            ),
            job_title=job.title,
            hired_candidate_name=hired_name,
            message=f"Arquétipo '{name}' criado com sucesso a partir da vaga '{job.title}'"
        )
    
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise HTTPException(status_code=500, detail="Falha ao processar resposta da IA")
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error generating archetype from job: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/archetypes/from-description", response_model=ArchetypeGenerationResponse)
async def generate_archetype_from_description(
    request: ArchetypeFromDescriptionRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Gera um arquétipo de busca a partir de uma descrição textual livre.
    
    Útil quando o usuário descreve o perfil ideal em linguagem natural.
    """
    import json
    import uuid as uuid_lib

    from app.models.archetype import SearchArchetype
    from app.shared.providers.llm_factory import get_provider_for_tenant

    try:
        # LGPD/CLT fairness guard: bloqueia descrições discriminatórias antes de chamar LLM
        _fg_result = _fairness_guard.check(request.description)
        if _fg_result.is_blocked:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "fairness_blocked",
                    "fairness_blocked": True,
                    "educational_message": _fg_result.educational_message,
                    "category": _fg_result.category,
                    "blocked_terms": _fg_result.blocked_terms or [],
                },
            )
        container = get_provider_for_tenant()
        
        prompt = f"""Você é um especialista em recrutamento. Analise a descrição do perfil ideal e crie um arquétipo de busca.

DESCRIÇÃO DO PERFIL IDEAL:
{request.description}

Gere um arquétipo de busca no formato JSON com:
1. name: Nome curto e descritivo do arquétipo (ex: "Product Manager B2B SaaS")
2. description: Descrição de 1-2 linhas do perfil ideal
3. query: Query em linguagem natural para buscar candidatos similares (incluir cargo, experiência, skills principais)
4. filters: Objeto com filtros:
   - seniority: "junior" | "pleno" | "senior" | "lead"
   - experience_years_min: número
   - skills: array de skills principais (máximo 5)
5. tags: Array de tags relevantes (máximo 5)
6. industry: Indústria/setor (ex: "tecnologia", "financas", "rh", "compras")
7. seniority: Senioridade principal do perfil

Responda APENAS com o JSON, sem explicações adicionais."""

        response_text = await container.generate_with_fallback(prompt, agent_type="ArchetypeGenerationAgent")
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        archetype_data = json.loads(response_text)
        
        archetype_id = f"custom-{uuid_lib.uuid4().hex[:8]}"
        name = request.name or archetype_data.get("name", "Perfil Personalizado")
        
        new_archetype = SearchArchetype(
            id=archetype_id,
            name=name,
            description=archetype_data.get("description"),
            emoji=request.emoji,
            query=archetype_data.get("query", ""),
            filters=archetype_data.get("filters", {}),
            tags=archetype_data.get("tags", []),
            industry=archetype_data.get("industry"),
            seniority=archetype_data.get("seniority"),
            is_default=False,
            is_active=True,
            usage_count=0,
            company_id=None,
            created_by="lia-system"
        )
        
        db.add(new_archetype)
        await db.flush()
        await db.refresh(new_archetype)
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Created archetype '{name}' from description")
        
        return ArchetypeGenerationResponse(
            success=True,
            archetype=ArchetypeDTO(
                id=new_archetype.id,
                name=new_archetype.name,
                description=new_archetype.description,
                emoji=new_archetype.emoji or "🎯",
                query=new_archetype.query,
                filters=new_archetype.filters or {},
                tags=new_archetype.tags or [],
                industry=new_archetype.industry,
                seniority=new_archetype.seniority,
                is_default=False,
                is_active=True,
                usage_count=0,
                created_at=new_archetype.created_at.isoformat() if new_archetype.created_at else None
            ),
            job_title="Descrição Personalizada",
            hired_candidate_name=None,
            message=f"Arquétipo '{name}' criado com sucesso"
        )
    
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response: {e}")
        raise HTTPException(status_code=500, detail="Falha ao processar resposta da IA")
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error generating archetype from description: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


class ClosedJobSuggestionDTO(BaseModel):
    """Suggestion for creating archetype from closed job."""
    id: int
    title: str
    department: str | None = None
    closed_at: str | None = None
    hired_candidate_name: str | None = None
    has_hired_data: bool = False


class ClosedJobsSuggestionsResponse(BaseModel):
    """Response with list of closed jobs that can be used to create archetypes."""
    jobs: list[ClosedJobSuggestionDTO]
    total: int


@router.get("/archetypes/suggestions", response_model=ClosedJobsSuggestionsResponse)
async def get_archetype_suggestions(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Lista vagas fechadas que podem ser usadas para criar arquétipos.
    Prioriza vagas com dados do candidato contratado.
    """
    from sqlalchemy import select

    from app.models.job_vacancy import JobVacancy

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py
    
    try:
        result = await db.execute(
            select(JobVacancy)
            .where(
                JobVacancy.status.in_(["Concluída", "Fechada", "Preenchida"]),
                JobVacancy.company_id == company_id,
            )
            .order_by(JobVacancy.closed_at.desc().nulls_last())
            .limit(limit)
        )
        jobs = result.scalars().all()
        
        suggestions = []
        for job in jobs:
            hired_data = job.additional_data.get("hired_candidate") if job.additional_data else None
            suggestions.append(ClosedJobSuggestionDTO(
                id=job.id,
                title=job.title,
                department=job.department,
                closed_at=job.closed_at.isoformat() if job.closed_at else None,
                hired_candidate_name=hired_data.get("name") if hired_data else None,
                has_hired_data=bool(hired_data)
            ))
        
        suggestions.sort(key=lambda x: (not x.has_hired_data, x.closed_at or ""))
        
        return ClosedJobsSuggestionsResponse(
            jobs=suggestions,
            total=len(suggestions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error fetching archetype suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CV-BASED SEARCH ENDPOINT - Search similar candidates from CV upload
# ============================================================================

class CVSearchResultDTO(BaseModel):
    """Result from CV-based search."""
    parsed_cv: dict
    query_generated: str
    candidates: list[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: int | None = None
    search_time_seconds: float | None = None
    extracted_skills: list[str] = Field(default_factory=list)
    extracted_title: str | None = None

