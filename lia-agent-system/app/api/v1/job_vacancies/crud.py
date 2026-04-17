import uuid as uuid_lib
from datetime import datetime
from typing import Any, Union, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from app.auth.models import UserRole
from app.middleware.trial_enforcement import require_active_subscription_or_demo  # noqa: F401
from app.shared.services.plan_limits_service import check_active_jobs_limit_or_demo  # noqa: F401

"""
CRUD routes: finalize, search, GET one, GET list, POST create, PUT update,
DELETE (archive), PATCH status, duplicate, clone, find-by-identifier.
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from ._shared import *
from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository
from app.domains.job_management.dependencies import get_job_vacancy_crud_repo
from app.domains.integrations_hub.services.rails_adapter import RailsAdapter, RAILS_ENABLED
from app.domains.integrations_hub.services.rails_adapter_dependency import get_rails_adapter
from app.shared.rails_migration.deprecation import enforce_job_vacancies_deprecation

# MIGRATION_PLAN item 7.1 — Python CRUD deprecated in favor of Rails (ats-api-copia).
#
# The 13 endpoints below are kept as a compatibility shim during the transition.
# Every request gets logged with a deprecation warning and a `Sunset` header
# pointing at the retirement date. Flip `STRICT_RAILS_ONLY=true` in the
# environment to turn all routes below into HTTP 410 Gone with a pointer at
# the Rails endpoint — this lets us kill-switch the old API without a deploy.
router = APIRouter(
    dependencies=[Depends(enforce_job_vacancies_deprecation)],
)


# ─── Finalize (conversational flow) ───────────────────────────────────────────

# ─── Response schemas for CRUD endpoints ─────────────────────────────────────

class JobVacancyDetailResponse(BaseModel):
    """Response for GET /job-vacancies/{id} — explicit typed contract."""
    id: str
    title: str | None = None
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    seniority_level: str | None = None
    status: str | None = None
    is_confidential: bool | None = None
    salary_range: dict | None = None
    technical_requirements: list[Union[str, dict]] | None = None
    languages: list[Union[str, dict]] | None = None
    behavioral_competencies: list[Union[str, dict]] | None = None
    interview_stages: list[dict] | None = None
    screening_questions: list[dict] | None = None
    disabled_eligibility_question_ids: list[str] = []
    timeline: dict | None = None
    governance_rules: dict | None = None
    whatsapp_template_type: str | None = None
    screening_config: dict | None = None
    screening_status: str | None = None
    enriched_jd: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None


class JobVacancyListItemResponse(BaseModel):
    """Single item in list response for GET /job-vacancies."""
    model_config = ConfigDict(extra='allow')
    id: str
    title: str | None = None
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    requirements: list[Union[str, dict]] = []
    technical_requirements: list[Union[str, dict]] = []
    languages: list[Union[str, dict]] = []
    behavioral_competencies: list[Union[str, dict]] = []
    salary_range: dict | None = None
    benefits: list[Union[str, dict]] = []
    manager: str | None = None
    status: str | None = None
    visibility: str | None = None
    is_confidential: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


class JobVacancyListResponse(BaseModel):
    """Response for GET /job-vacancies."""
    total: int
    skip: int
    limit: int
    items: list[JobVacancyListItemResponse]
    source: str | None = None


class JobVacancyDeleteResponse(BaseModel):
    """Response for DELETE /job-vacancies/{id}."""
    success: bool
    message: str
    id: str


class JobVacancyStatusUpdateResponse(BaseModel):
    """Response for PATCH /job-vacancies/{id}/status."""
    success: bool
    id: str
    old_status: str
    new_status: str


class DuplicateJobResponse(BaseModel):
    """Response for POST /job-vacancies/{id}/duplicate."""
    model_config = ConfigDict(extra='allow')
    success: bool
    total_jobs_created: int | None = None


class CloneFromTemplateResponse(BaseModel):
    """Response for POST /job-vacancies/{id}/clone-from-template."""
    model_config = ConfigDict(extra='allow')
    success: bool
    created_job: dict | None = None


class CloneSummaryResponse(BaseModel):
    """Response for GET /job-vacancies/{id}/clone-summary."""
    model_config = ConfigDict(extra='allow')
    id: str | None = None
    title: str | None = None


class FindJobResponse(BaseModel):
    """Response for POST /job-vacancies/find-by-identifier."""
    model_config = ConfigDict(extra='allow')
    id: str | None = None
    title: str | None = None



@router.post("/job-vacancies/finalize", response_model=FinalizeJobVacancyResponse)
async def finalize_job_vacancy(
    request: FinalizeJobVacancyRequest,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_active_user)
):
    """Finalize job vacancy creation from conversational flow."""
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Finalizing job vacancy: {request.job_vacancy_state.job_title} for company: {company_id}")

        if not request.job_vacancy_state.is_ready_for_publication():
            raise HTTPException(status_code=400, detail="Job vacancy is not ready for publication. Missing required fields.")

        # Task #358: block discriminatory text on the conversational
        # finalize path too — the wizard ultimately writes the same
        # JobVacancy row as the direct POST endpoint.
        state = request.job_vacancy_state
        fairness_warnings = run_fairness_guard_on_jd(
            title=state.job_title,
            description=(
                state.job_description_generated
                or state.description
            ),
            requirements=getattr(state, "required_skills", None),
            technical_requirements=[
                tr.model_dump() if hasattr(tr, "model_dump") else tr
                for tr in (state.technical_requirements or [])
            ],
            context="job_vacancy_finalize",
        )

        db = repo.get_session()
        job_vacancy = await job_vacancy_service.finalize_job_vacancy(
            state=request.job_vacancy_state,
            conversation_id=request.conversation_id,
            created_by=request.created_by,
            company_id=company_id,
            db=db,
            current_user=current_user,
            pipeline_template_id=getattr(request.job_vacancy_state, "pipeline_template_id", None)
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
            message=f"Vaga \{job_title}\ criada com sucesso!",
            fairness_warnings=fairness_warnings or None,
        )

    except HTTPException:
        raise
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
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Search job vacancies by title or job_id."""
    try:
        company_id = get_user_company_id(current_user)
        offset = (page - 1) * page_size

        total_count, rows = await repo.search_by_query(company_id, query, offset, page_size)

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

    except HTTPException:
        raise
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
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Get completed job vacancies with hired candidates for archetype search."""
    try:
        company_id = get_user_company_id(current_user)

        job_vacancies = await repo.get_completed_vacancies(company_id)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching archetypes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Find by identifier ────────────────────────────────────────────────────

class FindJobRequest(BaseModel):
    identifier: str = Field(..., description="Job ID, job_id code, or title to search for")


@router.post("/job-vacancies/find-by-identifier", response_model=FindJobResponse)
async def find_job_by_identifier(
    request: FindJobRequest,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Find a job by ID, job_id code, or title."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    company_id = get_user_company_id(current_user)
    db = repo.get_session()

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

@router.get("/job-vacancies/{job_vacancy_id}", response_model=JobVacancyDetailResponse)
async def get_job_vacancy(
    job_vacancy_id: str,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
):
    """Get job vacancy by ID. Accepts UUID (local) or integer string (Rails bigint).
    When RAILS_API_URL is configured and the ID looks like a Rails bigint, queries Rails first.
    Falls back to local DB with company/visibility authorization when Rails is disabled or ID is a UUID.
    """
    try:
        # When Rails is enabled and the ID is a bigint (Rails-style), try Rails first.
        # UUID-style IDs are always served from local DB with full authorization checks.
        # Any failure inside the Rails branch (network, parsing, mapping) must fall through
        # to the local DB path instead of bubbling up as a 500 — the bridge being unavailable
        # cannot block normal use of locally-stored vacancies (Task #241).
        if RAILS_ENABLED and job_vacancy_id.isdigit():
            try:
                rails_job = await rails_adapter.get_job_from_rails_only(job_vacancy_id)
            except Exception as bridge_err:  # noqa: BLE001 — bridge isolation
                logger.warning(
                    "[get_job_vacancy] Rails bridge failed for job %s, falling back to local DB: %s",
                    job_vacancy_id, bridge_err,
                )
                rails_job = None
            if rails_job:
                # Apply visibility/confidentiality checks equivalent to local path.
                # Rails is the authoritative auth source for its own data, but we
                # enforce confidentiality rules here as a defense-in-depth layer.
                jv_visibility = rails_job.get("visibility", "public")
                is_admin = current_user.role == UserRole.admin if hasattr(current_user, "role") else False
                can_access = jv_visibility in ("public", "internal") or is_admin
                if not can_access and jv_visibility == "confidential":
                    user_email = (current_user.email or "").lower()
                    user_id = str(current_user.id) if current_user.id else ""
                    jv_created_by = (rails_job.get("created_by") or "").lower()
                    jv_recruiter_email = (rails_job.get("recruiter_email") or "").lower()
                    jv_access_list = [x.lower() for x in (rails_job.get("access_list") or [])]
                    if user_email in (jv_created_by, jv_recruiter_email) or \
                       user_email in jv_access_list or user_id in (rails_job.get("access_list") or []):
                        can_access = True
                if not can_access:
                    raise HTTPException(status_code=403, detail="Você não tem acesso a esta vaga")
                logger.debug("[get_job_vacancy] Returning job %s from Rails", job_vacancy_id)
                return rails_job

        # Parse as UUID for local repository lookup
        try:
            job_vacancy_uuid = UUID(job_vacancy_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        user_company = get_user_company_id(current_user)

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_vacancy_uuid, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        user_email = (current_user.email or "").lower()
        user_id = str(current_user.id) if current_user.id else ""
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, "role") else False
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
            "created_at": job_vacancy.created_at.isoformat() if hasattr(job_vacancy.created_at, "isoformat") else None,
            "updated_at": job_vacancy.updated_at.isoformat() if hasattr(job_vacancy.updated_at, "isoformat") else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET list ────────────────────────────────────────────────────────────────

@router.get("/job-vacancies", response_model=JobVacancyListResponse)
async def list_job_vacancies(
    status: str | None = None,
    visibility: str | None = None,
    skip: int = 0,
    limit: int = 500,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
):
    """List job vacancies. When RAILS_API_URL is configured, tries Rails first then local DB."""
    try:
        # Only query Rails when explicitly enabled — never let the adapter's own DB fallback
        # bypass company/visibility scoping and authorization done in the local path below.
        user_email = current_user.email.lower() if current_user.email else ""
        user_id = str(current_user.id) if current_user.id else ""
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, "role") else False

        rails_bridge_failed = False
        if RAILS_ENABLED:
            page = skip // limit + 1 if limit else 1
            # Bridge isolation: any failure inside the Rails branch (network, parsing,
            # mapping, unexpected formats) must fall through to the local DB rather than
            # surfacing as a 500. The frontend depends on this endpoint being resilient
            # so newly-created vacancies remain navigable when Rails is misconfigured
            # or unavailable (Task #241).
            try:
                rails_jobs = await rails_adapter.list_jobs_from_rails_only(
                    page=page,
                    limit=limit,
                    status=status,
                    visibility=visibility,
                )
            except Exception as bridge_err:  # noqa: BLE001 — bridge isolation
                logger.warning(
                    "[list_job_vacancies] Rails bridge failed, falling back to local DB: %s",
                    bridge_err,
                )
                rails_jobs = None
                rails_bridge_failed = True
            if rails_jobs is not None:
                # Apply the same confidentiality/visibility filtering used in the local DB path.
                # This is a defense-in-depth layer — Rails may enforce its own access control,
                # but we must be consistent with our own security model.
                filtered: list[dict] = []
                for jv in rails_jobs:
                    jv_visibility = (jv.get("visibility") or "public")

                    if jv_visibility in ("public", "internal"):
                        filtered.append(jv)
                        continue

                    if is_admin:
                        filtered.append(jv)
                        continue

                    if jv_visibility == "confidential":
                        jv_created_by = (jv.get("created_by") or "").lower()
                        jv_recruiter_email = (jv.get("recruiter_email") or "").lower()
                        jv_access_list = [x.lower() for x in (jv.get("access_list") or [])]
                        if (user_email in (jv_created_by, jv_recruiter_email)
                                or user_email in jv_access_list
                                or user_id in (jv.get("access_list") or [])):
                            filtered.append(jv)

                logger.debug(
                    "[list_job_vacancies] Rails returned %d jobs; %d visible after auth filter",
                    len(rails_jobs), len(filtered),
                )
                return {
                    "total": len(filtered),
                    "skip": skip,
                    "limit": limit,
                    "items": filtered,
                }

        company_id = get_user_company_id(current_user)

        all_vacancies = await repo.list_vacancies(
            company_id=company_id,
            status=status,
            visibility=visibility,
            skip=skip,
            limit=limit,
        )

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
            "source": "local-fallback" if rails_bridge_failed else None,
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
                    "created_at": jv.created_at.isoformat() if hasattr(jv.created_at, "isoformat") else None,
                    "updated_at": jv.updated_at.isoformat() if hasattr(jv.updated_at, "isoformat") else None,
                    "deadline": jv.deadline.isoformat() if hasattr(jv, "deadline") and jv.deadline else None,
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing job vacancies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── POST create ──────────────────────────────────────────────────────────────

@router.post("/job-vacancies", response_model=JobVacancyResponse)
async def create_job_vacancy(
    job_data: JobVacancyCreate,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo),
    _trial_check: None = Depends(require_active_subscription_or_demo),
    _plan_check: None = Depends(check_active_jobs_limit_or_demo),
):
    """Create a new job vacancy directly (not via conversation)."""
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Creating job vacancy: {job_data.title} for company: {company_id}")

        # Task #358: refuse to persist a discriminatory JD. Soft warnings
        # (implicit-bias) are surfaced on the response without blocking.
        fairness_warnings = run_fairness_guard_on_jd(
            title=job_data.title,
            description=job_data.description,
            requirements=job_data.requirements,
            technical_requirements=job_data.technical_requirements,
            behavioral_competencies=job_data.behavioral_competencies,
            languages=job_data.languages,
            context="job_vacancy_create",
        )

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

        job_vacancy = await repo.create_vacancy(job_vacancy)

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
            conversation_id=str(job_vacancy.conversation_id) if job_vacancy.conversation_id else None,
            fairness_warnings=fairness_warnings or None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── PUT update ───────────────────────────────────────────────────────────────

@router.put("/job-vacancies/{job_vacancy_id}", response_model=JobVacancyResponse)
async def update_job_vacancy(
    job_vacancy_id: UUID,
    job_data: JobVacancyUpdate,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Update an existing job vacancy."""
    try:
        logger.info(f"Updating job vacancy: {job_vacancy_id}")

        user_company = get_user_company_id(current_user)
        db = repo.get_session()

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_vacancy_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        update_data = job_data.model_dump(exclude_unset=True, exclude_none=True)

        # Task #358: re-run FairnessGuard whenever any user-authored JD
        # field is being changed. Use the *post-update* value so a partial
        # PATCH (e.g. only description) still gets the full text checked.
        jd_fields = {
            "title", "description", "requirements", "technical_requirements",
            "behavioral_competencies", "languages",
        }
        fairness_warnings: list[str] = []
        if jd_fields & update_data.keys():
            fairness_warnings = run_fairness_guard_on_jd(
                title=update_data.get("title", job_vacancy.title),
                description=update_data.get("description", job_vacancy.description),
                requirements=update_data.get("requirements", job_vacancy.requirements),
                technical_requirements=update_data.get(
                    "technical_requirements", job_vacancy.technical_requirements
                ),
                behavioral_competencies=update_data.get(
                    "behavioral_competencies", job_vacancy.behavioral_competencies
                ),
                languages=update_data.get("languages", job_vacancy.languages),
                context="job_vacancy_update",
            )

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
            changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)
            await job_audit_service.log_update(
                job_id=str(job_vacancy_id),
                changes=changes,
                changed_by=changed_by,
                company_id=user_company,
                db=db,
            )

        await repo.flush_and_refresh(job_vacancy)

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
            enriched_jd=job_vacancy.enriched_jd,
            fairness_warnings=fairness_warnings or None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── DELETE (soft) ───────────────────────────────────────────────────────────

