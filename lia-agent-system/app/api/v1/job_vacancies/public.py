"""
Public routes (no authentication required) and share-link routes.
Also includes router_public for candidate application flow.
"""
from datetime import datetime
from uuid import UUID

import secrets
import uuid as uuid_lib

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile

from ._shared import (  # noqa: F401
    SATURATION_EXCLUDED_STATUSES,
    ADHERENCE_THRESHOLD,
    generate_slug,
    get_current_user_or_demo,
    get_user_company_id,
    User,
    Depends,
    HTTPException,
    notification_service,
    BaseModel,
    logger,
)
from app.domains.job_management.dependencies import get_job_vacancy_public_repo
from app.domains.cv_screening.services.cv_parser import CVParserService, get_cv_parser_service
from app.domains.cv_screening.services.lia_score_service import get_lia_score_service, LIAScoreService
from app.domains.job_management.repositories.job_vacancy_public_repository import JobVacancyPublicRepository
from app.models.candidate import Candidate, VacancyCandidate
from app.services.notification_service import NotificationType
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter()
router_public = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class GeneratePublicLinkRequest(WeDoBaseModel):
    regenerate: bool = False


class GeneratePublicLinkResponse(BaseModel):
    success: bool
    public_url: str
    slug: str
    message: str


class ShareLinkResponse(BaseModel):
    share_link: str
    slug: str
    qr_code_url: str | None = None
    expires_at: str | None = None
    view_count: int = 0


class PublicVacancyResponse(BaseModel):
    title: str
    description: str | None = None
    requirements: list[str] | None = []
    benefits: list[str] | None = []
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    company_name: str | None = None
    company_description: str | None = None
    company_website: str | None = None
    company_logo: str | None = None
    is_confidential: bool = False
    is_affirmative: bool = False
    technical_requirements: list[dict] | None = []
    languages: list[dict] | None = []
    behavioral_competencies: list[dict] | None = []
    salary_range: dict | None = None
    apply_url: str | None = None


class PublicApplicationResponse(BaseModel):
    status: str
    message: str
    candidate_id: str | None = None
    adherence_score: float | None = None
    next_step: str | None = None


# ─── Authenticated share-link routes ─────────────────────────────────────────

