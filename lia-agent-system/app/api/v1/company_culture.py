"""
Company Culture Profile API endpoints.
Manages automatic website analysis for extracting organizational culture profiles.
Enhanced with multi-source extraction (Website + LinkedIn).
"""
import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.domains.company_culture.dependencies import get_company_culture_repo
from app.domains.company_culture.repositories.company_culture_repository import (
    CompanyCultureRepository,
)
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
from app.services.company_scraper_service import company_scraper_service
from app.services.culture_analyzer_service import culture_analyzer_service

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
):
    """
    Start automatic culture profile analysis for a company website.

    The analysis runs in the background and includes:
    - Web scraping of relevant pages (About, Careers, Culture)
    - LinkedIn URL discovery and scraping
    - LLM analysis to extract mission, vision, values, EVP
    - Big Five organizational profile mapping

    Returns a job_id to track progress.
    """
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
        logger.error(f"Error starting culture analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-direct", response_model=CultureAnalysisResult)
async def analyze_culture_direct(
    request: CultureAnalysisDirectRequest,
):
    """
    Direct culture analysis that returns results immediately without requiring
    company_id to exist in database. Useful for onboarding new companies.

    Enhanced with multi-source extraction:
    - Scrapes website for culture-related content
    - Optionally scrapes LinkedIn for structured company data
    - Analyzes using LLM to extract full culture profile
    - Maps to Big Five organizational profile

    Note: Results are NOT saved to database. Use for preview/onboarding.
    """
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
        logger.error(f"Error in direct culture analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=CultureAnalysisJobStatus)
async def get_analysis_status(
    job_id: uuid.UUID,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
):
    """
    Get the status of a culture analysis job.
    """
    try:
        job = await repo.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Analysis job not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_model=CompanyCultureProfileResponse)
async def get_culture_profile(
    company_id: uuid.UUID,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
):
    """
    Get the culture profile for a company.
    """
    try:
        profile = await repo.get_profile_by_company(company_id)

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Culture profile not found. Use the analyze endpoint to create one.",
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching culture profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{company_id}", response_model=CompanyCultureProfileResponse)
async def update_culture_profile(
    company_id: uuid.UUID,
    data: CompanyCultureProfileUpdate,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
):
    """
    Update culture profile with recruiter adjustments.
    Changes the source to 'manual' to indicate human modifications.
    """
    try:
        update_data = data.model_dump(exclude_unset=True)
        profile = await repo.update_profile_fields(company_id, update_data)

        if not profile:
            raise HTTPException(status_code=404, detail="Culture profile not found")

        logger.info(f"Updated culture profile for company {company_id}")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating culture profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{company_id}", response_model=None)
async def delete_culture_profile(
    company_id: uuid.UUID,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
):
    """
    Delete a company's culture profile.
    """
    try:
        deleted = await repo.delete_profile(company_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Culture profile not found")

        return {"success": True, "message": "Culture profile deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting culture profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[CompanyCultureProfileResponse])
async def list_culture_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
):
    """
    List all culture profiles.
    """
    try:
        profiles = await repo.list_profiles(skip=skip, limit=limit)
        return profiles

    except Exception as e:
        logger.error(f"Error listing culture profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{company_id}/match", response_model=None)
async def calculate_culture_match(
    company_id: uuid.UUID,
    candidate_profile: dict,
    repo: CompanyCultureRepository = Depends(get_company_culture_repo),
):
    """
    Calculate culture fit match between a company and a candidate's Big Five profile.

    Expected candidate_profile format:
    {
        "openness": 0-100,
        "conscientiousness": 0-100,
        "extraversion": 0-100,
        "agreeableness": 0-100,
        "stability": 0-100
    }
    """
    try:
        profile = await repo.get_profile_by_company(company_id)

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
        logger.error(f"Error calculating culture match: {e}")
        raise HTTPException(status_code=500, detail=str(e))