@router.delete("/job-vacancies/{job_vacancy_id}", response_model=JobVacancyDeleteResponse)
async def delete_job_vacancy(
    job_vacancy_id: UUID,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a job vacancy (soft delete - sets status to Arquivada)."""
    try:
        logger.info(f"Deleting job vacancy: {job_vacancy_id}")

        user_company = get_user_company_id(current_user)
        db = repo.get_session()

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_vacancy_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        job_vacancy.status = "Arquivada"
        job_vacancy.updated_at = datetime.utcnow()

        from app.domains.job_management.services.job_audit_service import job_audit_service
        changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)
        await job_audit_service.log_archive(
            job_id=str(job_vacancy_id),
            changed_by=changed_by,
            company_id=user_company,
            db=db,
        )

        logger.info(f"Job vacancy archived: {job_vacancy_id}")

        return {
            "success": True,
            "message": f"Vaga \{job_vacancy.title}\ arquivada com sucesso",
            "id": str(job_vacancy_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── PATCH status ─────────────────────────────────────────────────────────────

@router.patch("/job-vacancies/{job_vacancy_id}/status", response_model=JobVacancyStatusUpdateResponse)
async def update_job_vacancy_status(
    job_vacancy_id: UUID,
    status: str,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_active_user)
):
    """Update job vacancy status."""
    try:
        valid_statuses = ["Rascunho", "Ativa", "Pausada", "Concluída", "Arquivada"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Valid options: " + ", ".join(valid_statuses)
            )

        user_company = get_user_company_id(current_user)
        db = repo.get_session()

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_vacancy_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        old_status = job_vacancy.status
        job_vacancy.status = status
        job_vacancy.updated_at = datetime.utcnow()

        from app.domains.job_management.services.job_audit_service import job_audit_service
        changed_by = str(current_user.email) if hasattr(current_user, "email") else str(current_user.id)
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


@router.post("/job-vacancies/{job_id}/duplicate", response_model=DuplicateJobResponse)
async def duplicate_job(
    job_id: UUID,
    request: DuplicateJobRequest,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Duplicate a job vacancy with all its data."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    company_id = get_user_company_id(current_user)
    db = repo.get_session()

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
            created_by=current_user.email if hasattr(current_user, "email") else "demo@wedotalent.com",
            company_id=company_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to duplicate job"))

        logger.info(f"Created {result[total_jobs_created]} duplicate jobs from {job_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/job-vacancies/{job_id}/clone-from-template", response_model=CloneFromTemplateResponse)
async def clone_from_template(
    job_id: UUID,
    request: CloneFromTemplateRequest,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo)
):
    """Create a new job using an existing job as a template (no candidates)."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    company_id = get_user_company_id(current_user)
    db = repo.get_session()

    try:
        logger.info(f"Creating job from template {job_id}")

        result = await job_clone_service.clone_from_template(
            db=db,
            source_job_id=job_id,
            new_title=request.new_title,
            overrides=request.overrides,
            created_by=current_user.email if hasattr(current_user, "email") else "demo@wedotalent.com",
            company_id=company_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to create from template"))

        logger.info(f"Created job from template: {result[created_job][title]}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{job_id}/clone-summary", response_model=CloneSummaryResponse)
async def get_clone_summary(
    job_id: UUID,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo)
):
    """Get a summary of a job for displaying before cloning."""
    from app.domains.job_management.services.job_clone_service import job_clone_service

    db = repo.get_session()

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
