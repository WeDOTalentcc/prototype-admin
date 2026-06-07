import uuid as uuid_lib
from datetime import datetime
from typing import Any, Union, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from app.auth.models import UserRole
from app.middleware.trial_enforcement import require_active_subscription_or_demo  # noqa: F401
from app.shared.services.plan_limits_service import check_active_jobs_limit_or_demo  # noqa: F401
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

"""
CRUD routes: finalize, search, GET one, GET list, POST create, PUT update,
DELETE (archive), PATCH status, duplicate, clone, find-by-identifier.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ._shared import VALID_JOB_STATUSES
from ._shared import *
from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository
from app.domains.job_management.dependencies import get_job_vacancy_crud_repo
from app.domains.integrations_hub.services.rails_adapter import RailsAdapter, RAILS_ENABLED
from app.domains.integrations_hub.services.rails_adapter_dependency import get_rails_adapter
from app.shared.rails_migration.deprecation import enforce_job_vacancies_deprecation
from app.shared.rbac.mutation_gate import assert_mutation_allowed
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

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
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Finalize job vacancy creation from conversational flow."""
    try:
        company_id = get_user_company_id(current_user)
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Finalizing job vacancy: {request.job_vacancy_state.job_title} for company: {company_id}")

        if not request.job_vacancy_state.is_ready_for_publication():
            raise HTTPException(status_code=400, detail="Job vacancy is not ready for publication. Missing required fields.")

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
            message=f"Vaga \{job_title}\ criada com sucesso!"
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
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
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
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
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

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Retrieved {len(archetypes)} archetypes")

        return ArchetypesResponse(vacancies=archetypes, total=len(archetypes))

    except HTTPException:
        raise
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error fetching archetypes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Find by identifier ────────────────────────────────────────────────────

class FindJobRequest(WeDoBaseModel):
    identifier: str = Field(..., description="Job ID, job_id code, or title to search for")