@router.post("/job-vacancies/{vacancy_id}/generate-public-link", response_model=GeneratePublicLinkResponse)
async def generate_public_link(
    vacancy_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    request: GeneratePublicLinkRequest = GeneratePublicLinkRequest(),
    repo: JobVacancyPublicRepository = Depends(get_job_vacancy_public_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """Generate or retrieve public sharing link for a job vacancy."""
    try:
        company_id = get_user_company_id(current_user)

        job = await repo.get_vacancy_by_id_and_company(vacancy_id, company_id)

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden":
            raise HTTPException(status_code=403, detail="Vagas ocultas não podem ter link público")

        if job.public_slug and not request.regenerate:
            return GeneratePublicLinkResponse(
                success=True,
                public_url=f"/vagas/{job.public_slug}",
                slug=job.public_slug,
                message="Link público existente"
            )

        company_short = ""
        if job.masked_company_name:
            company_short = job.masked_company_name[:30]

        new_slug = generate_slug(job.title, company_short)

        if await repo.slug_exists(new_slug):
            new_slug = generate_slug(job.title, secrets.token_hex(2))

        job = await repo.save_public_slug(job, new_slug)

        logger.info(f"Generated public link for job {vacancy_id}: /vagas/{new_slug}")

        return GeneratePublicLinkResponse(
            success=True,
            public_url=f"/vagas/{new_slug}",
            slug=new_slug,
            message="Link público gerado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating public link: {e}", exc_info=True)
        await repo.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{vacancy_id}/share-link", response_model=ShareLinkResponse)
async def get_share_link(
    vacancy_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    repo: JobVacancyPublicRepository = Depends(get_job_vacancy_public_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """Get shareable link details for a job vacancy."""
    try:
        company_id = get_user_company_id(current_user)

        job = await repo.get_vacancy_by_id_and_company(vacancy_id, company_id)

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden":
            raise HTTPException(status_code=403, detail="Vagas ocultas não podem ter link público")

        if not job.public_slug:
            company_short = ""
            if job.masked_company_name:
                company_short = job.masked_company_name[:30]

            new_slug = generate_slug(job.title, company_short)

            if await repo.slug_exists(new_slug):
                new_slug = generate_slug(job.title, secrets.token_hex(2))

            job = await repo.save_public_slug(job, new_slug)
            logger.info(f"Generated public slug for job {vacancy_id}: {new_slug}")

        share_link = f"https://app.wedotalent.com/jobs/{job.public_slug}"
        qr_code_url = f"/api/v1/job-vacancies/{vacancy_id}/qr-code"

        return ShareLinkResponse(
            share_link=share_link,
            slug=job.public_slug,
            qr_code_url=qr_code_url,
            expires_at=None,
            view_count=job.view_count or 0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting share link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Public routes (no auth) ──────────────────────────────────────────────────

@router_public.get("/p/{slug}", response_model=PublicVacancyResponse)
async def get_public_vacancy(
    slug: str,
    repo: JobVacancyPublicRepository = Depends(get_job_vacancy_public_repo), 
company_id: str = Depends(require_company_id)):
    """Get public vacancy information by slug (no authentication required)."""
    try:
        job = await repo.get_vacancy_by_slug(slug)

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden" or job.status not in ["Ativa", "Publicada"]:
            raise HTTPException(status_code=404, detail="Vaga não disponível")

        await repo.increment_view_count(job)

        is_confidential = job.is_confidential or job.visibility == "confidential"

        company_name = None
        if not is_confidential:
            if job.masked_company_name:
                company_name = job.masked_company_name

        tech_reqs = []
        if job.technical_requirements:
            for tr in job.technical_requirements:
                tech_reqs.append({
                    "technology": tr.get("technology"),
                    "level": tr.get("level"),
                    "category": tr.get("category"),
                    "required": tr.get("required", False)
                })

        languages = []
        if job.languages:
            for lang in job.languages:
                languages.append({
                    "language": lang.get("language"),
                    "level": lang.get("level"),
                    "required": lang.get("required", False)
                })

        competencies = []
        if job.behavioral_competencies:
            for comp in job.behavioral_competencies:
                competencies.append({
                    "competency": comp.get("competency"),
                    "weight": comp.get("weight")
                })

        salary_range = None
        if not is_confidential and job.salary_range:
            salary_range = job.salary_range

        apply_url = f"https://app.wedotalent.com/vagas/{slug}/apply"

        logger.info(f"Public vacancy accessed: {slug} (views: {job.view_count})")

        return PublicVacancyResponse(
            title=job.title,
            description=job.description,
            requirements=job.requirements or [],
            benefits=job.benefits or [],
            location=job.location,
            work_model=job.work_model,
            employment_type=job.employment_type,
            seniority_level=job.seniority_level,
            department=job.department,
            company_name=company_name,
            company_description=None,
            company_website=None,
            company_logo=None,
            is_confidential=is_confidential,
            is_affirmative=job.is_affirmative,
            technical_requirements=tech_reqs,
            languages=languages,
            behavioral_competencies=competencies,
            salary_range=salary_range,
            apply_url=apply_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching public vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router_public.post("/p/{slug}/apply", response_model=PublicApplicationResponse)
async def apply_to_public_vacancy(
    slug: str,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    lgpd_consent: str = Form(...),
    cv_file: UploadFile = File(...),
    repo: JobVacancyPublicRepository = Depends(get_job_vacancy_public_repo)
,
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
    lia_svc: LIAScoreService = Depends(get_lia_score_service),
company_id: str = Depends(require_company_id)):
    try:
        if lgpd_consent.lower() not in ("true", "1", "yes", "sim"):
            raise HTTPException(
                status_code=400,
                detail="Consentimento LGPD obrigatório para prosseguir."
            )

        job = await repo.get_vacancy_by_slug(slug)

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden" or job.status not in ["Ativa", "Publicada", "open", "active", "published"]:
            raise HTTPException(status_code=400, detail="Esta vaga não está aberta para candidaturas")

        cv_content = await cv_file.read()
        parsed_cv = {}
        try:
            parsed_cv = await cv_parser_svc.parse_cv(
                file_content=cv_content,
                filename=cv_file.filename
            )
        except Exception as e:
            logger.warning(f"CV parsing failed, continuing without parsed data: {e}")

        existing_candidate = await repo.get_candidate_by_email(email)

        if existing_candidate:
            candidate = existing_candidate
            candidate.name = name
            candidate.phone = phone or candidate.phone
            candidate.mobile_phone = phone or candidate.mobile_phone
            if parsed_cv.get("skills"):
                existing_skills = candidate.technical_skills or []
                candidate.technical_skills = list(set(existing_skills + parsed_cv.get("skills", [])))
            if parsed_cv.get("experience_years") and not candidate.years_of_experience:
                candidate.years_of_experience = parsed_cv.get("experience_years")
            if parsed_cv.get("current_title") and not candidate.current_title:
                candidate.current_title = parsed_cv.get("current_title")
            candidate.communication_consent = True
            candidate.updated_at = datetime.utcnow()
            await repo.flush_candidate(candidate)
        else:
            candidate = Candidate(
                id=uuid_lib.uuid4(),
                name=name,
                email=email,
                phone=phone,
                mobile_phone=phone,
                source="web_application",
                status="new",
                technical_skills=parsed_cv.get("skills", []),
                years_of_experience=parsed_cv.get("experience_years"),
                current_title=parsed_cv.get("current_title"),
                current_company=parsed_cv.get("current_company"),
                communication_consent=True
            )
            await repo.add_candidate(candidate)

        adherence_score = 70.0
        try:
            vacancy_requirements = {
                "query": job.title or "",
                "skills": job.required_skills or [],
                "experience_years": getattr(job, "min_experience_years", None),
                "seniority": job.seniority_level,
                "location": getattr(job, "location_city", None) or job.location
            }
            candidate_profile = {
                "skills": candidate.technical_skills or [],
                "experience_years": candidate.years_of_experience,
                "current_title": candidate.current_title,
                "location": candidate.location_city,
                "seniority": candidate.seniority_level
            }
            score_result = lia_svc.calculate_score(
                candidate=candidate_profile,
                search_criteria=vacancy_requirements
            )
            adherence_score = score_result.score
            candidate.lia_score = adherence_score
            candidate.skills_match_percentage = score_result.breakdown.skills_match
            candidate.lia_insights = score_result.to_dict()
        except Exception as e:
            logger.warning(f"Score calculation failed, using default: {e}")

        if adherence_score < ADHERENCE_THRESHOLD:
            return PublicApplicationResponse(
                status="low_adherence",
                message="Obrigado pela candidatura! Infelizmente seu perfil não atende aos requisitos mínimos desta vaga no momento. Recomendamos atualizar seu currículo e tentar novamente.",
                candidate_id=str(candidate.id),
                adherence_score=adherence_score,
                next_step="improve_profile"
            )

        existing_vc = await repo.get_vacancy_candidate(job.id, candidate.id)
        if existing_vc:
            return PublicApplicationResponse(
                status="already_applied",
                message="Você já se candidatou a esta vaga. Acompanhe seu email para atualizações.",
                candidate_id=str(candidate.id),
                adherence_score=adherence_score,
                next_step="wait_for_contact"
            )

        is_saturated = False
        try:
            company = None
            if job.company_id:
                company = await repo.get_company_profile(job.company_id)

            threshold_web = 20
            if company and company.additional_data:
                sat_settings = company.additional_data.get("saturation_settings", {})
                threshold_web = sat_settings.get("threshold_web", 20)

            governance = job.governance_rules or {}
            threshold_web = governance.get("threshold_web", threshold_web)

            organic_count = await repo.count_organic_candidates(job.id, SATURATION_EXCLUDED_STATUSES)
            is_saturated = organic_count >= threshold_web
        except Exception as e:
            logger.warning(f"Saturation check failed, allowing application: {e}")

        candidate_status = "awaiting_screening" if is_saturated else "applied"

        import secrets as _secrets
        screening_token = _secrets.token_urlsafe(32)

        vacancy_candidate = VacancyCandidate(
            id=uuid_lib.uuid4(),
            vacancy_id=job.id,
            candidate_id=candidate.id,
            company_id=str(job.company_id) if job.company_id else None,
            source="web_application",
            origin="web",
            lia_score=adherence_score,
            match_percentage=candidate.skills_match_percentage,
            status=candidate_status,
            stage="pending_gate1",
            additional_data={
                "screening_invite_token": screening_token,
                "applied_at": datetime.utcnow().isoformat(),
                "is_saturated_at_apply": is_saturated,
            },
        )
        await repo.add_vacancy_candidate(vacancy_candidate)

        # Agent Studio Fase 2.5 — Onda C1.3: emite candidate_applied no
        # platform.events para o motor event-driven (deployments on_apply).
        # REGRA 4: fail-soft mas LOUD. Multi-tenancy: company_id de
        # job.company_id (contexto tenant), NUNCA do payload do request.
        try:
            from app.shared.messaging.platform_events import (
                CandidateAppliedEvent,
                publish_platform_event,
            )

            await publish_platform_event(
                CandidateAppliedEvent(
                    company_id=str(job.company_id),
                    payload={
                        "candidate_id": str(candidate.id),
                        "vacancy_id": str(job.id),
                    },
                )
            )
        except Exception as _evt_err:  # noqa: BLE001
            logger.error(
                "[C1.3] publish candidate_applied (web) failed (apply prossegue): %s",
                _evt_err,
                exc_info=True,
            )

        try:
            await notification_service.create_notification(
                user_id="default_user",
                title="Nova candidatura via formulário web",
                message=f"{name} aplicou para {job.title} com aderência de {adherence_score:.0f}%",
                notification_type=NotificationType.SUCCESS,
                category="new_application",
                related_job_id=str(job.id),
                related_candidate_id=str(candidate.id),
                action_url=f"/candidates/{candidate.id}",
                action_label="Ver Candidato",
                db=repo.get_session()
            )
        except Exception as e:
            logger.warning(f"Notification creation failed: {e}")

        if is_saturated:
            return PublicApplicationResponse(
                status="queued",
                message="Obrigado pela candidatura! Seus dados foram registrados. Entraremos em contato em breve quando houver disponibilidade para a próxima etapa.",
                candidate_id=str(candidate.id),
                adherence_score=adherence_score,
                next_step="wait_in_queue"
            )

        return PublicApplicationResponse(
            status="applied",
            message="Candidatura enviada com sucesso! Você receberá um convite para a próxima etapa em breve.",
            candidate_id=str(candidate.id),
            adherence_score=adherence_score,
            next_step="screening"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing public application: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao processar candidatura. Tente novamente.")
