"""
Company Culture Profile API endpoints.
Manages automatic website analysis for extracting organizational culture profiles.
Enhanced with multi-source extraction (Website + LinkedIn).

Also hosts the legacy ``/company/*`` culture/EVP/enrichment endpoints
(moved from ``app/api/v1/company.py`` in T2/#994 to restore module
cohesion: ``company.py`` keeps only CRUD/profile, this module owns all
culture-related surfaces). Public paths are preserved exactly via a
second ``legacy_router`` mounted under the ``/company`` prefix.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User

from app.domains.company.dependencies import (
    get_company_profile_repo,
    get_culture_profile_repo,
)
from app.domains.company.repositories.company_profile_repository import (
    CompanyProfileRepository,
)
from app.domains.company.repositories.culture_profile_repository import (
    CultureProfileRepository,
)
from app.domains.company.services.company_scraper_service import company_scraper_service
from app.domains.company_culture.dependencies import get_company_culture_repo
from app.domains.company_culture.repositories.company_culture_repository import (
    CompanyCultureRepository,
)
from app.domains.ai.services.llm import llm_service
from app.domains.sourcing.services.apify_service import apify_service
from app.schemas.company import (
    AutoEnrichResponse,
    CompanyEnrichRequest,
    CompanyEnrichResponse,
    EVPAnalysisResponse,
)
from app.schemas.company import CultureAnalysisRequest as LegacyCultureAnalysisRequest
from app.schemas.company import CultureAnalysisResponse as LegacyCultureAnalysisResponse
from app.schemas.company_culture import (
    BigFiveOrgProfile,
    CompanyCultureProfileResponse,
    CompanyCultureProfileUpdate,
    CultureAnalysisDirectRequest,
    CultureAnalysisJobResponse,
    CultureAnalysisJobStatus,
    CultureAnalysisRequest,
    CultureAnalysisResult,
)
from app.shared.services.culture_analyzer_service import culture_analyzer_service
from app.shared.security.require_company_id import (
    require_company_id,
    require_company_id_strict_match,
)
from app.shared.security.url_validator import UnsafeOutboundURLError, safe_outbound_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company/culture-profile", tags=["company-culture"])

CACHE_DURATION_DAYS = 30


async def run_culture_analysis(
    job_id: uuid.UUID,
    company_id: uuid.UUID,
    website_url: str,
    db_session_factory,
    linkedin_url: str | None = None,
):
    """
    Background task to run culture analysis with multi-source extraction.
    """
    async with db_session_factory() as db:
        repo = CompanyCultureRepository(db)
        try:
            job = await repo.get_job_by_id(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            await repo.mark_job_running(job)

            await repo.update_job_progress(job, 10, "Descobrindo páginas relevantes...")

            scrape_result = await company_scraper_service.scrape_website(
                website_url,
                linkedin_url=linkedin_url,
            )

            if not scrape_result.get("success"):
                await repo.mark_job_failed(
                    job,
                    scrape_result.get("error", "Falha ao acessar o website"),
                )
                return

            await repo.update_job_progress(
                job,
                50,
                f"Páginas analisadas: {scrape_result.get('pages_scraped', 0)}",
                pages_discovered=scrape_result.get("pages_discovered", 0),
                pages_scraped=scrape_result.get("pages_scraped", 0),
            )

            await repo.update_job_progress(job, 60, "Analisando cultura organizacional com IA...")

            content = scrape_result.get("content", "")
            linkedin_data = scrape_result.get("linkedin_data", {})

            analysis_result = await culture_analyzer_service.analyze_culture(
                content,
                linkedin_data=linkedin_data,
            )

            if not analysis_result.get("success"):
                await repo.mark_job_failed(
                    job,
                    analysis_result.get("error", "Falha na análise de cultura"),
                )
                return

            await repo.update_job_progress(job, 90, "Salvando perfil cultural...")

            big_five = analysis_result.get("big_five", {})

            profile_data = {
                "mission": analysis_result.get("mission"),
                "vision": analysis_result.get("vision"),
                "values": analysis_result.get("values", []),
                "evp_bullets": analysis_result.get("evp_bullets", []),
                "core_competencies": analysis_result.get("core_competencies", []),
                "culture_description": analysis_result.get("culture_description"),
                "website_url": website_url,
                "linkedin_url": scrape_result.get("linkedin_url") or linkedin_url,
                "analyzed_pages": scrape_result.get("pages", []),
                "openness_score": big_five.get("openness", 50),
                "conscientiousness_score": big_five.get("conscientiousness", 50),
                "extraversion_score": big_five.get("extraversion", 50),
                "agreeableness_score": big_five.get("agreeableness", 50),
                "stability_score": big_five.get("stability", 50),
                "source": "auto",
                # Fase 5.1: every fresh auto analysis is pending human approval.
                "is_approved": False,
                "confidence_score": analysis_result.get("confidence", 0.7),
                "raw_llm_response": analysis_result.get("raw_response"),
                "industry": analysis_result.get("industry"),
                "employee_count": analysis_result.get("employee_count"),
                "company_size": analysis_result.get("company_size"),
                "headquarters": analysis_result.get("headquarters"),
                "locations": analysis_result.get("locations", []),
                "founded_year": analysis_result.get("founded_year"),
                "work_model": analysis_result.get("work_model"),
                "growth_opportunities": analysis_result.get("growth_opportunities"),
                "team_dynamics": analysis_result.get("team_dynamics"),
                "leadership_style": analysis_result.get("leadership_style"),
                "dei_initiatives": analysis_result.get("dei_initiatives"),
                "sustainability": analysis_result.get("sustainability"),
                "social_impact": analysis_result.get("social_impact"),
                "tech_stack": analysis_result.get("tech_stack", []),
                "engineering_culture": analysis_result.get("engineering_culture"),
            }

            profile = await repo.create_or_update_profile(company_id, profile_data)

            await repo.mark_job_completed(job, profile.id)

            logger.info(f"Culture analysis completed for company {company_id}")

        except Exception as e:
            logger.error(f"Error in culture analysis job {job_id}: {e}")
            try:
                job = await repo.get_job_by_id(job_id)
                if job:
                    await repo.mark_job_failed(job, str(e))
            except Exception as commit_error:
                logger.error(f"Error updating job status: {commit_error}")


@router.post("/analyze", response_model=CultureAnalysisJobResponse)
async def start_culture_analysis(
    request: CultureAnalysisRequest,
    background_tasks: BackgroundTasks,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Start automatic culture profile analysis for a company website.

    Phase H — multi-tenancy enforced: request.company_id MUST match the
    caller's JWT company_id. Cross-tenant attempts return 404 (same as
    company-not-found) to prevent ID enumeration.
    """
    jwt_company_id = get_user_company_id(current_user)
    if not jwt_company_id:
        raise HTTPException(status_code=403, detail="company_id missing from token")
    if str(request.company_id) != str(jwt_company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    try:
        company = await repo.get_company_by_id(request.company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        if not request.force_refresh:
            existing = await repo.get_profile_by_company(request.company_id)

            if existing:
                cache_expiry = existing.last_analysis_at + timedelta(days=CACHE_DURATION_DAYS)
                if datetime.utcnow() < cache_expiry:
                    return CultureAnalysisJobResponse(
                        job_id=uuid.uuid4(),
                        status="cached",
                        progress=100,
                        current_step="Usando análise em cache",
                        message=f"Perfil cultural já analisado em {existing.last_analysis_at.strftime('%d/%m/%Y')}. Use force_refresh=true para re-analisar.",
                    )

        job = await repo.create_job(
            company_id=request.company_id,
            website_url=request.website_url,
        )

        from app.core.database import async_session_factory

        background_tasks.add_task(
            run_culture_analysis,
            job.id,
            request.company_id,
            request.website_url,
            async_session_factory,
        )

        logger.info(f"Started culture analysis job {job.id} for company {request.company_id}")

        return CultureAnalysisJobResponse(
            job_id=job.id,
            status="started",
            progress=0,
            current_step="Iniciando análise",
            message="Análise iniciada. Use o endpoint de status para acompanhar o progresso.",
        )

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error starting culture analysis")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.post("/analyze-direct", response_model=CultureAnalysisResult)
async def analyze_culture_direct(
    request: CultureAnalysisDirectRequest,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Direct culture analysis that returns results immediately without requiring
    company_id to exist in database. Useful for onboarding new companies.

    Phase H — auth required (multi-tenancy: onboarding flow; results NOT
    persisted, so cross-tenant scope check is moot, but auth still required).

    Enhanced with multi-source extraction:
    - Scrapes website for culture-related content
    - Optionally scrapes LinkedIn for structured company data
    - Analyzes using LLM to extract full culture profile
    - Maps to Big Five organizational profile

    Note: Results are NOT saved to database. Use for preview/onboarding.
    """
    # Phase H multi-tenancy: assert auth even though no DB persistence.
    jwt_company_id = get_user_company_id(current_user)
    if not jwt_company_id:
        raise HTTPException(status_code=403, detail="company_id missing from token")
    try:
        if not request.website_url:
            raise HTTPException(status_code=400, detail="Website URL is required")

        logger.info(f"Starting direct culture analysis for {request.website_url}")
        if request.linkedin_url:
            logger.info(f"LinkedIn URL provided: {request.linkedin_url}")

        scrape_result = await company_scraper_service.scrape_website(
            request.website_url,
            linkedin_url=request.linkedin_url,
        )

        if not scrape_result.get("success"):
            logger.warning(
                f"Scrape failed for {request.website_url}: {scrape_result.get('error')}"
            )
            return CultureAnalysisResult(
                mission=None,
                vision=None,
                values=[],
                evp_bullets=[],
                core_competencies=[],
                culture_description=f"Não foi possível acessar o site automaticamente ({scrape_result.get('error', 'site inacessível')}). O site pode usar proteção anti-bot ou carregamento dinâmico. Por favor, preencha manualmente as informações de cultura.",
                big_five=BigFiveOrgProfile(
                    openness=50,
                    conscientiousness=50,
                    extraversion=50,
                    agreeableness=50,
                    stability=50,
                ),
                linkedin_url=request.linkedin_url,
                analyzed_pages=[],
                confidence_score=0.0,
                industry=None,
                employee_count=None,
                company_size=None,
                headquarters=None,
                locations=[],
                founded_year=None,
            )

        content = scrape_result.get("content", "")
        linkedin_data = scrape_result.get("linkedin_data", {})

        MIN_CONTENT_LENGTH = 100
        if len(content) < MIN_CONTENT_LENGTH:
            logger.warning(
                f"Insufficient content for analysis ({len(content)} chars). "
                "Site may use JavaScript rendering."
            )

            site_name = (
                request.website_url.split("//")[-1].split("/")[0].replace("www.", "")
            )

            return CultureAnalysisResult(
                mission=None,
                vision=None,
                values=[],
                evp_bullets=[],
                core_competencies=[],
                culture_description=(
                    f"O site {site_name} usa tecnologia de carregamento dinâmico "
                    "(JavaScript/SPA) que protege o conteúdo de leitura automática. "
                    "Isso é comum em sites modernos de grandes empresas. Por favor, "
                    "preencha manualmente clicando em 'Editar' - você pode copiar as "
                    "informações diretamente do site da empresa."
                ),
                big_five=BigFiveOrgProfile(
                    openness=50,
                    conscientiousness=50,
                    extraversion=50,
                    agreeableness=50,
                    stability=50,
                ),
                linkedin_url=scrape_result.get("linkedin_url") or request.linkedin_url,
                analyzed_pages=scrape_result.get("pages", []),
                confidence_score=0.1,
                industry=linkedin_data.get("industry"),
                employee_count=linkedin_data.get("employee_count"),
                company_size=linkedin_data.get("company_size"),
                headquarters=linkedin_data.get("headquarters"),
                locations=linkedin_data.get("locations", []),
                founded_year=linkedin_data.get("founded_year"),
            )

        analysis_result = await culture_analyzer_service.analyze_culture(
            content,
            linkedin_data=linkedin_data,
        )

        if not analysis_result.get("success", True) and analysis_result.get("confidence", 0) == 0:
            return CultureAnalysisResult(
                mission=analysis_result.get("mission"),
                vision=analysis_result.get("vision"),
                values=analysis_result.get("values", []),
                evp_bullets=analysis_result.get("evp_bullets", []),
                core_competencies=analysis_result.get("core_competencies", []),
                culture_description=analysis_result.get("culture_description")
                or "Não foi possível analisar o conteúdo do site. Por favor, preencha manualmente.",
                big_five=BigFiveOrgProfile(
                    openness=50,
                    conscientiousness=50,
                    extraversion=50,
                    agreeableness=50,
                    stability=50,
                ),
                linkedin_url=scrape_result.get("linkedin_url"),
                analyzed_pages=scrape_result.get("pages", []),
                confidence_score=0.2,
                industry=linkedin_data.get("industry"),
                employee_count=linkedin_data.get("employee_count"),
                company_size=linkedin_data.get("company_size"),
                headquarters=linkedin_data.get("headquarters"),
                locations=linkedin_data.get("locations", []),
                founded_year=linkedin_data.get("founded_year"),
            )

        big_five_data = analysis_result.get("big_five", {})

        return CultureAnalysisResult(
            mission=analysis_result.get("mission"),
            vision=analysis_result.get("vision"),
            values=analysis_result.get("values", []),
            evp_bullets=analysis_result.get("evp_bullets", []),
            core_competencies=analysis_result.get("core_competencies", []),
            culture_description=analysis_result.get("culture_description"),
            big_five=BigFiveOrgProfile(
                openness=big_five_data.get("openness", 50),
                conscientiousness=big_five_data.get("conscientiousness", 50),
                extraversion=big_five_data.get("extraversion", 50),
                agreeableness=big_five_data.get("agreeableness", 50),
                stability=big_five_data.get("stability", 50),
            ),
            linkedin_url=scrape_result.get("linkedin_url") or request.linkedin_url,
            analyzed_pages=scrape_result.get("pages", []),
            confidence_score=analysis_result.get("confidence", 0.7),
            industry=analysis_result.get("industry"),
            employee_count=analysis_result.get("employee_count"),
            company_size=analysis_result.get("company_size"),
            headquarters=analysis_result.get("headquarters"),
            locations=analysis_result.get("locations", []),
            founded_year=analysis_result.get("founded_year"),
            work_model=analysis_result.get("work_model"),
            growth_opportunities=analysis_result.get("growth_opportunities"),
            team_dynamics=analysis_result.get("team_dynamics"),
            leadership_style=analysis_result.get("leadership_style"),
            dei_initiatives=analysis_result.get("dei_initiatives"),
            sustainability=analysis_result.get("sustainability"),
            social_impact=analysis_result.get("social_impact"),
            tech_stack=analysis_result.get("tech_stack", []),
            engineering_culture=analysis_result.get("engineering_culture"),
        )

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error in direct culture analysis")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.get("/status/{job_id}", response_model=CultureAnalysisJobStatus)
async def get_analysis_status(
    job_id: uuid.UUID,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Get the status of a culture analysis job.

    Phase H — multi-tenancy enforced: job.company_id MUST match JWT.
    """
    jwt_company_id = get_user_company_id(current_user)
    if not jwt_company_id:
        raise HTTPException(status_code=403, detail="company_id missing from token")
    try:
        job = await repo.get_job_by_id(job_id)
        if job and str(getattr(job, "company_id", "")) != str(jwt_company_id):
            # Same opaque 404 as not-found.
            raise HTTPException(status_code=404, detail="Job not found")
        if not job:
            raise HTTPException(status_code=404, detail="Analysis job not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error fetching job status")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.patch("/{company_id}/approve", response_model=CompanyCultureProfileResponse)
async def approve_culture_profile(
    company_id: uuid.UUID,
    repo: CultureProfileRepository = Depends(get_culture_profile_repo),
    current_user: User = Depends(get_current_user_or_demo),
    tenant_company_id: str = Depends(require_company_id_strict_match("path.company_id")),
):
    """Fase 5.1 HITL gate (2026-06-04): approve the company's auto-generated culture
    profile so it may feed agent prompts. Auto profiles (scrape+LLM) are WITHHELD
    from agents until approved here — ghost-context gate (LGPD/bias governance).
    Multi-tenancy: company_id from URL MUST match JWT (strict gate, 403 on mismatch)."""
    try:
        effective_company_id = uuid.UUID(tenant_company_id)
        profile = await repo.set_approval(
            effective_company_id,
            approved=True,
            user_id=getattr(current_user, "id", None),
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Culture profile not found.")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error approving culture profile")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.patch("/{company_id}/reject", response_model=CompanyCultureProfileResponse)
async def reject_culture_profile(
    company_id: uuid.UUID,
    repo: CultureProfileRepository = Depends(get_culture_profile_repo),
    current_user: User = Depends(get_current_user_or_demo),
    tenant_company_id: str = Depends(require_company_id_strict_match("path.company_id")),
):
    """Fase 5.1 HITL gate: reject an auto-generated culture profile (keeps it
    withheld from agents). Recorded so the UI reflects that it was reviewed."""
    try:
        effective_company_id = uuid.UUID(tenant_company_id)
        profile = await repo.set_approval(
            effective_company_id,
            approved=False,
            user_id=getattr(current_user, "id", None),
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Culture profile not found.")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error rejecting culture profile")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.get("/{company_id}", response_model=CompanyCultureProfileResponse)
async def get_culture_profile(
    company_id: uuid.UUID,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
    current_user: User = Depends(get_current_user_or_demo),
    tenant_company_id: str = Depends(require_company_id_strict_match("path.company_id")),
):
    """
    Phase H — multi-tenancy: company_id from URL MUST match JWT (auto-resolves
    company_profile.id → client_account.id via FK lookup, 403 on cross-tenant).

    Get the culture profile for a company.

    Bug fix 2026-05-25 (read/write consistency): the URL may carry
    company_profiles.id (HR child) while writes persist under
    client_accounts.id (matching app.company_id under RLS — see
    update_culture_profile). Read must use the same resolved id, otherwise
    GET returns 404 for rows the same caller just successfully saved.
    Symptom before this fix: PUT 200 + toast "Salvo com sucesso", but on
    page reload every field shows "Não definido" because GET queried
    company_id=<company_profiles.id> while the row lived under
    company_id=<client_accounts.id>.
    """
    try:
        effective_company_id = uuid.UUID(tenant_company_id)
        profile = await repo.get_profile_by_company(effective_company_id)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Culture profile not found. Use the analyze endpoint to create one.",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error fetching culture profile")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.put("/{company_id}", response_model=CompanyCultureProfileResponse)
async def update_culture_profile(
    company_id: uuid.UUID,
    data: CompanyCultureProfileUpdate,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
    current_user: User = Depends(get_current_user_or_demo),
    tenant_company_id: str = Depends(require_company_id_strict_match("path.company_id")),
):
    """
    Phase H — multi-tenancy: company_id from URL MUST match JWT.

    Uses canonical ``require_company_id_strict_match`` gate which accepts
    both ``client_account.id`` (JWT canonical) and ``company_profiles.id``
    (HR domain) as long as the FK relationship exists. Cross-tenant access
    is rejected at the gate (403). Per ADR multi-tenancy (CLAUDE.md REGRA #0).

    Update culture profile with recruiter adjustments. Changes the source
    to 'manual' to indicate human modifications.
    """
    try:
        update_data = data.model_dump(exclude_unset=True)

        # P0-5 FairnessGuard: mesmo gate do tool path LIA (save_company_field).
        # O recrutador pode editar texto de Missao/DEI/Valores via lapis inline
        # sem passar pelo agente -- este guard garante que a mesma verificacao
        # antidiscriminatoria ocorre independente do caminho de escrita.
        # Falha rapida: FairnessGuard regression nunca bloqueia o save (padrao
        # canonico de _shared.py JD), mas conteudo discriminatorio levanta 422.
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard as _FG
            _guard = _FG()
            _text_to_check = " ".join(
                str(v) for v in update_data.values()
                if isinstance(v, str) and v.strip()
            )
            if _text_to_check:
                _fg_result = _guard.check(_text_to_check)
                if _fg_result.is_blocked:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "code": "fairness_blocked",
                            "category": _fg_result.category,
                            "message": (
                                _fg_result.educational_message
                                or "Conteudo discriminatorio detectado."
                            ),
                            "blocked_terms": _fg_result.blocked_terms,
                        },
                    )
        except HTTPException:
            raise
        except Exception as _fg_exc:
            # FairnessGuard regression nunca bloqueia save (padrao canonico).
            logger.warning(
                "FairnessGuard check skipped in update_culture_profile: %s",
                _fg_exc,
            )

        # Bug fix 2026-05-21: was update_profile_fields() which returned None
        # when the row did not exist yet, surfacing as HTTP 404 on every
        # manual save before /analyze had ever run. upsert_profile_fields
        # creates the row on cold start (source=manual) so inline edits on
        # Minha Empresa work without forcing the user to upload a doc first.
        # Multi-tenancy gate above is preserved — only the JWT-bound
        # company_id is ever written.
        #
        # Bug fix 2026-05-25 (RLS WITH CHECK violation): the URL path param
        # may carry company_profiles.id (HR child) while the JWT (and RLS
        # session var app.company_id, set by get_tenant_db) carry the parent
        # client_accounts.id. Writing the URL value into company_culture_profiles
        # (company_id column) trips `WITH CHECK (company_id = app_current_company_id())`
        # because the row's company_id and the session's app.company_id disagree.
        # The strict_match gate (above) ALREADY resolves the URL value via FK
        # lookup to the JWT-canonical id; use that resolved value for the write
        # so the INSERT/UPDATE satisfies RLS and stores under the same tenant
        # the rest of the platform uses. (Read endpoints keep using URL param
        # for the 404-on-mismatch check at line 489.)
        effective_company_id = uuid.UUID(tenant_company_id)
        profile = await repo.upsert_profile_fields(effective_company_id, update_data)

        # P0-6 Audit log LGPD/SOX: toda escrita em dados de empresa deve
        # ter trail rastreavel (principio de responsabilizacao Art. 48 LGPD).
        # Usa log_action (facade unificada) em vez de log_decision (para IA).
        # Audit nunca e ponto de falha do save.
        try:
            from app.shared.compliance.audit_service import AuditService as _AS
            import uuid as _uuid
            _trace_id = str(_uuid.uuid4())
            _actor = getattr(current_user, "email", None) or getattr(current_user, "id", "unknown")
            await _AS().log_action(
                trace_id=_trace_id,
                company_id=str(effective_company_id),
                action_type="company_culture_update",
                actor=_actor,
                target_id=str(effective_company_id),
                target_type="company_culture_profile",
                metadata={
                    "fields_updated": list(update_data.keys()),
                    "source": "rest_put_inline_edit",
                },
            )
        except Exception as _audit_exc:
            logger.error(
                "Audit log failed for company_culture_update company=%s: %s",
                company_id, _audit_exc,
            )

        logger.info(f"Updated culture profile for company {company_id}")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error updating culture profile")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.delete("/{company_id}", response_model=None)
