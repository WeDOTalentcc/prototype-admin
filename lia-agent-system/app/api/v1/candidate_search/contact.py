"""
Contact reveal (reveal/cost, reveal) and filter suggestions routes.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    CandidateSearchResultDTO,
    PearchSearchRequest,
    PearchService,
    SearchType,
    get_contact_enrichment_service,
    get_db,
    get_pearch_service,
)
from app.domains.sourcing.services.contact_enrichment_service import ContactEnrichmentService
from app.domains.candidates.repositories.candidate_filter_repository import CandidateFilterRepository
from app.shared.types import WeDoBaseModel

router = APIRouter()

import logging as _contact_log
from app.shared.security.require_company_id import require_company_id
_contact_logger = _contact_log.getLogger(__name__)


async def _track_pearch_reveal(
    db: AsyncSession,
    company_id: str | None,
    operation: str,
    credits_consumed: int,
    success: bool,
    result_status: str = "success",
) -> None:
    resolved_company_id = company_id or "unattributed"
    try:
        from app.domains.billing.services.consumption_tracking_service import ConsumptionTrackingService
        await ConsumptionTrackingService.record_pearch_call(
            db=db,
            company_id=resolved_company_id,
            user_id=None,
            operation=operation,
            credits_consumed=credits_consumed,
            success=success,
            result_status=result_status,
        )
    except Exception as e:
        _contact_logger.error("[Reveal] Failed to track pearch reveal: %s", e)
        # Defence-in-depth: if tracking poisoned the session (e.g. RLS rejection),
        # rollback so the caller's session is not stuck in PendingRollbackError.
        # Without this, get_db() teardown raises PendingRollbackError → HTTP 500
        # overrides the actual success/failure response.
        try:
            await db.rollback()
        except Exception:
            pass

class RevealType(str):
    EMAIL = "email"
    PHONE = "phone"


class RevealContactRequest(WeDoBaseModel):
    """Request para revelar email ou telefone de um candidato Pearch."""
    candidate_id: str = Field(..., description="ID do candidato (docid do Pearch)")
    candidate_name: str = Field(..., description="Nome do candidato para busca")
    reveal_type: str = Field(..., description="Tipo: 'email' ou 'phone'", pattern="^(email|phone)$")
    linkedin_slug: str | None = Field(None, description="LinkedIn slug para busca mais precisa")


class RevealContactResponse(BaseModel):
    """Response com dados de contato revelados."""
    success: bool
    candidate_id: str
    reveal_type: str
    
    # Dados revelados
    email: str | None = None
    emails: list[str] = Field(default_factory=list)
    phone: str | None = None
    phones: list[str] = Field(default_factory=list)
    
    # Custos
    credits_used: int = 0
    credits_remaining: int | None = None
    
    # Mensagem
    message: str = ""


class RevealCostEstimate(BaseModel):
    """Estimativa de custo para reveal."""
    reveal_type: str
    credits_required: int
    description: str


@router.get("/reveal/cost", response_model=None)
async def get_reveal_cost(
    reveal_type: str = Query(..., description="Tipo: 'email' ou 'phone'"), 
company_id: str = Depends(require_company_id)) -> RevealCostEstimate:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Retorna o custo para revelar email ou telefone.
    
    Fluxo: Apify primeiro ($0.01) → Pearch como fallback (2/14 créditos).
    """
    if reveal_type == "email":
        return RevealCostEstimate(
            reveal_type="email",
            credits_required=0,
            description="Revelar email via Apify ($0.01) — fallback Pearch: 2 créditos"
        )
    elif reveal_type == "phone":
        return RevealCostEstimate(
            reveal_type="phone",
            credits_required=0,
            description="Revelar telefone via Apify ($0.01) — fallback Pearch: 14 créditos"
        )
    else:
        raise HTTPException(status_code=400, detail="reveal_type deve ser 'email' ou 'phone'")


