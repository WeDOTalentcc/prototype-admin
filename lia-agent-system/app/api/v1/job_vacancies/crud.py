from datetime import datetime
from typing import (
    Any,  # noqa: F401
    )
from uuid import UUID

from pydantic import Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.trial_enforcement import require_active_subscription_or_demo  # noqa: F401
from app.services.plan_limits_service import check_active_jobs_limit_or_demo  # noqa: F401

"""
CRUD routes: finalize, search, GET one, GET list, POST create, PUT update,
DELETE (archive), PATCH status, duplicate, clone, find-by-identifier.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from ._shared import *

router = APIRouter()


# ─── Finalize (conversational flow) ───────────────────────────────────────────

@router.post("/job-vacancies/finalize", response_model=FinalizeJobVacancyResponse)
async def finalize_job_vacancy(
    request: FinalizeJobVacancyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Finalize job vacancy creation from conversational flow."""
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Finalizing job vacancy: {request.job_vacancy_state.job_title} for company: {company_id}")

        if not request.job_vacancy_state.is_ready_for_publication():
            raise HTTPException(status_code=400, detail="Job vacancy is not ready for publication. Missing required fields.")

        job_vacancy = await job_vacancy_service.finalize_job_vacancy(
            state=request.job_vacancy_state,
            conversation_id=request.conversation_id,
            created_by=request.created_by,
            company_id=company_id,
            db=db,
            current_user=current_user,
            pipeline_template_id=getattr(request.job_vacancy_state, 'pipeline_template_id', None)
        )

        logger.info(f"Job vacancy finalized: {job_vacancy.id} - {job_vacancy.title}")

        job_id = str(job_vacancy.id)
        job_title = str(job_vacancy.title)
        job_status = str(job_vacancy.status)

        from app.domains.job_management.services.job_audit_service import job_audit_service
        await job_audit_service.log_creation(
            job_id=job_id,
            created_by=request.created_by,
            company_id=company_id,
            db=db,
            job_data={"title": job_title, "status": job_status},
        )

        return FinalizeJobVacancyResponse(
            success=True,
            job_vacancy_id=job_id,
            title=job_title,
            status=job_status,
            message=f"Vaga '{job_title}' criada com sucesso!"
        )

    except Exception as e:
        logger.error(f"Error finalizing job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Search ───────────────────────────────────────────────────────────────────

class JobVacancySearchItem(BaseModel):
    id: str
    job_id: str | None = None
    title: str
    status: str
    created_at: str
    description_preview: str | None = None


class JobVacancySearchResponse(BaseModel):
    items: list[JobVacancySearchItem]
    total_count: int
    has_more: bool


@router.get("/job-vacancies/search", response_model=JobVacancySearchResponse)
async def search_job_vacancies(
    query: str = Query("", min_length=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Search job vacancies by title or job_id."""
    try:
        company_id = get_user_company_id(current_user)
        offset = (page - 1) * page_size

        base_filter = JobVacancy.company_id == company_id

        if query and len(query) >= 2:
            search_term = f"%{query}%"
            search_filter = and_(
                base_filter,
                or_(
                    JobVacancy.title.ilike(search_term),
                    JobVacancy.job_id.ilike(search_term)
                )
            )
        else:
            search_filter = base_filter

        count_stmt = select(func.count(JobVacancy.id)).where(search_filter)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        stmt = (
            select(
                JobVacancy.id,
                JobVacancy.job_id,
                JobVacancy.title,
                JobVacancy.status,
                JobVacancy.created_at,
                JobVacancy.description
            )
            .where(search_filter)
            .order_by(JobVacancy.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            description_preview = None
            if row.description:
                description_preview = row.description[:150] + "..." if len(row.description) > 150 else row.description
            items.append(JobVacancySearchItem(
                id=str(row.id),
                job_id=row.job_id,
                title=row.title,
                status=row.status or "Rascunho",
                created_at=row.created_at.isoformat() if row.created_at else "",
                description_preview=description_preview
            ))

        return JobVacancySearchResponse(
            items=items,
            total_count=total_count,
            has_more=(offset + len(items)) < total_count
        )

    except Exception as e:
        logger.error(f"Error searching job vacancies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Archetypes (must be before param routes) ──────────────────────────────

class ArchetypeCandidateResponse(BaseModel):
    id: str
    name: str
    current_title: str | None = None
    years_experience: int | None = None
    skills: list[str] | None = []
    hired_at: str | None = None


class ArchetypeVacancyResponse(BaseModel):
    id: str
    title: str
    department: str | None = None
    closed_at: str | None = None
    hired_candidate: ArchetypeCandidateResponse | None = None


class ArchetypesResponse(BaseModel):
    vacancies: list[ArchetypeVacancyResponse]
    total: int


@router.get("/job-vacancies/archetypes", response_model=ArchetypesResponse)
async def get_archetypes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Get completed job vacancies with hired candidates for archetype search."""
    try:
        company_id = get_user_company_id(current_user)

        result = await db.execute(
            select(JobVacancy)
            .where(JobVacancy.status == "Concluída")
            .where(JobVacancy.company_id == company_id)
            .order_by(JobVacancy.closed_at.desc())
        )
        job_vacancies = result.scalars().all()

        archetypes = []
        for jv in job_vacancies:
            hired_data = jv.additional_data.get("hired_candidate") if jv.additional_data else None

            if not hired_data:
                tech_skills = []
                if jv.technical_requirements:
                    tech_skills = [tr.get("technology", "") for tr in jv.technical_requirements[:5] if tr.get("technology")]

                hired_data = {
                    "id": f"arch_{str(jv.id)[:8]}",
                    "name": f"Contratado - {jv.title}",
                    "current_title": jv.title,
                    "years_experience": 5 if jv.seniority_level in ["Sênior", "Especialista"] else 3 if jv.seniority_level == "Pleno" else 1,
                    "skills": tech_skills or (jv.requirements[:5] if jv.requirements else []),
                    "hired_at": jv.closed_at.isoformat() if jv.closed_at else None
                }

            archetype = ArchetypeVacancyResponse(
                id=str(jv.id),
                title=jv.title,
                department=jv.department,
                closed_at=jv.closed_at.isoformat() if jv.closed_at else None,
                hired_candidate=ArchetypeCandidateResponse(**hired_data)
            )
            archetypes.append(archetype)

        logger.info(f"Retrieved {len(archetypes)} archetypes")

        return ArchetypesResponse(vacancies=archetypes, total=len(archetypes))

    except Exception as e:
        logger.error(f"Error fetching archetypes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Find by identifier ────────────────────────────────────────────────────

class FindJobRequest(BaseModel):
    identifier: str = Field(..., description="Job ID, job_id code, or title to search for")


@router.post("/job-vacancies/find-by-identifier", response_model=None)
async def find_job_by_identifier(
    request: FindJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Find a job by ID, job_id code, or title."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    company_id = get_user_company_id(current_user)

    try:
        job = await job_clone_service.get_job_by_id_or_title(
            db=db,
            identifier=request.identifier,
            company_id=company_id
        )

        if not job:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {request.identifier}")

        summary = await job_clone_service.get_job_summary_for_clone(db, job.id)
        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET one ──────────────────────────────────────────────────────────────────

@router.get("/job-vacancies/{job_vacancy_id}", response_model=None)
async def get_job_vacancy(
    job_vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Get job vacancy by ID."""
    try:
        user_company = get_user_company_id(current_user)

        result = await db.execute(
            select(JobVacancy).where(
                JobVacancy.id == job_vacancy_id,
                JobVacancy.company_id == user_company
            )
        )
        job_vacancy = result.scalar_one_or_none()

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        user_email = (current_user.email or "").lower()
        user_id = str(current_user.id) if current_user.id else ""
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, 'role') else False
        jv_visibility = job_vacancy.visibility or "public"

        can_access = False
        if jv_visibility in ["public", "internal"]:
            can_access = True
        elif is_admin:
            can_access = True
        elif jv_visibility == "confidential":
            jv_created_by = (job_vacancy.created_by or "").lower()
            jv_recruiter_email = (job_vacancy.recruiter_email or "").lower()
            jv_access_list = [x.lower() for x in (job_vacancy.access_list or [])]
            if user_email == jv_created_by or user_email == jv_recruiter_email:
                can_access = True
            elif user_email in jv_access_list or user_id in (job_vacancy.access_list or []):
                can_access = True

        if not can_access:
            raise HTTPException(status_code=403, detail="Você não tem acesso a esta vaga")

        return {
            "id": str(job_vacancy.id),
            "title": job_vacancy.title,
            "department": job_vacancy.department,
            "location": job_vacancy.location,
            "work_model": job_vacancy.work_model,
            "seniority_level": job_vacancy.seniority_level,
            "status": job_vacancy.status,
            "is_confidential": job_vacancy.is_confidential,
            "salary_range": job_vacancy.salary_range,
            "technical_requirements": job_vacancy.technical_requirements,
            "languages": job_vacancy.languages,
            "behavioral_competencies": job_vacancy.behavioral_competencies,
            "interview_stages": job_vacancy.interview_stages,
            "screening_questions": job_vacancy.screening_questions,
            "disabled_eligibility_question_ids": job_vacancy.disabled_eligibility_question_ids or [],
            "timeline": job_vacancy.timeline,
            "governance_rules": job_vacancy.governance_rules,
            "whatsapp_template_type": job_vacancy.whatsapp_template_type,
            "screening_config": job_vacancy.screening_config,
            "screening_status": derive_screening_status(job_vacancy.screening_config),
            "enriched_jd": job_vacancy.enriched_jd,
            "created_at": job_vacancy.created_at.isoformat() if hasattr(job_vacancy.created_at, 'isoformat') else None,
            "updated_at": job_vacancy.updated_at.isoformat() if hasattr(job_vacancy.updated_at, 'isoformat') else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET list ────────────────────────────────────────────────────────────────

@router.get("/job-vacancies", response_model=None)
async def list_job_vacancies(
    status: str | None = None,
    visibility: str | None = None,
    skip: int = 0,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """List job vacancies with optional status filter."""
    try:
        company_id = get_user_company_id(current_user)
        user_email = current_user.email.lower() if current_user.email else ""
        user_id = str(current_user.id) if current_user.id else ""
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, 'role') else False

        query = select(JobVacancy).where(JobVacancy.company_id == company_id)

        if status:
            query = query.where(JobVacancy.status == status)

        if visibility:
            query = query.where(JobVacancy.visibility == visibility)

        query = query.offset(skip).limit(limit).order_by(JobVacancy.created_at.desc())

        result = await db.execute(query)
        all_vacancies = result.scalars().all()

        job_vacancies = []
        for jv in all_vacancies:
            jv_visibility = jv.visibility or "public"

            if jv_visibility in ["public", "internal"]:
                job_vacancies.append(jv)
                continue

            if is_admin:
                job_vacancies.append(jv)
                continue

            if jv_visibility == "confidential":
                jv_created_by = (jv.created_by or "").lower()
                jv_recruiter_email = (jv.recruiter_email or "").lower()
                jv_access_list = [x.lower() for x in (jv.access_list or [])]

                if user_email == jv_created_by or user_email == jv_recruiter_email:
                    job_vacancies.append(jv)
                elif user_email in jv_access_list or user_id in (jv.access_list or []):
                    job_vacancies.append(jv)

        return {
            "total": len(job_vacancies),
            "skip": skip,
            "limit": limit,
            "items": [
                {
                    "id": str(jv.id),
                    "title": jv.title,
                    "department": jv.department,
                    "location": jv.location,
                    "work_model": jv.work_model,
                    "employment_type": jv.employment_type,
                    "seniority_level": jv.seniority_level,
                    "description": jv.description,
                    "requirements": jv.requirements or [],
                    "technical_requirements": jv.technical_requirements or [],
                    "languages": jv.languages or [],
                    "behavioral_competencies": jv.behavioral_competencies or [],
                    "salary_range": jv.salary_range,
                    "benefits": jv.benefits or [],
                    "manager": jv.manager,
                    "manager_email": jv.manager_email,
                    "recruiter": jv.recruiter,
                    "recruiter_email": jv.recruiter_email,
                    "is_confidential": jv.is_confidential or False,
                    "visibility": jv.visibility or "public",
                    "access_list": jv.access_list or [],
                    "masked_company_name": jv.masked_company_name,
                    "exclude_from_sync": jv.exclude_from_sync or False,
                    "created_by": jv.created_by,
                    "status": jv.status or "Rascunho",
                    "stage": jv.stage,
                    "priority": jv.priority or "média",
                    "created_at": jv.created_at.isoformat() if hasattr(jv.created_at, 'isoformat') else None,
                    "updated_at": jv.updated_at.isoformat() if hasattr(jv.updated_at, 'isoformat') else None,
                    "deadline": jv.deadline.isoformat() if hasattr(jv, 'deadline') and jv.deadline else None,
                    "funnel_data": jv.funnel_data,
                    "lia_metrics": jv.lia_metrics or generate_lia_metrics(jv.funnel_data),
                    "nps": jv.nps,
                    "budget": jv.budget,
                    "budget_used": jv.budget_used,
                    "published_linkedin": jv.published_linkedin or False,
                    "published_website": jv.published_website or False,
                    "next_actions": jv.next_actions or [],
                    "urgency_level": jv.urgency_level,
                    "approval_status": jv.approval_status,
                    "tags": jv.tags or [],
                    "salary": jv.salary,
                    "screening_questions": jv.screening_questions or [],
                    "interview_stages": jv.interview_stages or [],
                    "eligibility_questions": jv.eligibility_questions or [],
                    "disabled_eligibility_question_ids": jv.disabled_eligibility_question_ids or [],
                    "confidentiality_config": jv.confidentiality_config,
                    "conversation_id": str(jv.conversation_id) if jv.conversation_id else None,
                    "screening_config": jv.screening_config,
                    "screening_status": derive_screening_status(jv.screening_config),
                    "enriched_jd": jv.enriched_jd,
                    "is_affirmative": jv.is_affirmative or False,
                    "affirmative_criteria_primary": jv.affirmative_criteria_primary,
                    "affirmative_criteria_secondary": jv.affirmative_criteria_secondary,
                    "affirmative_description": jv.affirmative_description,
                    "affirmative_document_required": jv.affirmative_document_required or False,
                    "affirmative_document_types": jv.affirmative_document_types or [],
                }
                for jv in job_vacancies
            ]
        }

    except Exception as e:
        logger.error(f"Error listing job vacancies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST create ──────────────────────────────────────────────────────────────

@router.post("/job-vacancies", response_model=JobVacancyResponse)
async def create_job_vacancy(
    job_data: JobVacancyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    _trial_check: None = Depends(require_active_subscription_or_demo),
    _plan_check: None = Depends(check_active_jobs_limit_or_demo),
):
    """Create a new job vacancy directly (not via conversation)."""
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Creating job vacancy: {job_data.title} for company: {company_id}")

        job_vacancy = JobVacancy(
            id=uuid_lib.uuid4(),
            title=job_data.title,
            department=job_data.department,
            location=job_data.location,
            work_model=job_data.work_model,
            employment_type=job_data.employment_type,
            seniority_level=job_data.seniority_level,
            description=job_data.description,
            requirements=job_data.requirements or [],
            technical_requirements=job_data.technical_requirements or [],
            languages=job_data.languages or [],
            behavioral_competencies=job_data.behavioral_competencies or [],
            salary=job_data.salary,
            salary_range=job_data.salary_range,
            benefits=job_data.benefits or [],
            manager=job_data.manager,
            manager_email=job_data.manager_email,
            recruiter=job_data.recruiter,
            recruiter_email=job_data.recruiter_email,
            is_confidential=job_data.is_confidential,
            visibility=job_data.visibility,
            access_list=job_data.access_list or [],
            masked_company_name=job_data.masked_company_name,
            exclude_from_sync=job_data.exclude_from_sync,
            status=job_data.status,
            priority=job_data.priority,
            screening_questions=job_data.screening_questions or [],
            interview_stages=job_data.interview_stages or [],
            disabled_eligibility_question_ids=job_data.disabled_eligibility_question_ids or [],
            conversation_id=uuid_lib.UUID(job_data.conversation_id) if job_data.conversation_id else None,
            company_id=company_id,
            created_by=str(current_user.id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(job_vacancy)
        await db.flush()
        await db.refresh(job_vacancy)

        logger.info(f"Job vacancy created: {job_vacancy.id} - {job_vacancy.title}")

        return JobVacancyResponse(
            id=str(job_vacancy.id),
            title=job_vacancy.title,
            department=job_vacancy.department,
            location=job_vacancy.location,
            work_model=job_vacancy.work_model,
            employment_type=job_vacancy.employment_type,
            seniority_level=job_vacancy.seniority_level,
            description=job_vacancy.description,
            requirements=job_vacancy.requirements or [],
            technical_requirements=job_vacancy.technical_requirements or [],
            languages=job_vacancy.languages or [],
            behavioral_competencies=job_vacancy.behavioral_competencies or [],
            salary=job_vacancy.salary,
            salary_range=job_vacancy.salary_range,
            benefits=job_vacancy.benefits or [],
            manager=job_vacancy.manager,
            manager_email=job_vacancy.manager_email,
            recruiter=job_vacancy.recruiter,
            recruiter_email=job_vacancy.recruiter_email,
            is_confidential=job_vacancy.is_confidential or False,
            status=job_vacancy.status or "Rascunho",
            priority=job_vacancy.priority or "média",
            created_at=job_vacancy.created_at.isoformat() if job_vacancy.created_at else None,
            updated_at=job_vacancy.updated_at.isoformat() if job_vacancy.updated_at else None,
            screening_questions=job_vacancy.screening_questions or [],
            interview_stages=job_vacancy.interview_stages or [],
            disabled_eligibility_question_ids=job_vacancy.disabled_eligibility_question_ids or [],
            conversation_id=str(job_vacancy.conversation_id) if job_vacancy.conversation_id else None
        )

    except Exception as e:
        logger.error(f"Error creating job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── PUT update ───────────────────────────────────────────────────────────────

@router.put("/job-vacancies/{job_vacancy_id}", response_model=JobVacancyResponse)
async def update_job_vacancy(
    job_vacancy_id: UUID,
    job_data: JobVacancyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Update an existing job vacancy."""
    try:
        logger.info(f"Updating job vacancy: {job_vacancy_id}")

        user_company = get_user_company_id(current_user)

        query = select(JobVacancy).where(
            JobVacancy.id == job_vacancy_id,
            JobVacancy.company_id == user_company
        )

        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        update_data = job_data.model_dump(exclude_unset=True, exclude_none=True)
        update_data["updated_at"] = datetime.utcnow()

        changes = {}
        for field, value in update_data.items():
            if field == "updated_at":
                continue
            if hasattr(job_vacancy, field):
                old_value = getattr(job_vacancy, field)
                if old_value != value:
                    changes[field] = {"old": old_value, "new": value}
                setattr(job_vacancy, field, value)

        if changes:
            from app.domains.job_management.services.job_audit_service import job_audit_service
            changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
            await job_audit_service.log_update(
                job_id=str(job_vacancy_id),
                changes=changes,
                changed_by=changed_by,
                company_id=user_company,
                db=db,
            )

        await db.flush()
        await db.refresh(job_vacancy)

        logger.info(f"Job vacancy updated: {job_vacancy.id} - {job_vacancy.title} ({len(changes)} fields changed)")

        return JobVacancyResponse(
            id=str(job_vacancy.id),
            title=job_vacancy.title,
            department=job_vacancy.department,
            location=job_vacancy.location,
            work_model=job_vacancy.work_model,
            employment_type=job_vacancy.employment_type,
            seniority_level=job_vacancy.seniority_level,
            description=job_vacancy.description,
            requirements=job_vacancy.requirements or [],
            technical_requirements=job_vacancy.technical_requirements or [],
            languages=job_vacancy.languages or [],
            behavioral_competencies=job_vacancy.behavioral_competencies or [],
            salary=job_vacancy.salary,
            salary_range=job_vacancy.salary_range,
            benefits=job_vacancy.benefits or [],
            manager=job_vacancy.manager,
            manager_email=job_vacancy.manager_email,
            recruiter=job_vacancy.recruiter,
            recruiter_email=job_vacancy.recruiter_email,
            is_confidential=job_vacancy.is_confidential or False,
            status=job_vacancy.status or "Rascunho",
            priority=job_vacancy.priority or "média",
            created_at=job_vacancy.created_at.isoformat() if job_vacancy.created_at else None,
            updated_at=job_vacancy.updated_at.isoformat() if job_vacancy.updated_at else None,
            screening_questions=job_vacancy.screening_questions or [],
            interview_stages=job_vacancy.interview_stages or [],
            disabled_eligibility_question_ids=job_vacancy.disabled_eligibility_question_ids or [],
            conversation_id=str(job_vacancy.conversation_id) if job_vacancy.conversation_id else None,
            enriched_jd=job_vacancy.enriched_jd
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── DELETE (soft) ───────────────────────────────────────────────────────────

@router.delete("/job-vacancies/{job_vacancy_id}", response_model=None)
async def delete_job_vacancy(
    job_vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a job vacancy (soft delete - sets status to 'Arquivada')."""
    try:
        logger.info(f"Deleting job vacancy: {job_vacancy_id}")

        user_company = get_user_company_id(current_user)

        query = select(JobVacancy).where(
            JobVacancy.id == job_vacancy_id,
            JobVacancy.company_id == user_company
        )

        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        job_vacancy.status = "Arquivada"
        job_vacancy.updated_at = datetime.utcnow()

        from app.domains.job_management.services.job_audit_service import job_audit_service
        changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
        await job_audit_service.log_archive(
            job_id=str(job_vacancy_id),
            changed_by=changed_by,
            company_id=user_company,
            db=db,
        )


        logger.info(f"Job vacancy archived: {job_vacancy_id}")

        return {
            "success": True,
            "message": f"Vaga '{job_vacancy.title}' arquivada com sucesso",
            "id": str(job_vacancy_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── PATCH status ─────────────────────────────────────────────────────────────

@router.patch("/job-vacancies/{job_vacancy_id}/status", response_model=None)
async def update_job_vacancy_status(
    job_vacancy_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update job vacancy status."""
    try:
        valid_statuses = ["Rascunho", "Ativa", "Pausada", "Concluída", "Arquivada"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid options: {', '.join(valid_statuses)}"
            )

        user_company = get_user_company_id(current_user)

        query = select(JobVacancy).where(
            JobVacancy.id == job_vacancy_id,
            JobVacancy.company_id == user_company
        )

        result = await db.execute(query)
        job_vacancy = result.scalar_one_or_none()

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        old_status = job_vacancy.status
        job_vacancy.status = status
        job_vacancy.updated_at = datetime.utcnow()

        from app.domains.job_management.services.job_audit_service import job_audit_service
        changed_by = str(current_user.email) if hasattr(current_user, 'email') else str(current_user.id)
        await job_audit_service.log_status_change(
            job_id=str(job_vacancy_id),
            old_status=old_status,
            new_status=status,
            changed_by=changed_by,
            company_id=user_company,
            db=db,
        )


        logger.info(f"Job vacancy status updated: {job_vacancy_id} ({old_status} -> {status})")

        try:
            await job_status_webhook_service.dispatch_status_change(
                job_id=str(job_vacancy_id),
                old_status=old_status,
                new_status=status,
                company_id=user_company,
                db=db,
                changed_by=changed_by,
                job_title=job_vacancy.title
            )
        except Exception as webhook_error:
            logger.warning(f"Webhook dispatch failed (non-blocking): {webhook_error}")

        return {
            "success": True,
            "id": str(job_vacancy_id),
            "old_status": old_status,
            "new_status": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job vacancy status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Duplicate / Clone ────────────────────────────────────────────────────────

class DuplicateJobRequest(BaseModel):
    copies: int = Field(default=1, ge=1, le=10)
    include_candidates: bool = Field(default=True)
    candidate_filter: str | None = Field(default=None)
    candidate_status_override: str | None = Field(default=None)
    overrides: dict[str, Any] | None = Field(default=None)


class CloneFromTemplateRequest(BaseModel):
    new_title: str | None = Field(default=None)
    overrides: dict[str, Any] | None = Field(default=None)


@router.post("/job-vacancies/{job_id}/duplicate", response_model=None)
async def duplicate_job(
    job_id: UUID,
    request: DuplicateJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Duplicate a job vacancy with all its data."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    company_id = get_user_company_id(current_user)

    try:
        logger.info(f"Duplicating job {job_id} with {request.copies} copies")

        result = await job_clone_service.duplicate_job(
            db=db,
            source_job_id=job_id,
            copies=request.copies,
            include_candidates=request.include_candidates,
            candidate_filter=request.candidate_filter,
            candidate_status_override=request.candidate_status_override,
            overrides=request.overrides,
            created_by=current_user.email if hasattr(current_user, 'email') else "demo@wedotalent.com",
            company_id=company_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to duplicate job"))

        logger.info(f"Created {result['total_jobs_created']} duplicate jobs from {job_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-vacancies/{job_id}/clone-from-template", response_model=None)
async def clone_from_template(
    job_id: UUID,
    request: CloneFromTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Create a new job using an existing job as a template (no candidates)."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    company_id = get_user_company_id(current_user)

    try:
        logger.info(f"Creating job from template {job_id}")

        result = await job_clone_service.clone_from_template(
            db=db,
            source_job_id=job_id,
            new_title=request.new_title,
            overrides=request.overrides,
            created_by=current_user.email if hasattr(current_user, 'email') else "demo@wedotalent.com",
            company_id=company_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to create from template"))

        logger.info(f"Created job from template: {result['created_job']['title']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{job_id}/clone-summary", response_model=None)
async def get_clone_summary(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a summary of a job for displaying before cloning."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    try:
        summary = await job_clone_service.get_job_summary_for_clone(db, job_id)

        if not summary:
            raise HTTPException(status_code=404, detail=f"Vaga não encontrada: {job_id}")

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clone summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))