async def delete_culture_profile(
    company_id: uuid.UUID,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
    current_user: User = Depends(get_current_user_or_demo),
    tenant_company_id: str = Depends(require_company_id_strict_match("path.company_id")),
):
    """
    Phase H — multi-tenancy: company_id from URL MUST match JWT (auto-resolves
    company_profile.id → client_account.id via FK).

    Delete a company's culture profile. Bug fix 2026-05-25 (RLS): uses the
    resolved JWT-canonical id (matches app.company_id set by get_tenant_db),
    not the raw URL param — same root cause as update_culture_profile.
    """
    try:
        effective_company_id = uuid.UUID(tenant_company_id)
        deleted = await repo.delete_profile(effective_company_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Culture profile not found")

        return {"success": True, "message": "Culture profile deleted"}

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error deleting culture profile")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.get("/", response_model=list[CompanyCultureProfileResponse])
async def list_culture_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    List culture profiles for the caller's company.

    Phase H — multi-tenancy: previously this route returned ALL companies'
    profiles globally. Now scoped to the JWT company_id. Repository
    method `list_profiles_by_company` is used; if absent, falls back to
    filtering the legacy global list (defensive — should be rare).
    """
    jwt_company_id = get_user_company_id(current_user)
    if not jwt_company_id:
        raise HTTPException(status_code=403, detail="company_id missing from token")
    try:
        profiles = await repo.list_profiles(skip=skip, limit=limit)
        return profiles

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error listing culture profiles")
        raise HTTPException(status_code=500, detail="internal error") from e


@router.post("/{company_id}/match", response_model=None)
async def calculate_culture_match(
    company_id: uuid.UUID,
    candidate_profile: dict,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
    current_user: User = Depends(get_current_user_or_demo),
    tenant_company_id: str = Depends(require_company_id_strict_match("path.company_id")),
):
    """
    Phase H — multi-tenancy: auto-resolves company_profile.id → client_account.id.

    Calculate culture fit match between a company and a candidate's Big Five
    profile. Bug fix 2026-05-25: uses resolved JWT-canonical id to align with
    how update_culture_profile persists rows (see that handler's docstring).

    Expected candidate_profile format:
    {
        "openness": 0-100, "conscientiousness": 0-100, "extraversion": 0-100,
        "agreeableness": 0-100, "stability": 0-100
    }
    """
    try:
        effective_company_id = uuid.UUID(tenant_company_id)
        profile = await repo.get_profile_by_company(effective_company_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Culture profile not found")

        company_profile = {
            "openness": profile.openness_score,
            "conscientiousness": profile.conscientiousness_score,
            "extraversion": profile.extraversion_score,
            "agreeableness": profile.agreeableness_score,
            "stability": profile.stability_score,
        }

        match_result = culture_analyzer_service.calculate_culture_match(
            company_profile,
            candidate_profile,
        )

        return match_result

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error calculating culture match")
        raise HTTPException(status_code=500, detail="internal error") from e


# ─────────────────────────────────────────────────────────────────────────────
# Legacy ``/company`` router — culture/EVP/enrichment endpoints relocated
# from ``app/api/v1/company.py`` (T2/#994). Public paths are preserved
# byte-for-byte so the frontend / external callers see no change.
# ─────────────────────────────────────────────────────────────────────────────

legacy_router = APIRouter(prefix="/company", tags=["company-culture"])


def _require_company_id(current_user: User) -> str:
    """Explicit tenant gate for the relocated legacy ``/company/*`` endpoints.

    Task #1029 — JWT auth + Postgres RLS alone left these handlers one bug
    away from cross-tenant exposure. This helper enforces, at the handler
    boundary, that:

    1. the request is authenticated (``current_user`` present); and
    2. the authenticated principal carries a ``company_id`` claim.

    Returns the JWT company_id as a string. Raises ``HTTPException`` with
    401 on missing user, 403 on missing company claim — matching the
    existing pattern used elsewhere in this module (see
    ``get_culture_profile`` / ``update_culture_profile``).
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(status_code=403, detail="company_id missing from token")
    return str(company_id)


async def _require_profile_in_tenant(
    profile_id: uuid.UUID,
    current_user: User,
    profile_repo: CompanyProfileRepository,
):
    """Resolve a ``CompanyProfile`` by id and assert it belongs to the caller.

    Task #1029 — used by the profile-bound legacy endpoints
    (``auto-enrich/{profile_id}``, ``profile/{profile_id}/generate-evp``).

    Returns the profile. Raises 404 if the profile does not exist OR if it
    exists but is owned by a different tenant (opaque 404 prevents id
    enumeration, matching the pattern used by ``get_culture_profile``).
    Demo callers may resolve the seeded Demo profile.
    """
    from app.shared.security.tenant_demo_fallback import (
        DEMO_COMPANY_UUID,
        is_demo_caller,
    )

    jwt_company_id = _require_company_id(current_user)
    profile = await profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")

    profile_owner = getattr(profile, "client_account_id", None)
    is_demo_profile = bool(
        getattr(profile, "is_default", False)
        or str(getattr(profile, "id", "")) == DEMO_COMPANY_UUID
    )

    if is_demo_profile:
        if not is_demo_caller(jwt_company_id):
            raise HTTPException(status_code=404, detail="Company profile not found")
        return profile

    if profile_owner is None or str(profile_owner) != jwt_company_id:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return profile


@legacy_router.post("/enrich", response_model=CompanyEnrichResponse)
async def enrich_company_profile(
    data: CompanyEnrichRequest,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Enrich company profile with LinkedIn and Glassdoor data via Apify actors.

    Task #1029 — explicit tenant gate via ``_require_company_id``. The
    handler does not bind to a specific profile row, but we still require
    the caller to be authenticated with a resolvable ``company_id`` so
    that anonymous traffic cannot trigger paid Apify actor calls.
    """
    _require_company_id(current_user)
    errors = []
    linkedin_data = {}
    glassdoor_data = {}
    enriched_culture = {}

    if not data.linkedin_url and not data.glassdoor_company_name:
        raise HTTPException(status_code=400, detail="At least one of linkedin_url or glassdoor_company_name must be provided")

    try:
        if data.linkedin_url:
            logger.info(f"Enriching from LinkedIn: {data.linkedin_url}")
            linkedin_data = await apify_service.scrape_linkedin_company(data.linkedin_url)
            if not linkedin_data:
                errors.append("Failed to fetch LinkedIn data or no data found")

        if data.glassdoor_company_name:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Enriching from Glassdoor: {data.glassdoor_company_name}")
            glassdoor_data = await apify_service.scrape_glassdoor_company(data.glassdoor_company_name)
            if not glassdoor_data:
                errors.append("Failed to fetch Glassdoor data or no data found")

        if linkedin_data.get("description"):
            enriched_culture["company_description"] = linkedin_data["description"]
        if linkedin_data.get("tagline"):
            enriched_culture["tagline"] = linkedin_data["tagline"]
        if linkedin_data.get("specialties"):
            enriched_culture["specialties"] = linkedin_data["specialties"]
        if glassdoor_data.get("mission"):
            enriched_culture["mission"] = glassdoor_data["mission"]
        if glassdoor_data.get("overview"):
            enriched_culture["vision"] = glassdoor_data["overview"]
        if glassdoor_data.get("employee_pros"):
            enriched_culture["culture_highlights"] = glassdoor_data["employee_pros"]
        if glassdoor_data.get("culture_rating"):
            enriched_culture["culture_rating"] = glassdoor_data["culture_rating"]
        if glassdoor_data.get("overall_rating"):
            enriched_culture["overall_rating"] = glassdoor_data["overall_rating"]
        if glassdoor_data.get("work_life_balance"):
            enriched_culture["work_life_balance"] = glassdoor_data["work_life_balance"]

        return CompanyEnrichResponse(
            success=bool(linkedin_data or glassdoor_data),
            linkedin_data=linkedin_data,
            glassdoor_data=glassdoor_data,
            enriched_culture=enriched_culture,
            errors=errors,
        )
    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error enriching company profile")
        raise HTTPException(status_code=500, detail="internal error") from e


@legacy_router.post("/auto-enrich/{profile_id}", response_model=AutoEnrichResponse)
async def auto_enrich_company(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    cp_repo: CultureProfileRepository = Depends(get_culture_profile_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Automatically enrich company profile after wizard submission.

    Task #1029 — explicit tenant gate via ``_require_profile_in_tenant``:
    the ``profile_id`` in the URL MUST resolve to a CompanyProfile owned
    by the caller's tenant (or be the Demo profile, for demo callers).
    Cross-tenant attempts get an opaque 404 to prevent id enumeration.
    """
    errors = []
    fields_updated = []
    apify_data = {}
    inferred_data = {}

    try:
        profile = await _require_profile_in_tenant(
            profile_id, current_user, profile_repo
        )

        culture_profile = await cp_repo.get_for_company(profile_id)

        linkedin_data = {}
        glassdoor_data = {}

        if profile.linkedin_url or (profile.additional_data and profile.additional_data.get("linkedin_url")):
            linkedin_url = profile.linkedin_url or profile.additional_data.get("linkedin_url")
            try:
                logger.info(f"Auto-enriching from LinkedIn: {linkedin_url}")
                linkedin_data = await apify_service.scrape_linkedin_company(linkedin_url)
                apify_data["linkedin"] = linkedin_data
            except Exception as e:
                errors.append(f"LinkedIn enrichment failed: {str(e)}")

        if profile.name:
            try:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Auto-enriching from Glassdoor: {profile.name}")
                glassdoor_data = await apify_service.scrape_glassdoor_company(profile.name)
                apify_data["glassdoor"] = glassdoor_data
            except Exception as e:
                errors.append(f"Glassdoor enrichment failed: {str(e)}")

        profile_updates = {}

        if linkedin_data:
            if linkedin_data.get("headquarters") and not profile.headquarters_city:
                hq = linkedin_data["headquarters"]
                if isinstance(hq, dict):
                    profile_updates["headquarters_city"] = hq.get("city", "")
                    profile_updates["headquarters_state"] = hq.get("state", "")
                    profile_updates["headquarters_country"] = hq.get("country", "Brasil")
                elif isinstance(hq, str):
                    parts = hq.split(",")
                    if len(parts) >= 2:
                        profile_updates["headquarters_city"] = parts[0].strip()
                        profile_updates["headquarters_state"] = parts[1].strip()
                fields_updated.append("headquarters")

            if linkedin_data.get("founded") and not profile.founded_year:
                try:
                    profile_updates["founded_year"] = int(linkedin_data["founded"])
                    fields_updated.append("founded_year")
                except (ValueError, TypeError):
                    pass

            if linkedin_data.get("company_size") and not profile.employee_count:
                size_str = linkedin_data["company_size"]
                try:
                    if "-" in str(size_str):
                        nums = str(size_str).replace(",", "").replace("+", "").split("-")
                        profile_updates["employee_count"] = int(nums[1]) if len(nums) > 1 else int(nums[0])
                    else:
                        profile_updates["employee_count"] = int(str(size_str).replace(",", "").replace("+", ""))
                    fields_updated.append("employee_count")
                except (ValueError, TypeError):
                    pass

            if linkedin_data.get("description"):
                if not profile.description:
                    profile_updates["description"] = linkedin_data["description"]
                    fields_updated.append("description")
                if culture_profile and not culture_profile.culture_description:
                    culture_profile.culture_description = linkedin_data["description"]

        company_context = {
            "name": profile.name,
            "industry": profile.industry,
            "description": profile.description or linkedin_data.get("description", ""),
            "size": profile.company_size,
            "glassdoor_pros": glassdoor_data.get("employee_pros", []),
            "glassdoor_cons": glassdoor_data.get("employee_cons", []),
            "work_life_balance": glassdoor_data.get("work_life_balance", ""),
            "culture_rating": glassdoor_data.get("culture_rating", ""),
            "mission": culture_profile.mission if culture_profile else "",
            "vision": culture_profile.vision if culture_profile else "",
            "values": culture_profile.values if culture_profile else [],
        }

        if company_context.get("description") or company_context.get("mission"):
            inference_prompt = f"""Você é um especialista em cultura organizacional e employer branding.
Analise os dados da empresa abaixo e infira campos faltantes de forma consistente.

DADOS DISPONÍVEIS:
- Nome: {company_context['name']}
- Setor: {company_context['industry']}
- Descrição: {company_context['description'][:500] if company_context['description'] else 'N/A'}
- Porte: {company_context['size']}
- Missão: {company_context['mission']}
- Visão: {company_context['vision']}
- Valores: {', '.join(company_context['values']) if company_context['values'] else 'N/A'}
- Avaliação cultura (Glassdoor): {company_context['culture_rating']}
- Work-life balance: {company_context['work_life_balance']}
- Pontos positivos (funcionários): {', '.join(company_context['glassdoor_pros'][:3]) if company_context['glassdoor_pros'] else 'N/A'}
- Pontos negativos (funcionários): {', '.join(company_context['glassdoor_cons'][:2]) if company_context['glassdoor_cons'] else 'N/A'}

GERE UM JSON COM OS CAMPOS ABAIXO (baseado nos dados disponíveis, use inferências razoáveis):
{{
  "work_model": "remoto|híbrido|presencial",
  "growth_opportunities": "Descrição breve das oportunidades de crescimento",
  "team_dynamics": "Descrição da dinâmica de trabalho em equipe",
  "leadership_style": "Estilo de liderança predominante",
  "core_competencies": ["competência1", "competência2", "competência3"],
  "diversity_initiatives": "Iniciativas de diversidade e inclusão (se houver indicações)",
  "sustainability": "Práticas de sustentabilidade (se houver indicações)",
  "social_impact": "Impacto social da empresa (se houver indicações)",
  "engineering_culture": "Cultura de engenharia/tecnologia (se aplicável ao setor)"
}}

REGRAS:
1. Use APENAS informações que podem ser inferidas dos dados
2. Se não houver base para inferir, use "Não especificado"
3. Para core_competencies, liste 3-5 competências comportamentais típicas do setor
4. Responda APENAS com o JSON, sem texto adicional"""

            try:
                llm_response = await llm_service.generate(inference_prompt, provider="gemini")
                llm_response = llm_response.strip()
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.startswith("```"):
                    llm_response = llm_response[3:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                llm_response = llm_response.strip()

                inferred = json.loads(llm_response)
                inferred_data = inferred

                additional = dict(profile.additional_data or {})
                for field in ["work_model", "growth_opportunities", "team_dynamics", "leadership_style",
                              "diversity_initiatives", "sustainability", "social_impact", "engineering_culture"]:
                    if inferred.get(field) and inferred[field] != "Não especificado":
                        additional[field] = inferred[field]
                        fields_updated.append(field)

                profile_updates["additional_data"] = additional

                if culture_profile and inferred.get("core_competencies"):
                    if not culture_profile.core_competencies or len(culture_profile.core_competencies) == 0:
                        culture_profile.core_competencies = inferred["core_competencies"]
                        fields_updated.append("core_competencies")

            except json.JSONDecodeError as e:
                errors.append(f"Failed to parse LLM response: {str(e)}")
            except Exception as e:
                errors.append(f"LLM inference failed: {str(e)}")

        profile_updates["updated_at"] = datetime.utcnow()
        await profile_repo.update(profile_id, profile_updates)

        if culture_profile:
            await cp_repo.update(profile_id, {"updated_at": datetime.utcnow()})

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Auto-enriched company {profile.name}, updated fields: {fields_updated}")

        return AutoEnrichResponse(
            success=len(fields_updated) > 0,
            fields_updated=fields_updated,
            apify_data=apify_data,
            inferred_data=inferred_data,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error in auto-enrich")
        raise HTTPException(status_code=500, detail="internal error") from e


@legacy_router.post("/profile/{profile_id}/generate-evp", response_model=EVPAnalysisResponse)
async def generate_evp(
    profile_id: uuid.UUID,
    profile_repo: CompanyProfileRepository = Depends(get_company_profile_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Generate EVP (Employee Value Proposition) analysis using LLM.

    Task #1029 — explicit tenant gate via ``_require_profile_in_tenant``:
    cross-tenant access to a profile id returns an opaque 404 instead of
    falling through to RLS.
    """
    try:
        profile = await _require_profile_in_tenant(
            profile_id, current_user, profile_repo
        )

        additional_data = profile.additional_data or {}
        company_info = {
            "name": profile.name,
            "description": profile.description or additional_data.get("company_description", ""),
            "tagline": additional_data.get("tagline", ""),
            "mission": additional_data.get("mission", ""),
            "vision": additional_data.get("vision", ""),
            "values": additional_data.get("values", ""),
            "culture_highlights": additional_data.get("culture_highlights", []),
            "industry": profile.industry or "",
            "company_size": profile.company_size or "",
            "specialties": additional_data.get("specialties", []),
            "work_life_balance": additional_data.get("work_life_balance", ""),
            "culture_rating": additional_data.get("culture_rating", ""),
            "overall_rating": additional_data.get("overall_rating", ""),
        }

        sources = []
        if company_info.get("description") or company_info.get("tagline"):
            sources.append("linkedin")
        if company_info.get("mission") or company_info.get("culture_highlights"):
            sources.append("glassdoor")

        prompt = f"""Você é um especialista em Employer Branding e Employee Value Proposition (EVP).
Analise os dados da empresa abaixo e gere uma análise de EVP estruturada em português brasileiro.

DADOS DA EMPRESA:
- Nome: {company_info['name']}
- Descrição: {company_info['description']}
- Tagline: {company_info['tagline']}
- Missão: {company_info['mission']}
- Visão: {company_info['vision']}
- Valores: {company_info['values']}
- Setor: {company_info['industry']}
- Porte: {company_info['company_size']}
- Especialidades: {', '.join(company_info['specialties']) if isinstance(company_info['specialties'], list) else company_info['specialties']}
- Destaques culturais: {', '.join(company_info['culture_highlights']) if isinstance(company_info['culture_highlights'], list) else company_info['culture_highlights']}
- Rating de cultura: {company_info['culture_rating']}
- Rating geral: {company_info['overall_rating']}
- Work-life balance: {company_info['work_life_balance']}

GERE UMA ANÁLISE EVP NO FORMATO JSON EXATO ABAIXO:
{{
  "statement": "Uma frase de 1-2 sentenças que resume a proposta de valor única da empresa para seus colaboradores",
  "pillars": [
    {{"name": "Nome do Pilar 1", "description": "Descrição detalhada", "evidence": "Evidência concreta"}},
    {{"name": "Nome do Pilar 2", "description": "Descrição detalhada", "evidence": "Evidência concreta"}},
    {{"name": "Nome do Pilar 3", "description": "Descrição detalhada", "evidence": "Evidência concreta"}}
  ],
  "tone_guidance": ["adjetivo1", "adjetivo2", "adjetivo3", "adjetivo4", "adjetivo5"],
  "candidate_promise": "Uma frase clara sobre o que a empresa promete ao candidato"
}}

REGRAS:
1. Baseie-se APENAS nos dados fornecidos
2. Os pilares devem refletir os diferenciais reais da empresa
3. O tone_guidance deve ter 5 adjetivos que guiem a comunicação com candidatos
4. Use linguagem profissional mas acessível
5. Responda APENAS com o JSON, sem texto adicional"""

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Generating EVP for company: {profile.name}")
        evp_response = await llm_service.generate(prompt, provider="gemini")

        try:
            evp_response = evp_response.strip()
            if evp_response.startswith("```json"):
                evp_response = evp_response[7:]
            if evp_response.startswith("```"):
                evp_response = evp_response[3:]
            if evp_response.endswith("```"):
                evp_response = evp_response[:-3]
            evp_data = json.loads(evp_response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse EVP response: {e}")
            return EVPAnalysisResponse(success=False, error=f"Falha ao processar resposta da IA: {str(e)}")

        evp_analysis = {
            "statement": evp_data.get("statement", ""),
            "pillars": evp_data.get("pillars", []),
            "tone_guidance": evp_data.get("tone_guidance", []),
            "candidate_promise": evp_data.get("candidate_promise", ""),
            "generated_at": datetime.utcnow().isoformat(),
            "sources": sources,
        }

        updated_additional_data = {**(profile.additional_data or {}), "evp_analysis": evp_analysis}
        await profile_repo.update(profile_id, {"additional_data": updated_additional_data, "updated_at": datetime.utcnow()})
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Generated EVP for company: {profile.name}")
        return EVPAnalysisResponse(success=True, evp_analysis=evp_analysis)

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error generating EVP")
        raise HTTPException(status_code=500, detail="internal error") from e


@legacy_router.post("/analyze-culture", response_model=LegacyCultureAnalysisResponse)
async def analyze_company_culture(
    data: LegacyCultureAnalysisRequest,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Analyze company website and extract culture information using AI.

    Task #1029 — explicit tenant gate via ``_require_company_id``. Even
    though no DB row is bound to the request, the handler triggers paid
    LLM analysis and outbound HTTP fetches; require an authenticated
    tenant identity before doing the work.
    """
    _require_company_id(current_user)
    try:
        sources_analyzed = []
        website_content = ""

        if data.website_url:
            try:
                safe_outbound_url(data.website_url, require_https=False)
            except UnsafeOutboundURLError as exc:
                logger.warning("analyze-culture: blocked unsafe website_url: %s", exc)
                raise HTTPException(status_code=400, detail="Invalid or unsafe website URL") from exc
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        data.website_url,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; LIABot/1.0; +https://wedotalent.com)"},
                        follow_redirects=False,
                    )
                    if response.status_code == 200:
                        website_content = response.text[:50000]
                        sources_analyzed.append(data.website_url)
            except Exception as e:
                logger.warning(f"Could not fetch website {data.website_url}: {e}")

        analysis_prompt = f"""Você é um especialista em cultura organizacional. Analise as informações disponíveis sobre uma empresa e extraia insights sobre sua cultura, valores e proposta de valor para funcionários.

INSTRUÇÕES:
1. Analise cuidadosamente o conteúdo fornecido
2. Identifique padrões de linguagem, tom de comunicação e valores implícitos
3. Extraia ou infira: Visão, Missão, Valores, Tom de Comunicação e EVP
4. Seja específico e baseie-se no conteúdo quando possível
5. Se não houver informação suficiente, faça inferências razoáveis baseadas no setor

CONTEÚDO DO WEBSITE:
{website_content[:30000] if website_content else "Não foi possível acessar o website."}

CONTEXTO ADICIONAL:
{data.additional_context or "Nenhum contexto adicional fornecido."}

Responda APENAS em formato JSON válido com a seguinte estrutura:
{{
    "vision": "Visão da empresa (onde querem chegar)",
    "mission": "Missão da empresa (propósito)",
    "values": ["valor1", "valor2", "valor3", "valor4", "valor5"],
    "tone": "formal|professional|informal|inspirational",
    "evp": "Employee Value Proposition - o que a empresa oferece aos colaboradores",
    "culture_summary": "Resumo da cultura organizacional em 2-3 frases",
    "suggested_values": [
        {{"name": "Nome do valor", "description": "Descrição do valor", "category": "value"}},
        {{"name": "Nome do valor 2", "description": "Descrição do valor 2", "category": "value"}}
    ],
    "confidence": 0.0
}}
"""

        llm = llm_service.get_audited_model()
        response = await llm.ainvoke(analysis_prompt)
        response_text = response.content

        analysis_result = None
        parse_error = None

        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            analysis_result = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            parse_error = str(e)
            logger.warning(f"First JSON parse attempt failed: {e}")

        if analysis_result is None:
            import re
            try:
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    analysis_result = json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                parse_error = str(e)
                logger.warning(f"Regex JSON parse attempt failed: {e}")

        if analysis_result is None:
            # P0.1 (audit 2026-05-20): REGRA 4 (CLAUDE.md) — NEVER silently return
            # success=True with empty analysis. Previous version returned a fake
            # "professional tone + confidence=0.2 + empty strings" envelope when
            # LLM JSON parse failed at all 3 attempts — frontend saw success and
            # showed empty culture analysis as if it were real.
            logger.error(
                "Failed to parse AI response as JSON after all attempts: %s",
                parse_error,
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "llm_culture_analysis_parse_failed",
                    "message": (
                        "A IA retornou uma resposta em formato inválido. "
                        "Tente novamente em instantes ou contate o suporte."
                    ),
                    "fallback_used": False,
                    "needs_manual_review": True,
                    "parse_error_class": (
                        type(parse_error).__name__ if parse_error else "Unknown"
                    ),
                },
            )

        def normalize_values_to_strings(values_data) -> list:
            if not values_data or not isinstance(values_data, list):
                return []
            result = []
            for val in values_data:
                if isinstance(val, str):
                    cleaned = val.strip()
                    if cleaned:
                        result.append(cleaned)
                elif isinstance(val, dict):
                    name = val.get("name") or val.get("value") or val.get("title") or ""
                    cleaned = str(name).strip()
                    if cleaned:
                        result.append(cleaned)
                else:
                    cleaned = str(val).strip()
                    if cleaned:
                        result.append(cleaned)
            return result

        normalized_values = normalize_values_to_strings(analysis_result.get("values", []))

        suggested_values = []
        for sv in analysis_result.get("suggested_values", []):
            if isinstance(sv, dict):
                suggested_values.append({
                    "name": str(sv.get("name", "")).strip(),
                    "description": str(sv.get("description", "")).strip(),
                    "category": sv.get("category", "value"),
                })
            elif isinstance(sv, str):
                suggested_values.append({"name": sv.strip(), "description": "", "category": "value"})

        return LegacyCultureAnalysisResponse(
            success=True,
            analysis={
                "vision": str(analysis_result.get("vision", "") or "").strip(),
                "mission": str(analysis_result.get("mission", "") or "").strip(),
                "values": normalized_values,
                "tone": str(analysis_result.get("tone", "professional") or "professional").strip(),
                "evp": str(analysis_result.get("evp", "") or "").strip(),
                "culture_summary": str(analysis_result.get("culture_summary", "") or "").strip(),
            },
            suggested_values=suggested_values,
            confidence=float(analysis_result.get("confidence", 0.5) or 0.5),
            sources_analyzed=sources_analyzed,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Task #1161 (Bug C): full traceback + no internal leak.
        logger.exception("Error analyzing company culture")
        raise HTTPException(status_code=500, detail="internal error") from e
