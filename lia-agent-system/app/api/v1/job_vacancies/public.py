"""
Public routes (no authentication required) and share-link routes.
Also includes router_public for candidate application flow.
"""
from fastapi import APIRouter
from ._shared import *

router = APIRouter()
router_public = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class GeneratePublicLinkRequest(BaseModel):
    regenerate: bool = False


class GeneratePublicLinkResponse(BaseModel):
    success: bool
    public_url: str
    slug: str
    message: str


class ShareLinkResponse(BaseModel):
    share_link: str
    slug: str
    qr_code_url: Optional[str] = None
    expires_at: Optional[str] = None
    view_count: int = 0


class PublicVacancyResponse(BaseModel):
    title: str
    description: Optional[str] = None
    requirements: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    location: Optional[str] = None
    work_model: Optional[str] = None
    employment_type: Optional[str] = None
    seniority_level: Optional[str] = None
    department: Optional[str] = None
    company_name: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_logo: Optional[str] = None
    is_confidential: bool = False
    is_affirmative: bool = False
    technical_requirements: Optional[List[dict]] = []
    languages: Optional[List[dict]] = []
    behavioral_competencies: Optional[List[dict]] = []
    salary_range: Optional[dict] = None
    apply_url: Optional[str] = None


class PublicApplicationResponse(BaseModel):
    status: str
    message: str
    candidate_id: Optional[str] = None
    adherence_score: Optional[float] = None
    next_step: Optional[str] = None


# ─── Authenticated share-link routes ─────────────────────────────────────────

@router.post("/job-vacancies/{vacancy_id}/generate-public-link", response_model=GeneratePublicLinkResponse)
async def generate_public_link(
    vacancy_id: UUID,
    request: GeneratePublicLinkRequest = GeneratePublicLinkRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Generate or retrieve public sharing link for a job vacancy."""
    try:
        company_id = get_user_company_id(current_user)

        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == vacancy_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()

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

        existing = await db.execute(
            select(JobVacancy.id).where(JobVacancy.public_slug == new_slug)
        )
        if existing.scalar_one_or_none():
            new_slug = generate_slug(job.title, secrets.token_hex(2))

        job.public_slug = new_slug
        job.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(job)

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
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{vacancy_id}/share-link", response_model=ShareLinkResponse)
async def get_share_link(
    vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Get shareable link details for a job vacancy."""
    try:
        company_id = get_user_company_id(current_user)

        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == vacancy_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden":
            raise HTTPException(status_code=403, detail="Vagas ocultas não podem ter link público")

        if not job.public_slug:
            company_short = ""
            if job.masked_company_name:
                company_short = job.masked_company_name[:30]

            new_slug = generate_slug(job.title, company_short)

            existing = await db.execute(
                select(JobVacancy.id).where(JobVacancy.public_slug == new_slug)
            )
            if existing.scalar_one_or_none():
                new_slug = generate_slug(job.title, secrets.token_hex(2))

            job.public_slug = new_slug
            job.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(job)
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
    db: AsyncSession = Depends(get_db)
):
    """Get public vacancy information by slug (no authentication required)."""
    try:
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.public_slug == slug)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden" or job.status not in ["Ativa", "Publicada"]:
            raise HTTPException(status_code=404, detail="Vaga não disponível")

        job.view_count = (job.view_count or 0) + 1
        await db.commit()

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
    db: AsyncSession = Depends(get_db)
):
    try:
        if lgpd_consent.lower() not in ("true", "1", "yes", "sim"):
            raise HTTPException(
                status_code=400,
                detail="Consentimento LGPD obrigatório para prosseguir."
            )

        result = await db.execute(
            select(JobVacancy).where(JobVacancy.public_slug == slug)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        if job.visibility == "hidden" or job.status not in ["Ativa", "Publicada", "open", "active", "published"]:
            raise HTTPException(status_code=400, detail="Esta vaga não está aberta para candidaturas")

        cv_content = await cv_file.read()
        parsed_cv = {}
        try:
            from app.domains.cv_screening.services.cv_parser import cv_parser_service
            parsed_cv = await cv_parser_service.parse_cv(
                file_content=cv_content,
                filename=cv_file.filename
            )
        except Exception as e:
            logger.warning(f"CV parsing failed, continuing without parsed data: {e}")

        result = await db.execute(
            select(Candidate).where(Candidate.email == email)
        )
        existing_candidate = result.scalar_one_or_none()

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
            db.add(candidate)

        await db.flush()

        adherence_score = 70.0
        try:
            from app.services.lia_score_service import LIAScoreService
            lia_svc = LIAScoreService()
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
            await db.commit()
            return PublicApplicationResponse(
                status="low_adherence",
                message="Obrigado pela candidatura! Infelizmente seu perfil não atende aos requisitos mínimos desta vaga no momento. Recomendamos atualizar seu currículo e tentar novamente.",
                candidate_id=str(candidate.id),
                adherence_score=adherence_score,
                next_step="improve_profile"
            )

        existing_vc = await db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == job.id,
                VacancyCandidate.candidate_id == candidate.id
            )
        )
        if existing_vc.scalar_one_or_none():
            await db.commit()
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
                cr = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.id == job.company_id)
                )
                company = cr.scalar_one_or_none()

            threshold_web = 20
            if company and company.additional_data:
                sat_settings = company.additional_data.get("saturation_settings", {})
                threshold_web = sat_settings.get("threshold_web", 20)

            governance = job.governance_rules or {}
            threshold_web = governance.get("threshold_web", threshold_web)

            active_filter = and_(
                VacancyCandidate.vacancy_id == job.id,
                not_(VacancyCandidate.status.in_(SATURATION_EXCLUDED_STATUSES)),
                VacancyCandidate.origin.in_(("web", "whatsapp"))
            )
            count_result = await db.execute(
                select(func.count(VacancyCandidate.id)).where(active_filter)
            )
            organic_count = count_result.scalar() or 0
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
        db.add(vacancy_candidate)

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
                db=db
            )
        except Exception as e:
            logger.warning(f"Notification creation failed: {e}")

        await db.commit()

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
