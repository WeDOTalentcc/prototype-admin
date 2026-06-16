"""Import and promote candidate routes."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    CVParserService,
    CandidateProfile,
    CandidateSearchResultDTO,
    EducationDTO,
    EvaluateForJobRequest,
    EvaluateForJobResponse,
    EvaluateForJobResult,
    ExperienceDTO,
    HybridSearchRequest,
    IdMapping,
    ImportCandidateDTO,
    ImportCandidateExperienceDTO,
    ImportCandidatesRequest,
    ImportCandidatesResponse,
    ImportUser,
    JobRequirement,
    JobRequirementCreate,
    LanguageDTO,
    PearchService,
    PearchSearchRequest,
    RubricEvaluationService,
    SearchRequestDTO,
    SearchResponseDTO,
    SearchType,
    User,
    _build_candidate_data_from_dto,
    _evaluate_candidates_with_rubrics,
    _generate_fingerprint,
    _get_job_requirements,
    _get_match_label,
    _normalize_name,
    _normalize_priority,
    assert_resource_ownership,
    get_current_user_or_demo,
    get_cv_parser_service,
    get_db,
    get_pearch_service,
    get_rubric_evaluation_service,
    get_user_company_id,
    logger,
    rubric_evaluation_service,
)
from app.domains.credits.services.credit_service import CreditService, get_credit_service

router = APIRouter()


def _normalize_name(name: str) -> str:
    """Normaliza nome para comparação e deduplicação."""
    import re
    import unicodedata
    normalized = unicodedata.normalize('NFKD', name.lower())
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    normalized = re.sub(r'[^a-z\s]', '', normalized)
    normalized = ' '.join(normalized.split())
    return normalized


def _generate_fingerprint(name: str, linkedin_url: str | None = None, email: str | None = None) -> str:
    """Gera hash de fingerprint para deduplicação."""
    import hashlib
    parts = [_normalize_name(name)]
    if linkedin_url:
        linkedin_id = linkedin_url.rstrip('/').split('/')[-1].lower()
        parts.append(f"li:{linkedin_id}")
    if email:
        parts.append(f"email:{email.lower()}")
    fingerprint_str = "|".join(sorted(parts))
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]


from app.auth.dependencies import assert_resource_ownership, get_current_user_or_demo, get_user_company_id
from app.auth.models import User as ImportUser
from app.shared.security.require_company_id import require_company_id


@router.post("/candidates/import", response_model=ImportCandidatesResponse)
async def import_pearch_candidates(
    request: ImportCandidatesRequest,
    current_user: ImportUser = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    """
    Importa candidatos da busca Pearch para a TABELA DE STAGING (external_candidate_profiles).
    
    ARQUITETURA DE STAGING:
    - Candidatos descobertos NÃO vão para a base principal (candidates)
    - Ficam em staging até serem explicitamente "promovidos" pelo recrutador
    - Evita poluição da base com candidatos sem contato revelado
    
    SEGURANÇA:
    - company_id derivado do usuário autenticado via get_current_user_or_demo
    - Multi-tenant isolation garantido via company_id do usuário
    
    Use POST /candidates/promote/{profile_id} para promover um candidato para a base principal.
    """
    import uuid as uuid_lib

    from sqlalchemy import or_, select

    from app.models.candidate import Candidate, ExternalCandidateProfile
    
    imported_ids = []
    skipped_ids = []
    skipped_no_email_ids = []
    updated_ids = []
    id_mappings = []
    company_id = get_user_company_id(current_user)
    
    try:
        for candidate_dto in request.candidates:
            fingerprint = _generate_fingerprint(
                candidate_dto.name,
                candidate_dto.linkedin_url,
                candidate_dto.email
            )
            
            existing_in_main = await db.execute(
                select(Candidate).where(
                    or_(
                        Candidate.pearch_profile_id == candidate_dto.pearch_id,
                        Candidate.linkedin_url == candidate_dto.linkedin_url
                    ),
                    Candidate.company_id == company_id,
                ).limit(1)
            )
            existing_candidate = existing_in_main.scalars().first()
            if existing_candidate:
                skipped_ids.append(candidate_dto.pearch_id)
                id_mappings.append(IdMapping(
                    pearch_id=candidate_dto.pearch_id,
                    local_id=str(existing_candidate.id)
                ))
                continue
            
            staging_filters = [ExternalCandidateProfile.source_profile_id == candidate_dto.pearch_id]
            if candidate_dto.linkedin_url:
                staging_filters.append(ExternalCandidateProfile.linkedin_url == candidate_dto.linkedin_url)
            staging_filters.append(ExternalCandidateProfile.fingerprint_hash == fingerprint)
            
            existing_in_staging = await db.execute(
                select(ExternalCandidateProfile).where(
                    ExternalCandidateProfile.company_id == company_id,
                    or_(*staging_filters)
                ).limit(1)
            )
            existing_profile = existing_in_staging.scalars().first()
            
            if existing_profile:
                updated = False
                if candidate_dto.email and not existing_profile.email:
                    existing_profile.email = candidate_dto.email
                    existing_profile.has_email = True
                    existing_profile.contact_revealed = True
                    updated = True
                if candidate_dto.phone and not existing_profile.phone:
                    existing_profile.phone = candidate_dto.phone
                    existing_profile.has_phone = True
                    existing_profile.contact_revealed = True
                    updated = True
                if updated:
                    updated_ids.append(candidate_dto.pearch_id)
                else:
                    skipped_ids.append(candidate_dto.pearch_id)
                id_mappings.append(IdMapping(
                    pearch_id=candidate_dto.pearch_id,
                    local_id=str(existing_profile.id)
                ))
                continue
            
            location_city, location_state, location_country = None, None, None
            if candidate_dto.location:
                parts = [p.strip() for p in candidate_dto.location.split(",")]
                if len(parts) >= 1:
                    location_city = parts[0]
                if len(parts) >= 2:
                    location_state = parts[1]
                if len(parts) >= 3:
                    location_country = parts[2]
            
            name_parts = candidate_dto.name.split(' ', 1)
            first_name = candidate_dto.first_name or (name_parts[0] if len(name_parts) > 0 else None)
            last_name = candidate_dto.last_name or (name_parts[1] if len(name_parts) > 1 else None)
            
            experiences_snapshot = []
            for exp in candidate_dto.experiences:
                experiences_snapshot.append({
                    "company_name": exp.company_name,
                    "company_linkedin_url": exp.company_linkedin_url,
                    "company_domain": exp.company_domain,
                    "title": exp.title,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "duration_years": exp.duration_years,
                    "is_current": exp.is_current,
                    "description": exp.description,
                    "location": exp.location,
                    "industries": exp.industries or [],
                    "company_size": exp.company_size,
                    "company_size_range": exp.company_size_range,
                    "technologies": exp.technologies or [],
                    "is_startup": exp.is_startup,
                    "company_founded_year": exp.company_founded_year,
                    "company_annual_revenue": exp.company_annual_revenue,
                    # Campos Pearch company_info
                    "company_followers_count": exp.company_followers_count,
                    "company_keywords": exp.company_keywords or []
                })
            
            # Reveal-no-save (Paulo): salvar exige no minimo email. Quando chega sem
            # email, tenta revelar via Apify (linkedin_url, ~$0.01). Sem email apos reveal:
            #   - save_without_email=True -> salva mesmo assim (recrutador escolheu)
            #   - senao -> NAO salva; reporta em skipped_no_email_ids (base nunca tem registro inutil)
            _resolved_email = candidate_dto.email
            _resolved_phone = candidate_dto.phone
            if not _resolved_email and candidate_dto.linkedin_url:
                try:
                    from app.domains.sourcing.services.contact_enrichment_service import (
                        get_contact_enrichment_service,
                    )
                    _enrich = get_contact_enrichment_service()
                    _r = await _enrich.enrich_by_linkedin_url(
                        candidate_dto.linkedin_url, company_id=company_id
                    )
                    if _r and _r.get('success') and _r.get('has_contact'):
                        _resolved_email = _resolved_email or _r.get('email')
                        _resolved_phone = _resolved_phone or _r.get('phone')
                except Exception as _e:
                    logger.warning('[Import] reveal por linkedin falhou (nao-fatal): %s', _e)

            if not _resolved_email and not request.save_without_email:
                skipped_no_email_ids.append(candidate_dto.pearch_id)
                continue

            new_id = uuid_lib.uuid4()
            profile = ExternalCandidateProfile(
                id=new_id,
                company_id=company_id,
                source="pearch",
                source_profile_id=candidate_dto.pearch_id,
                linkedin_url=candidate_dto.linkedin_url,
                raw_payload={
                    "original_dto": candidate_dto.model_dump(),
                    "source_search_query": request.source_search_query
                },
                name=candidate_dto.name,
                normalized_name=_normalize_name(candidate_dto.name),
                first_name=first_name,
                last_name=last_name,
                email=_resolved_email,
                phone=_resolved_phone,
                avatar_url=candidate_dto.avatar_url,
                headline=candidate_dto.headline,
                summary=candidate_dto.summary,
                current_title=candidate_dto.current_title,
                current_company=candidate_dto.current_company,
                location_city=location_city,
                location_state=location_state,
                location_country=location_country,
                location_raw=candidate_dto.location,
                years_of_experience=int(candidate_dto.years_of_experience) if candidate_dto.years_of_experience else None,
                skills=candidate_dto.skills[:50] if candidate_dto.skills else [],
                expertise=candidate_dto.expertise[:20] if candidate_dto.expertise else [],
                languages={"items": candidate_dto.languages} if candidate_dto.languages else {},
                experiences_snapshot=experiences_snapshot,
                education_snapshot=candidate_dto.education,
                is_open_to_work=candidate_dto.is_open_to_work,
                is_decision_maker=candidate_dto.is_decision_maker,
                is_top_universities=candidate_dto.is_top_universities,
                has_email=bool(_resolved_email),
                has_phone=bool(_resolved_phone),
                contact_revealed=bool(_resolved_email or _resolved_phone),
                fingerprint_hash=fingerprint,
                status="discovered",
                search_query=request.source_search_query
            )
            db.add(profile)
            
            imported_ids.append(str(new_id))
            id_mappings.append(IdMapping(
                pearch_id=candidate_dto.pearch_id,
                local_id=str(new_id)
            ))
        
        
        return ImportCandidatesResponse(
            imported_count=len(imported_ids),
            skipped_count=len(skipped_ids),
            updated_count=len(updated_ids),
            imported_ids=imported_ids,
            skipped_ids=skipped_ids,
            skipped_no_email_ids=skipped_no_email_ids,
            mapping=id_mappings,
            message=f"Salvos {len(imported_ids)} candidatos descobertos em staging. {len(updated_ids)} atualizados. {len(skipped_ids)} já existiam."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error importing candidates to staging: {e}")
        raise LIAError(message="Erro interno do servidor")


class PromoteCandidateResponse(BaseModel):
    """Response da promoção de candidato para a base principal."""
    success: bool
    message: str
    candidate_id: str
    profile_id: str
    was_merged: bool = False
    merged_with_id: str | None = None


@router.post("/candidates/promote/{profile_id}", response_model=PromoteCandidateResponse)
async def promote_candidate_to_main_base(
    profile_id: str,
    current_user: ImportUser = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    """
    Promove um candidato descoberto (staging) para a base principal.
    
    FLUXO DE PROMOÇÃO:
    1. Busca o perfil em external_candidate_profiles
    2. Valida ownership (company_id derivado do usuário autenticado) e status (não promovido)
    3. Verifica se já existe candidato similar na base principal (por linkedin_url ou fingerprint)
    4. Se existe: faz merge dos dados (APENAS adiciona dados faltantes, não sobrescreve)
    5. Se não existe: cria novo candidato + CandidateSource + experiências + educação
    6. Atualiza o perfil de staging com promoted_to_candidate_id
    
    SEGURANÇA:
    - company_id derivado do usuário autenticado via get_current_user_or_demo
    - assert_resource_ownership valida isolamento multi-tenant
    - Bloqueia se já foi promovido
    - Merge preserva dados canônicos (não sobrescreve dados existentes)
    - Operação atômica com rollback em caso de erro
    
    Returns:
        PromoteCandidateResponse com o ID do candidato na base principal
    """
    import uuid as uuid_lib
    from datetime import datetime

    from sqlalchemy import select

    from app.models.candidate import (
from app.shared.errors import LIAError
        Candidate,
        CandidateEducation,
        CandidateExperience,
        CandidateSource,
        ExternalCandidateProfile,
    )
    
    get_user_company_id(current_user)
    
    try:
        profile_result = await db.execute(
            select(ExternalCandidateProfile).where(ExternalCandidateProfile.id == profile_id, ExternalCandidateProfile.company_id == company_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil não encontrado na staging")
        
        assert_resource_ownership(profile, current_user, "external_profile")
        
        if profile.promoted_to_candidate_id:
            return PromoteCandidateResponse(
                success=True,
                message="Candidato já foi promovido anteriormente",
                candidate_id=str(profile.promoted_to_candidate_id),
                profile_id=profile_id,
                was_merged=False
            )
        
        existing_candidate = None
        if profile.linkedin_url:
            existing_result = await db.execute(
                select(Candidate).where(Candidate.linkedin_url == profile.linkedin_url, Candidate.company_id == company_id)
            )
            existing_candidate = existing_result.scalar_one_or_none()
        
        if not existing_candidate and profile.source_profile_id:
            existing_result = await db.execute(
                select(Candidate).where(Candidate.pearch_profile_id == profile.source_profile_id, Candidate.company_id == company_id)
            )
            existing_candidate = existing_result.scalar_one_or_none()
        
        if existing_candidate:
            updated_fields = []
            if profile.email and not existing_candidate.email:
                existing_candidate.email = profile.email
                updated_fields.append("email")
            if profile.phone and not existing_candidate.phone:
                existing_candidate.phone = profile.phone
                updated_fields.append("phone")
            if profile.avatar_url and not existing_candidate.avatar_url:
                existing_candidate.avatar_url = profile.avatar_url
                updated_fields.append("avatar_url")
            if profile.summary and not existing_candidate.self_introduction:
                existing_candidate.self_introduction = profile.summary
                updated_fields.append("self_introduction")
            if profile.skills and not existing_candidate.technical_skills:
                existing_candidate.technical_skills = profile.skills
                updated_fields.append("technical_skills")
            
            # Campos exclusivos da busca global Pearch - SEMPRE sobrescrever com dados frescos
            # Usar raw_payload como fonte da verdade para determinar se campo foi retornado
            # O raw_payload pode ter estrutura { original_dto: {...} } ou os campos diretamente
            raw_payload_raw = profile.raw_payload or {}
            raw_payload = raw_payload_raw.get("original_dto", raw_payload_raw)
            
            # Campos booleanos - usar raw_payload como fonte da verdade
            # Quando Pearch retorna o campo, sobrescrever (inclusive com None para limpar dados antigos)
            # IMPORTANTE: Usar atribuição direta sem `or` para preservar valores False legítimos
            if "is_open_to_work" in raw_payload:
                existing_candidate.is_open_to_work = raw_payload["is_open_to_work"]
                updated_fields.append("is_open_to_work")
            elif "is_opentowork" in raw_payload:
                existing_candidate.is_open_to_work = raw_payload["is_opentowork"]
                updated_fields.append("is_open_to_work")
            if "is_decision_maker" in raw_payload:
                existing_candidate.is_decision_maker = raw_payload["is_decision_maker"]
                updated_fields.append("is_decision_maker")
            if "is_top_universities" in raw_payload:
                existing_candidate.is_top_universities = raw_payload["is_top_universities"]
                updated_fields.append("is_top_universities")
            if "is_hiring" in raw_payload:
                existing_candidate.is_hiring = raw_payload["is_hiring"]
                updated_fields.append("is_hiring")
            
            # Campos de texto - verificar raw_payload primeiro, depois fallback para profile
            # Quando Pearch omite um campo, NÃO sobrescrever (manter dados existentes)
            if "headline" in raw_payload:
                existing_candidate.headline = raw_payload.get("headline")
                updated_fields.append("headline")
            elif profile.headline is not None:
                existing_candidate.headline = profile.headline
                updated_fields.append("headline")
            
            if "expertise" in raw_payload:
                existing_candidate.expertise = raw_payload.get("expertise")
                updated_fields.append("expertise")
            elif profile.expertise is not None:
                existing_candidate.expertise = profile.expertise
                updated_fields.append("expertise")
            
            if "seniority_level" in raw_payload:
                existing_candidate.seniority_level = raw_payload.get("seniority_level")
                updated_fields.append("seniority_level")
            elif profile.seniority_level is not None:
                existing_candidate.seniority_level = profile.seniority_level
                updated_fields.append("seniority_level")
            
            if "best_personal_email" in raw_payload:
                existing_candidate.best_personal_email = raw_payload.get("best_personal_email")
                updated_fields.append("best_personal_email")
            elif profile.best_personal_email is not None:
                existing_candidate.best_personal_email = profile.best_personal_email
                updated_fields.append("best_personal_email")
            
            if "estimated_age" in raw_payload:
                existing_candidate.estimated_age = raw_payload.get("estimated_age")
                updated_fields.append("estimated_age")
            elif profile.estimated_age is not None:
                existing_candidate.estimated_age = profile.estimated_age
                updated_fields.append("estimated_age")
            
            # Campos JSON/dict - verificar raw_payload primeiro
            if "phone_types" in raw_payload:
                existing_candidate.phone_types = raw_payload.get("phone_types")
                updated_fields.append("phone_types")
            elif profile.phone_types is not None:
                existing_candidate.phone_types = profile.phone_types
                updated_fields.append("phone_types")
            
            # Construir pearch_insights a partir do raw_payload (insights + query_insights)
            if "insights" in raw_payload or profile.pearch_insights is not None:
                pearch_insights_data = {}
                raw_insights = raw_payload.get("insights", {})
                if raw_insights:
                    pearch_insights_data = {
                        "overall_summary": raw_insights.get("overall_summary"),
                        "query_insights": raw_insights.get("query_insights", []),
                        "match_reasoning": raw_payload.get("match_reasoning")
                    }
                elif profile.pearch_insights is not None:
                    pearch_insights_data = profile.pearch_insights
                existing_candidate.pearch_insights = pearch_insights_data
                updated_fields.append("pearch_insights")
            
            # Campos numéricos - verificar raw_payload primeiro (0 é válido)
            if "followers_count" in raw_payload or "linkedin_followers_count" in raw_payload:
                existing_candidate.linkedin_followers_count = raw_payload.get("followers_count") or raw_payload.get("linkedin_followers_count")
                updated_fields.append("linkedin_followers_count")
            elif profile.linkedin_followers_count is not None:
                existing_candidate.linkedin_followers_count = profile.linkedin_followers_count
                updated_fields.append("linkedin_followers_count")
            
            if "connections_count" in raw_payload or "linkedin_connections_count" in raw_payload:
                existing_candidate.linkedin_connections_count = raw_payload.get("connections_count") or raw_payload.get("linkedin_connections_count")
                updated_fields.append("linkedin_connections_count")
            elif profile.linkedin_connections_count is not None:
                existing_candidate.linkedin_connections_count = profile.linkedin_connections_count
                updated_fields.append("linkedin_connections_count")
            
            # Campo outreach_message - verificar raw_payload primeiro
            if "outreach_message" in raw_payload:
                existing_candidate.outreach_message = raw_payload.get("outreach_message")
                updated_fields.append("outreach_message")
            elif profile.outreach_message is not None:
                existing_candidate.outreach_message = profile.outreach_message
                updated_fields.append("outreach_message")
            
            # Novos campos Pearch - middle_name, emails de negócio/pessoais
            if "middle_name" in raw_payload:
                existing_candidate.middle_name = raw_payload.get("middle_name")
                updated_fields.append("middle_name")
            
            if "best_business_email" in raw_payload:
                existing_candidate.best_business_email = raw_payload.get("best_business_email")
                updated_fields.append("best_business_email")
            
            if "personal_emails" in raw_payload:
                existing_candidate.personal_emails = raw_payload.get("personal_emails", [])
                updated_fields.append("personal_emails")
            
            if "business_emails" in raw_payload:
                existing_candidate.business_emails = raw_payload.get("business_emails", [])
                updated_fields.append("business_emails")
            
            # Campos de company_info da primeira experiência
            # Suporta formato API Pearch (company_info aninhado) e DTO (campos diretos)
            experiences_data = raw_payload.get("experiences", [])
            if experiences_data and len(experiences_data) > 0:
                first_exp = experiences_data[0] if isinstance(experiences_data[0], dict) else {}
                # Primeiro tenta o formato API Pearch (company_info aninhado)
                company_info = first_exp.get("company_info", {})
                if company_info:
                    if "followers_count" in company_info:
                        existing_candidate.company_followers_count = company_info.get("followers_count")
                        updated_fields.append("company_followers_count")
                    if "keywords" in company_info:
                        existing_candidate.company_keywords = company_info.get("keywords", [])
                        updated_fields.append("company_keywords")
                # Se não tiver company_info, usa campos diretos do DTO
                if "company_followers_count" not in updated_fields and "company_followers_count" in first_exp:
                    existing_candidate.company_followers_count = first_exp.get("company_followers_count")
                    updated_fields.append("company_followers_count")
                if "company_keywords" not in updated_fields and "company_keywords" in first_exp:
                    existing_candidate.company_keywords = first_exp.get("company_keywords", [])
                    updated_fields.append("company_keywords")
            
            existing_source = await db.execute(
                select(CandidateSource).where(
                    CandidateSource.candidate_id == existing_candidate.id,
                    CandidateSource.source == profile.source
                )
            )
            if not existing_source.scalar_one_or_none():
                source = CandidateSource(
                    candidate_id=existing_candidate.id,
                    source=profile.source,
                    source_profile_id=profile.source_profile_id,
                    linkedin_url=profile.linkedin_url,
                    fingerprint_hash=profile.fingerprint_hash,
                    is_primary=False,
                    external_profile_id=profile.id
                )
                db.add(source)
            
            profile.promoted_to_candidate_id = existing_candidate.id
            profile.promoted_at = datetime.utcnow()
            profile.status = "promoted_merged"
            
            
            return PromoteCandidateResponse(
                success=True,
                message=f"Candidato mesclado com existente. Campos atualizados: {', '.join(updated_fields) if updated_fields else 'nenhum (dados já completos)'}",
                candidate_id=str(existing_candidate.id),
                profile_id=profile_id,
                was_merged=True,
                merged_with_id=str(existing_candidate.id)
            )
        
        new_candidate_id = uuid_lib.uuid4()
        
        # Extrair insights da Pearch do raw_payload se disponível
        # O raw_payload pode ter estrutura { original_dto: {...} } ou os campos diretamente
        raw_payload_raw = profile.raw_payload or {}
        raw_payload = raw_payload_raw.get("original_dto", raw_payload_raw)
        pearch_insights_data = {}
        if raw_payload.get("insights"):
            pearch_insights_data = {
                "overall_summary": raw_payload.get("insights", {}).get("overall_summary"),
                "query_insights": raw_payload.get("insights", {}).get("query_insights", []),
                "match_reasoning": raw_payload.get("match_reasoning")
            }
        
        # Extrair company_info da primeira experiência (se disponível)
        # Suporta formato API Pearch (company_info aninhado) e DTO (campos diretos)
        company_followers_count = None
        company_keywords = None
        experiences_data = raw_payload.get("experiences", [])
        if experiences_data and len(experiences_data) > 0:
            first_exp = experiences_data[0] if isinstance(experiences_data[0], dict) else {}
            # Primeiro tenta o formato API Pearch (company_info aninhado)
            company_info = first_exp.get("company_info", {})
            if company_info:
                company_followers_count = company_info.get("followers_count")
                company_keywords = company_info.get("keywords", [])
            # Se não tiver company_info, usa campos diretos do DTO
            if company_followers_count is None:
                company_followers_count = first_exp.get("company_followers_count")
            if not company_keywords:
                company_keywords = first_exp.get("company_keywords", [])
        
        candidate = Candidate(
            id=new_candidate_id,
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            linkedin_url=profile.linkedin_url,
            avatar_url=profile.avatar_url,
            current_title=profile.current_title,
            current_company=profile.current_company,
            seniority_level=profile.seniority_level,
            self_introduction=profile.summary,
            headline=profile.headline,
            location_city=profile.location_city,
            location_state=profile.location_state,
            location_country=profile.location_country,
            years_of_experience=profile.years_of_experience,
            technical_skills=profile.skills or [],
            expertise=profile.expertise or [],
            languages=profile.languages or {},
            source="pearch",
            pearch_profile_id=profile.source_profile_id,
            # Campos exclusivos da busca global Pearch
            is_open_to_work=profile.is_open_to_work,
            is_decision_maker=profile.is_decision_maker,
            is_top_universities=profile.is_top_universities,
            is_hiring=raw_payload.get("is_hiring"),
            linkedin_followers_count=raw_payload.get("followers_count"),
            linkedin_connections_count=raw_payload.get("connections_count"),
            pearch_insights=pearch_insights_data,
            outreach_message=raw_payload.get("outreach_message") or getattr(profile, 'outreach_message', None),
            best_personal_email=getattr(profile, 'best_personal_email', None) or raw_payload.get("best_personal_email"),
            phone_types=getattr(profile, 'phone_types', None) or raw_payload.get("phone_types", {}),
            estimated_age=getattr(profile, 'estimated_age', None) or raw_payload.get("estimated_age"),
            # Novos campos Pearch
            middle_name=raw_payload.get("middle_name"),
            best_business_email=raw_payload.get("best_business_email"),
            personal_emails=raw_payload.get("personal_emails", []),
            business_emails=raw_payload.get("business_emails", []),
            company_followers_count=company_followers_count,
            company_keywords=company_keywords,
            status="new",
            is_active=True,
            additional_data={
                "promoted_from_staging": True,
                "original_profile_id": str(profile.id)
            }
        )
        db.add(candidate)
        
        source = CandidateSource(
            candidate_id=new_candidate_id,
            source=profile.source,
            source_profile_id=profile.source_profile_id,
            linkedin_url=profile.linkedin_url,
            fingerprint_hash=profile.fingerprint_hash,
            is_primary=True,
            external_profile_id=profile.id
        )
        db.add(source)
        
        for idx, exp_data in enumerate(profile.experiences_snapshot or []):
            experience = CandidateExperience(
                candidate_id=new_candidate_id,
                company_name=exp_data.get("company_name", "Unknown"),
                company_linkedin_url=exp_data.get("company_linkedin_url"),
                company_domain=exp_data.get("company_domain"),
                title=exp_data.get("title"),
                start_date=exp_data.get("start_date"),
                end_date=exp_data.get("end_date"),
                duration_years=exp_data.get("duration_years"),
                is_current=exp_data.get("is_current", False),
                description=exp_data.get("description"),
                location=exp_data.get("location"),
                industries=exp_data.get("industries", []),
                company_size=exp_data.get("company_size"),
                company_size_range=exp_data.get("company_size_range"),
                technologies=exp_data.get("technologies", []),
                is_startup=exp_data.get("is_startup"),
                company_founded_year=exp_data.get("company_founded_year"),
                company_annual_revenue=exp_data.get("company_annual_revenue"),
                sequence_order=idx
            )
            db.add(experience)
        
        for idx, edu_data in enumerate(profile.education_snapshot or []):
            education = CandidateEducation(
                candidate_id=new_candidate_id,
                institution=edu_data.get("school") or edu_data.get("institution"),
                degree=edu_data.get("degree"),
                field_of_study=edu_data.get("field_of_study") or edu_data.get("field"),
                start_date=edu_data.get("start_date"),
                end_date=edu_data.get("end_date"),
                is_completed=True if edu_data.get("end_date") else False,
                sequence_order=idx
            )
            db.add(education)
        
        profile.promoted_to_candidate_id = new_candidate_id
        profile.promoted_at = datetime.utcnow()
        profile.status = "promoted"
        
        
        return PromoteCandidateResponse(
            success=True,
            message="Candidato promovido para a base principal com sucesso",
            candidate_id=str(new_candidate_id),
            profile_id=profile_id,
            was_merged=False
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error promoting candidate: {e}")
        raise LIAError(message="Erro interno do servidor")