@router.post("/reveal", response_model=RevealContactResponse)
async def reveal_contact(
    request: RevealContactRequest,
    db: AsyncSession = Depends(get_db),
    pearch_svc: PearchService = Depends(get_pearch_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Revela email ou telefone de um candidato.
    
    Fluxo:
    1. Tenta Apify primeiro ($0.01/candidato) via LinkedIn URL
    2. Se Apify falhar, usa Pearch como fallback (2/14 créditos)
    """
    import logging as _log
    _logger = _log.getLogger(__name__)
    
    try:
        enrichment_svc = get_contact_enrichment_service()

        from uuid import UUID as _UUID
        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )

        candidate_repo = CandidateRepository(db)

        linkedin_url = None
        if request.linkedin_slug:
            linkedin_url = f"https://www.linkedin.com/in/{request.linkedin_slug}"

        cand_uuid = None
        try:
            cand_uuid = _UUID(request.candidate_id)
        except (ValueError, AttributeError):
            pass

        # ADR-001: LinkedIn URL resolution via CandidateRepository
        if not linkedin_url and cand_uuid:
            try:
                db_url = await candidate_repo.get_linkedin_url_by_id(cand_uuid)
                if db_url:
                    linkedin_url = db_url
                    _logger.info("[Reveal] Resolved LinkedIn URL from DB for %s", cand_uuid)
            except Exception as e:
                _logger.warning("[Reveal] DB LinkedIn URL lookup failed: %s", e)

        # ADR-001: docid → UUID mapping via CandidateRepository
        if not cand_uuid and request.linkedin_slug:
            try:
                local_cand = await candidate_repo.find_by_linkedin_slug(request.linkedin_slug)
                if local_cand:
                    cand_uuid = local_cand.id
                    _logger.info("[Reveal] Resolved docid %s to UUID %s via LinkedIn slug", request.candidate_id, cand_uuid)
            except Exception as lookup_err:
                _logger.warning("[Reveal] LinkedIn lookup failed: %s", lookup_err)

        # ADR-001: company_id recovery — JWT company_id is canonical default.
        # Pearch docid candidates never have a UUID (cand_uuid=None), so the old
        # pattern of initializing _company_id=None left tracking with
        # company_id='unattributed', violating RLS on external_api_consumption
        # and poisoning the SQLAlchemy session for the whole request.
        # Fix: seed _company_id from the JWT claim; only override with DB lookup
        # when a better (per-candidate) value is available.
        _company_id = company_id  # JWT company_id — fail-closed multi-tenancy
        if cand_uuid:
            try:
                _db_company_id = await candidate_repo.get_company_id_from_credits_usage(cand_uuid)
                if _db_company_id:
                    _company_id = _db_company_id
            except Exception:
                pass

        if linkedin_url:
            _logger.info("[Reveal] Trying Apify first for %s", request.candidate_id)
            
            if cand_uuid:
                try:
                    apify_result = await enrichment_svc.enrich_candidate_contact(
                        db=db,
                        candidate_id=cand_uuid,
                        linkedin_url=linkedin_url,
                        force=True,
                        company_id=_company_id,
                    )
                    
                    if apify_result.get("success") and apify_result.get("has_contact"):
                        email = apify_result.get("email")
                        phone = apify_result.get("phone")
                        
                        if request.reveal_type == "email" and email:
                            return RevealContactResponse(
                                success=True,
                                candidate_id=request.candidate_id,
                                reveal_type="email",
                                email=email,
                                emails=[email],
                                credits_used=0,
                                message="Email revelado via Apify ($0.01)",
                            )
                        elif request.reveal_type == "phone" and phone:
                            return RevealContactResponse(
                                success=True,
                                candidate_id=request.candidate_id,
                                reveal_type="phone",
                                phone=phone,
                                phones=[phone],
                                credits_used=0,
                                message="Telefone revelado via Apify ($0.01)",
                            )
                except Exception as apify_err:
                    _logger.warning("[Reveal] Apify via DB failed, falling back: %s", apify_err)
            else:
                _logger.info("[Reveal] Non-UUID candidate %s, trying Apify direct scrape", request.candidate_id)
                try:
                    apify_result = await enrichment_svc.enrich_by_linkedin_url(linkedin_url, company_id=_company_id)
                    if apify_result.get("success") and apify_result.get("has_contact"):
                        email = apify_result.get("email")
                        phone = apify_result.get("phone")

                        if request.reveal_type == "email" and email:
                            return RevealContactResponse(
                                success=True,
                                candidate_id=request.candidate_id,
                                reveal_type="email",
                                email=email,
                                emails=[email],
                                credits_used=0,
                                message="Email revelado via Apify ($0.01)",
                            )
                        elif request.reveal_type == "phone" and phone:
                            return RevealContactResponse(
                                success=True,
                                candidate_id=request.candidate_id,
                                reveal_type="phone",
                                phone=phone,
                                phones=[phone],
                                credits_used=0,
                                message="Telefone revelado via Apify ($0.01)",
                            )
                except Exception as apify_err:
                    _logger.warning("[Reveal] Apify direct scrape failed: %s", apify_err)
        
        _logger.info("[Reveal] Falling back to Pearch for %s", request.candidate_id)
        
        search_query = request.candidate_name
        if request.linkedin_slug:
            search_query = f"{request.candidate_name} linkedin:{request.linkedin_slug}"
        
        show_emails = request.reveal_type == "email"
        show_phone_numbers = request.reveal_type == "phone"
        
        pearch_request = PearchSearchRequest(
            query=search_query,
            type=SearchType.FAST,
            limit=1,
            insights=False,
            profile_scoring=False,
            high_freshness=False,
            require_emails=show_emails,
            show_emails=show_emails,
            require_phone_numbers=show_phone_numbers,
            show_phone_numbers=show_phone_numbers
        )
        
        result = await pearch_svc.search_candidates(pearch_request, timeout=30, company_id=_company_id)
        
        if not result.search_results:
            await _track_pearch_reveal(db, _company_id, f"reveal_{request.reveal_type}", 0, False, result_status="no_contact")
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
                await _track_pearch_reveal(db, _company_id, "reveal_email", 0, False, result_status="no_contact")
                return RevealContactResponse(
                    success=False,
                    candidate_id=request.candidate_id,
                    reveal_type=request.reveal_type,
                    message="Este candidato não possui email disponível",
                    credits_used=0,
                    credits_remaining=result.credits_remaining
                )
            
            await _track_pearch_reveal(db, _company_id, "reveal_email", 2, True)
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
                await _track_pearch_reveal(db, _company_id, "reveal_phone", 0, False, result_status="no_contact")
                return RevealContactResponse(
                    success=False,
                    candidate_id=request.candidate_id,
                    reveal_type=request.reveal_type,
                    message="Este candidato não possui telefone disponível",
                    credits_used=0,
                    credits_remaining=result.credits_remaining
                )
            
            await _track_pearch_reveal(db, _company_id, "reveal_phone", 14, True)
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


# ============================================================================
# BULK REVEAL ENDPOINT - Reveal de múltiplos candidatos em paralelo
# ============================================================================

class BulkRevealRequest(WeDoBaseModel):
    """Request para revelar contatos de múltiplos candidatos em paralelo."""
    items: list[RevealContactRequest] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Lista de candidatos para revelar (máx 50)",
    )


class BulkRevealResponse(BaseModel):
    """Response com resultados do reveal em bulk."""
    results: list[RevealContactResponse]
    revealed_count: int
    unavailable_count: int
    timeout_count: int = 0


@router.post("/reveal/bulk", response_model=BulkRevealResponse)
async def reveal_contact_bulk(
    request: BulkRevealRequest,
    db: AsyncSession = Depends(get_db),
    pearch_svc: PearchService = Depends(get_pearch_service),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime
    """
    Revela contatos de múltiplos candidatos em paralelo.

    Usa asyncio.gather com semaphore(3) para limitar concorrência.
    Timeout de 35s por candidato para evitar travamento do frontend.
    """
    semaphore = asyncio.Semaphore(3)

    async def _reveal_one(item: RevealContactRequest) -> RevealContactResponse:
        async with semaphore:
            try:
                from app.core.database import async_session_factory
                async with async_session_factory() as db_local:
                    return await asyncio.wait_for(
                        reveal_contact(
                            request=item,
                            db=db_local,
                            pearch_svc=pearch_svc,
                            company_id=company_id,
                        ),
                        timeout=35.0,
                    )
            except asyncio.TimeoutError:
                _contact_logger.warning(
                    "[RevealBulk] Timeout for candidate %s after 35s", item.candidate_id
                )
                return RevealContactResponse(
                    success=False,
                    candidate_id=item.candidate_id,
                    reveal_type=item.reveal_type,
                    message="Timeout: contato não disponível no momento. Tente individualmente.",
                )
            except Exception as exc:
                _contact_logger.error(
                    "[RevealBulk] Error for candidate %s: %s", item.candidate_id, exc, exc_info=True
                )
                return RevealContactResponse(
                    success=False,
                    candidate_id=item.candidate_id,
                    reveal_type=item.reveal_type,
                    message="Não foi possível revelar o contato. Tente individualmente.",
                )

    results = await asyncio.gather(*[_reveal_one(item) for item in request.items])

    revealed_count = sum(1 for r in results if r.success)
    unavailable_count = sum(
        1 for r in results if not r.success and "timeout" not in r.message.lower()
    )
    timeout_count = sum(
        1 for r in results if not r.success and "timeout" in r.message.lower()
    )

    return BulkRevealResponse(
        results=list(results),
        revealed_count=revealed_count,
        unavailable_count=unavailable_count,
        timeout_count=timeout_count,
    )


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
    global_count: int | None = Field(None, description="Contagem estimada na busca global (se disponível)")
    aliases: list[str] = Field(default_factory=list, description="Variações do mesmo termo")
    source: str = Field("local", description="Fonte da sugestão: local ou global")


class FilterSuggestionsRequest(WeDoBaseModel):
    """Request para buscar sugestões de filtros."""
    category: str = Field(..., description="Categoria: titles, companies, skills, universities, fields_of_study, locations, countries, industries, languages")
    query: str = Field(..., description="Termo de busca parcial")
    limit: int = Field(10, ge=1, le=50, description="Número máximo de sugestões")
    include_global: bool = Field(False, description="Incluir estimativa global (assíncrono)")


class FilterSuggestionsResponse(BaseModel):
    """Response com sugestões de filtros."""
    category: str
    query: str
    suggestions: list[FilterSuggestion]
    has_more: bool = Field(False, description="Indica se há mais resultados")
    global_pending: bool = Field(False, description="Indica se contagem global está sendo processada")


@router.post("/suggestions", response_model=FilterSuggestionsResponse)
async def get_filter_suggestions(
    request: FilterSuggestionsRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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

    query_lower = request.query.lower().strip()
    suggestions: list[FilterSuggestion] = []
    
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
        _filter_repo = CandidateFilterRepository(db)
        if request.category == "titles":
            rows = await _filter_repo.get_titles(query_lower, request.limit)
            
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
            rows = await _filter_repo.get_companies(query_lower, request.limit)
            
            for row in rows:
                suggestions.append(FilterSuggestion(
                    value=row[0],
                    label=row[0],
                    local_count=row[1]
                ))
        
        elif request.category == "skills":
            rows = await _filter_repo.get_skills(query_lower, request.limit)
            
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
            rows = await _filter_repo.get_locations(query_lower, request.limit)
            
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
            rows = await _filter_repo.get_countries(query_lower, request.limit)
            
            for row in rows:
                suggestions.append(FilterSuggestion(
                    value=row[0],
                    label=row[0],
                    local_count=row[1]
                ))
        
        elif request.category == "universities":
            rows = await _filter_repo.get_universities(query_lower, request.limit)
            
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
            rows = await _filter_repo.get_languages(query_lower, request.limit)
            
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

# Sprint F.3 #25 canonical-fix: ArchetypeDTO moved to api/v1/candidate_search/archetypes.py
from app.api.v1.candidate_search.archetypes import ArchetypeDTO  # noqa: F401  (re-export for backward compat)


class ArchetypeListResponse(BaseModel):
    """Response for listing archetypes."""
    archetypes: list[ArchetypeDTO]
    total: int
    default_count: int


# Sprint F.3 #25 canonical-fix: ArchetypeCreateRequest moved to api/v1/candidate_search/archetypes.py
from app.api.v1.candidate_search.archetypes import ArchetypeCreateRequest  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: ArchetypeUpdateRequest moved to api/v1/candidate_search/archetypes.py
from app.api.v1.candidate_search.archetypes import ArchetypeUpdateRequest  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: ArchetypeSearchRequest moved to api/v1/candidate_search/archetypes.py
from app.api.v1.candidate_search.archetypes import ArchetypeSearchRequest  # noqa: F401  (re-export for backward compat)


class ArchetypeSearchResultDTO(CandidateSearchResultDTO):
    """Extended search result with LIA score."""
    lia_score: float | None = None
    lia_reasoning: str | None = None
    lia_breakdown: dict | None = None
    lia_strengths: list[str] = Field(default_factory=list)
    lia_concerns: list[str] = Field(default_factory=list)


# Sprint F.3 #25 canonical-fix: ArchetypeSearchResponse moved to api/v1/candidate_search/archetypes.py
from app.api.v1.candidate_search.archetypes import ArchetypeSearchResponse  # noqa: F401  (re-export for backward compat)
from app.shared.errors import LIAError