@router.post("/job-vacancies/find-by-identifier", response_model=FindJobResponse)
async def find_job_by_identifier(
    request: FindJobRequest,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
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
    # Regex guard (Task #455 + #952): accept UUID OR bigint legacy id,
    # reject any other token (e.g. "lifecycle-overview", "stats") so that
    # if router-include order ever regresses, FastAPI returns 422 instead
    # of swallowing a static collection path into this item handler.
    job_vacancy_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
company_id: str = Depends(require_company_id)):
    """Get job vacancy by ID. Accepts UUID (local) or integer string (Rails bigint).
    When RAILS_API_URL is configured and the ID looks like a Rails bigint, queries Rails first.
    Falls back to local DB with company/visibility authorization when Rails is disabled or ID is a UUID.
    """
    try:
        # When Rails is enabled and the ID is a bigint (Rails-style), try Rails first.
        # UUID-style IDs are always served from local DB with full authorization checks.
        if RAILS_ENABLED and job_vacancy_id.isdigit():
            rails_job = await rails_adapter.get_job_from_rails_only(job_vacancy_id)
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

        await resolve_inherited_salary_ranges(repo.db, user_company, [job_vacancy])
        await resolve_inherited_benefits(repo.db, user_company, [job_vacancy])
        _role_defaults = await load_role_pii_defaults(repo.db, user_company)
        _vacancy_detail = {
            "id": str(job_vacancy.id),
            "title": job_vacancy.title,
            "department": job_vacancy.department,
            "location": job_vacancy.location,
            "work_model": job_vacancy.work_model,
            "seniority_level": job_vacancy.seniority_level,
            "status": job_vacancy.status,
            "is_confidential": job_vacancy.is_confidential,
            "salary_range": job_vacancy.salary_range,
            "responsibilities": job_vacancy.responsibilities or [],  # T-1166
            "requirements": job_vacancy.requirements or [],
            "technical_requirements": job_vacancy.technical_requirements,
            "languages": job_vacancy.languages,
            "behavioral_competencies": job_vacancy.behavioral_competencies,
            "interview_stages": job_vacancy.interview_stages,
            # P1-4 (audit 2026-06-05): preview lê esta coluna; wizard/grafo grava
            # em screening_config["screening_questions"]. Fallback p/ nao vir vazio.
            "screening_questions": job_vacancy.screening_questions or (job_vacancy.screening_config or {}).get("screening_questions") or [],
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
        return apply_vacancy_salary_visibility(_vacancy_detail, current_user, _role_defaults)

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
    source: str | None = None,  # Phase 4H — filter by 'wizard' | 'ats_import' | 'ats_external' | 'manual'
    skip: int = 0,
    limit: int = 500,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
company_id: str = Depends(require_company_id)):
    """List job vacancies. When RAILS_API_URL is configured, tries Rails first then local DB."""
    try:
        # Only query Rails when explicitly enabled — never let the adapter's own DB fallback
        # bypass company/visibility scoping and authorization done in the local path below.
        user_email = current_user.email.lower() if current_user.email else ""
        user_id = str(current_user.id) if current_user.id else ""
        is_admin = current_user.role == UserRole.admin if hasattr(current_user, "role") else False

        # Sprint 6 RBAC: compute visible scope (own dept + 1-level subordinate depts/emails)
        try:
            from app.shared.rbac.visible_scope import compute_visible_scope
            _scope = await compute_visible_scope(current_user)
            current_user._sprint6_subord_depts = set(_scope.subordinate_dept_ids)
            current_user._sprint6_subord_emails = set(_scope.subordinate_user_emails)
        except Exception:
            current_user._sprint6_subord_depts = set()
            current_user._sprint6_subord_emails = set()

        if RAILS_ENABLED:
            page = skip // limit + 1 if limit else 1
            rails_jobs = await rails_adapter.list_jobs_from_rails_only(
                page=page,
                limit=limit,
                status=status,
                visibility=visibility,
            )
            if rails_jobs is not None:
                # Apply the same confidentiality/visibility filtering used in the local DB path.
                # This is a defense-in-depth layer — Rails may enforce its own access control,
                # but we must be consistent with our own security model.
                filtered: list[dict] = []
                for jv in rails_jobs:
                                        # Phase 4H — source filter on Rails branch
                    if source and (jv.get('source') or 'wizard') != source:
                        continue
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
                        # Phase 4H — source filter (wizard|ats_import|ats_external|manual)
            if source and (jv.source if hasattr(jv, 'source') else 'wizard') != source:
                continue
            jv_visibility = jv.visibility or "public"

            # RBAC Sprint 2 + Sprint 6 (2026-05-25): department scope + manager hierarchy.
            # Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
            #
            # Sprint 6 adds 1-level manager hierarchy. Manager sees jobs of their direct subordinates.
            # NULL on either side (user.dept_id or jv.dept_id) = legacy soft-launch (no enforcement).
            user_dept_id = getattr(current_user, "department_id", None)
            jv_dept_id = getattr(jv, "department_id", None)

            # Build expanded dept set: own dept + direct subordinate depts
            subord_depts = getattr(current_user, "_sprint6_subord_depts", None)
            subord_emails = getattr(current_user, "_sprint6_subord_emails", None)
            visible_depts: set[str] = set()
            if user_dept_id:
                visible_depts.add(str(user_dept_id))
            if subord_depts:
                visible_depts.update(subord_depts)

            dept_scope_enforced = (
                not is_admin
                and user_dept_id is not None
                and jv_dept_id is not None
                and str(jv_dept_id) not in visible_depts
            )

            if jv_visibility in ["public", "internal"]:
                if not dept_scope_enforced:
                    job_vacancies.append(jv)
                    continue
                # Dept out of scope → libera se hiring_team match OU subordinate owner (Sprint 6)
                jv_created_by = (jv.created_by or "").lower()
                jv_recruiter_email = (jv.recruiter_email or "").lower()
                jv_access_list = [x.lower() for x in (jv.access_list or [])]
                if user_email in (jv_created_by, jv_recruiter_email) or user_email in jv_access_list:
                    job_vacancies.append(jv)
                    continue
                # Sprint 6: manager sees jobs owned by direct subordinates
                if subord_emails and (jv_created_by in subord_emails or jv_recruiter_email in subord_emails):
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

        # P1-2: métricas reais por vaga (Candidatos / Funil / Performance LIA) —
        # batch aggregate de vacancy_candidates + wsi_sessions + interviews
        # (UMA query GROUP BY por fonte, sem N+1). Substitui o antigo
        # generate_lia_metrics() que fabricava números com random.uniform.
        _metrics_by_vaga = await repo.aggregate_list_metrics(
            [str(jv.id) for jv in job_vacancies], company_id
        )
        _empty_metrics = {
            "candidates_count": 0,
            "funnel_data": {
                "total": 0, "screening": 0, "interview": 0, "final": 0, "hired": 0,
            },
            "lia_metrics": {
                "pipeline_lia": 0, "triagens_agendadas": 0, "triagens_realizadas": 0,
                "sem_resposta": 0, "entrevistas_agendadas": 0,
            },
        }

        await resolve_inherited_salary_ranges(repo.db, company_id, job_vacancies)
        _list_role_defaults = await load_role_pii_defaults(repo.db, company_id)
        return {
            "total": len(job_vacancies),
            "skip": skip,
            "limit": limit,
            "items": [
                apply_vacancy_salary_visibility({
                    "id": str(jv.id),
                    "title": jv.title,
                    "department": jv.department,
                    "location": jv.location,
                    "work_model": jv.work_model,
                    "employment_type": jv.employment_type,
                    "seniority_level": jv.seniority_level,
                    "description": jv.description,
                    "responsibilities": jv.responsibilities or [],  # T-1166
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
                    # Phase 4H — source + wizard_stage
                    "source": jv.source if hasattr(jv, "source") else "wizard",
                    "wizard_stage": jv.wizard_stage if hasattr(jv, "wizard_stage") else None,
                    "priority": jv.priority or "média",
                    "created_at": jv.created_at.isoformat() if hasattr(jv.created_at, "isoformat") else None,
                    "updated_at": jv.updated_at.isoformat() if hasattr(jv.updated_at, "isoformat") else None,
                    "deadline": jv.deadline.isoformat() if hasattr(jv, "deadline") and jv.deadline else None,
                    "candidates_count": _metrics_by_vaga.get(str(jv.id), _empty_metrics)["candidates_count"],
                    "funnel_data": _metrics_by_vaga.get(str(jv.id), _empty_metrics)["funnel_data"],
                    "lia_metrics": _metrics_by_vaga.get(str(jv.id), _empty_metrics)["lia_metrics"],
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
                    "screening_questions": jv.screening_questions or (jv.screening_config or {}).get("screening_questions") or [],  # P1-4: fallback forma wizard
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
                }, current_user, _list_role_defaults)
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
company_id: str = Depends(require_company_id)):
    """Create a new job vacancy directly (not via conversation)."""
    try:
        company_id = get_user_company_id(current_user)
        logger.info(f"Creating job vacancy: {job_data.title} for company: {company_id}")

        # Sprint 4 Refactor (audit 2026-05-20): elimina drop silencioso de fields.
        # job_data.model_dump() retorna TODOS os fields do schema automaticamente —
        # quando schema cresce, novos fields fluem sem precisar editar este bloco.
        # Sensor harness: tests/contract/test_jobvacancy_roundtrip.py garante regressao.
        job_data_dict = job_data.model_dump(exclude={"conversation_id"})

        # Preservar semantica original (None -> []) para list fields com default=list
        # T-1166 — responsibilities especialmente: model coerce None nao acontece automatico.
        _LIST_FIELDS_DEFAULT_EMPTY = (
            "responsibilities", "requirements", "technical_requirements",
            "languages", "behavioral_competencies", "benefits",
            "access_list", "screening_questions", "interview_stages",
            "eligibility_questions", "disabled_eligibility_question_ids",
            "affirmative_document_types",
        )
        for _field in _LIST_FIELDS_DEFAULT_EMPTY:
            if job_data_dict.get(_field) is None:
                job_data_dict[_field] = []

        # conversation_id requer UUID conversion (nao puro dump)
        conversation_id = uuid_lib.UUID(job_data.conversation_id) if job_data.conversation_id else None

        job_vacancy = JobVacancy(
            id=uuid_lib.uuid4(),
            **job_data_dict,
            conversation_id=conversation_id,
            company_id=company_id,
            created_by=str(current_user.id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
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
            responsibilities=job_vacancy.responsibilities or [],  # T-1166
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
            # Sprint 3 Boy Scout (audit 2026-05-20): 11 fields que dropavam no constructor
            # também filtravam aqui. Bug simétrico: INSERT salvava, response não devolvia.
            bonus_range=job_vacancy.bonus_range,
            eligibility_questions=job_vacancy.eligibility_questions or [],
            confidentiality_config=job_vacancy.confidentiality_config,
            is_affirmative=job_vacancy.is_affirmative or False,
            affirmative_criteria_primary=job_vacancy.affirmative_criteria_primary,
            affirmative_criteria_secondary=job_vacancy.affirmative_criteria_secondary,
            affirmative_description=job_vacancy.affirmative_description,
            affirmative_document_required=job_vacancy.affirmative_document_required or False,
            affirmative_document_types=job_vacancy.affirmative_document_types or [],
            source=job_vacancy.source,
            wizard_stage=job_vacancy.wizard_stage,
            # Sprint 4 symmetric fix (audit 2026-05-22): INSERT flowed these
            # 4 fields via model_dump() but response builder still omitted them,
            # causing test_jobvacancy_post_preserves_all_schema_fields to detect
            # silent drop. Confidentiality/access-list features were broken in
            # the POST round-trip until this fix.
            visibility=job_vacancy.visibility or "public",
            access_list=job_vacancy.access_list or [],
            masked_company_name=job_vacancy.masked_company_name,
            exclude_from_sync=job_vacancy.exclude_from_sync or False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job vacancy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── PUT update ───────────────────────────────────────────────────────────────

@router.put("/job-vacancies/{job_vacancy_id}", response_model=JobVacancyResponse)
async def update_job_vacancy(
    job_vacancy_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    job_data: JobVacancyUpdate = ...,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
    """Update an existing job vacancy."""
    try:
        logger.info(f"Updating job vacancy: {job_vacancy_id}")

        user_company = get_user_company_id(current_user)
        db = repo.get_session()

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_vacancy_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        await assert_mutation_allowed(job_vacancy, current_user, resource_label="vaga")

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

        # Onda 2D (audit 2026-06-06): prazos derivados do SLA do pipeline ao salvar as etapas.
        if "interview_stages" in update_data:
            from app.domains.cv_screening.services.deadline_calculator_service import (
                derive_deadlines_from_stages,
            )
            for _df, _dv in derive_deadlines_from_stages(update_data["interview_stages"]).items():
                if hasattr(job_vacancy, _df):
                    setattr(job_vacancy, _df, _dv)

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
            responsibilities=job_vacancy.responsibilities or [],  # T-1166
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

@router.delete("/job-vacancies/{job_vacancy_id}", response_model=JobVacancyDeleteResponse)
async def delete_job_vacancy(
    job_vacancy_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
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
    job_vacancy_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    status: str = ...,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Update job vacancy status."""
    try:
        # Phase C.1 — consolidate with _shared.VALID_JOB_STATUSES (was drift).
        # The bulk endpoint in lifecycle.py:942 already used the shared constant;
        # this single-vacancy PATCH was rejecting "Cancelada" which IS valid
        # there. Pinned by tests/api/test_job_vacancy_status_cancelada.py.
        if status not in VALID_JOB_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Valid options: " + ", ".join(VALID_JOB_STATUSES),
            )

        user_company = get_user_company_id(current_user)
        db = repo.get_session()

        job_vacancy = await repo.get_vacancy_by_id_and_company(job_vacancy_id, user_company)

        if not job_vacancy:
            raise HTTPException(status_code=404, detail="Job vacancy not found")
        # Sprint 7.2 RBAC: mutation gate
        await assert_mutation_allowed(job_vacancy, current_user, resource_label="vaga")

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

class DuplicateJobRequest(WeDoBaseModel):
    copies: int = Field(default=1, ge=1, le=10)
    include_candidates: bool = Field(default=True)
    candidate_filter: str | None = Field(default=None)
    candidate_status_override: str | None = Field(default=None)
    overrides: dict[str, Any] | None = Field(default=None)


class CloneFromTemplateRequest(WeDoBaseModel):
    new_title: str | None = Field(default=None)
    overrides: dict[str, Any] | None = Field(default=None)


@router.post("/job-vacancies/{job_id}/duplicate", response_model=DuplicateJobResponse)
async def duplicate_job(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    request: DuplicateJobRequest = ...,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
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
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    request: CloneFromTemplateRequest = ...,
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)):
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
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    repo: JobVacancyCRUDRepository = Depends(get_job_vacancy_crud_repo), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
