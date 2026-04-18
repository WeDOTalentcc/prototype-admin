"""
CRUD endpoints for candidates: list, get, create, update, stage-update, delete, enrich.
"""
import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Request

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

from ._shared import (
    ActivityService,
    AuditService,
    Candidate,
    CandidateCreate,
    CandidateRepository,
    CandidateStageUpdate,
    CandidateUpdate,
    CalibrationService,
    VacancyCandidateRepository,
    check_rejection_reason,
    determine_feedback_action,
    extract_company_info_from_work_history,
    get_activity_service,
    get_audit_service,
    get_candidate_repo,
    get_current_user_or_demo,
    get_stage_rank,
    get_vacancy_candidate_repo,
    logger,
    normalize_array_field,
    User,
)
from pydantic import BaseModel
from app.domains.integrations_hub.services.rails_adapter import RailsAdapter, RAILS_ENABLED
from app.domains.integrations_hub.services.rails_adapter_dependency import get_rails_adapter
from app.shared.rails_migration.deprecation import enforce_candidates_deprecation
from app.shared.robustness.idempotency import reject_duplicate_async

# MIGRATION_PLAN item 7.2 — Python CRUD deprecated in favor of Rails (ats-api-copia).
#
# The 7 endpoints below are kept as a compatibility shim during the transition.
# Every request gets logged with a deprecation warning and a `Sunset` header
# pointing at the retirement date. Flip `STRICT_RAILS_ONLY=true` in the
# environment to turn all routes below into HTTP 410 Gone with a pointer at
# the Rails endpoint. This lets us kill-switch the old API without a deploy.
router = APIRouter(
    dependencies=[Depends(enforce_candidates_deprecation)],
)


# ---------------------------------------------------------------------------
# Response helper: serialize a candidate ORM object to dict
# ---------------------------------------------------------------------------
def _serialize_candidate_light(c) -> dict:
    """
    Serialização enxuta para a LISTAGEM (GET /candidates).

    Remove colunas JSON/TEXT pesadas que o UI da listagem não consome —
    elas permanecem disponíveis via GET /candidates/{id} (serializer `full`).
    Motivação: reduzir payload de ~2.3KB/candidato para ~800B/candidato e
    evitar CPU de parsing de JSONs grandes (pearch_insights, lia_insights,
    additional_data, work_history, etc.) no hot path do list.
    Veja também `CandidateRepository.list_candidates(slim=True)` que evita
    trazer essas colunas do Postgres logo na query (defer).
    """
    return {
        # Identificação + contato básico exibido nos cards/rows
        "id": str(c.id),
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "mobile_phone": c.mobile_phone,
        "linkedin_url": c.linkedin_url,
        "avatar_url": c.avatar_url,
        # Perfil profissional resumido
        "current_title": c.current_title,
        "current_company": c.current_company,
        "seniority_level": c.seniority_level,
        "years_of_experience": c.years_of_experience,
        "headline": c.headline,
        "technical_skills": c.technical_skills or [],
        "location_city": c.location_city,
        "location_state": c.location_state,
        "location_country": c.location_country,
        # Flags usadas para badges/filtros no card
        "is_remote": c.is_remote,
        "is_open_to_work": c.is_open_to_work,
        "is_decision_maker": c.is_decision_maker,
        "is_top_universities": c.is_top_universities,
        "is_hiring": c.is_hiring,
        # Métricas exibidas no card
        "lia_score": c.lia_score,
        "skills_match_percentage": c.skills_match_percentage,
        # Fonte + workflow
        "source": c.source,
        "status": c.status,
        "is_active": c.is_active,
        "is_blacklisted": c.is_blacklisted,
        "tags": c.tags or [],
        # Timestamps
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "last_activity_at": c.last_activity_at.isoformat() if c.last_activity_at else None,
    }


def _serialize_candidate(c, *, full: bool = False) -> dict:
    """Return a dict representation of a Candidate ORM object."""
    base = {
        "id": str(c.id),
        "name": c.name,
        "email": c.email,
        "secondary_email": c.secondary_email,
        "phone": c.phone,
        "mobile_phone": c.mobile_phone,
        "secondary_phone": c.secondary_phone,
        "linkedin_url": c.linkedin_url,
        "github_url": c.github_url,
        "portfolio_url": c.portfolio_url,
        "avatar_url": c.avatar_url,
        "date_of_birth": str(c.date_of_birth) if c.date_of_birth else None,
        "gender": c.gender,
        "nationality": c.nationality,
        "marital_status": c.marital_status,
        "cpf": c.cpf,
        "current_title": c.current_title,
        "current_company": c.current_company,
        "seniority_level": c.seniority_level,
        "years_of_experience": c.years_of_experience,
        "self_introduction": c.self_introduction,
        "technical_skills": c.technical_skills or [],
        "soft_skills": c.soft_skills or [],
        "languages": c.languages or {},
        "certifications": c.certifications or [],
        "interests": c.interests or [],
        "location_city": c.location_city,
        "location_state": c.location_state,
        "location_country": c.location_country,
        "address_street": c.address_street,
        "address_number": c.address_number,
        "address_district": c.address_district,
        "address_zip": c.address_zip,
        "address_complement": c.address_complement,
        "is_remote": c.is_remote,
        "willing_to_relocate": c.willing_to_relocate,
        "mobility": c.mobility,
        "work_model_preference": c.work_model_preference,
        "contract_type_preference": c.contract_type_preference,
        "current_salary": c.current_salary,
        "desired_salary_min": c.desired_salary_min,
        "desired_salary_max": c.desired_salary_max,
        "salary_currency": c.salary_currency,
        "salary_expectation_clt": c.salary_expectation_clt,
        "salary_expectation_pj": c.salary_expectation_pj,
        "salary_expectation_freelance": c.salary_expectation_freelance,
        "resume_url": c.resume_url,
        "source": c.source,
        "ats_source_name": c.ats_source_name,
        "ats_candidate_id": c.ats_candidate_id,
        "pearch_profile_id": c.pearch_profile_id,
        "is_open_to_work": c.is_open_to_work,
        "is_decision_maker": c.is_decision_maker,
        "is_top_universities": c.is_top_universities,
        "is_hiring": c.is_hiring,
        "headline": c.headline,
        "expertise": normalize_array_field(c.expertise),
        "linkedin_followers_count": c.linkedin_followers_count,
        "linkedin_connections_count": c.linkedin_connections_count,
        "pearch_insights": c.pearch_insights or {},
        "outreach_message": c.outreach_message,
        "best_personal_email": c.best_personal_email,
        "best_business_email": c.best_business_email,
        "personal_emails": c.personal_emails or [],
        "business_emails": c.business_emails or [],
        "phone_types": c.phone_types or {},
        "estimated_age": c.estimated_age,
        "middle_name": c.middle_name,
        "company_followers_count": c.company_followers_count,
        "company_keywords": c.company_keywords or [],
        "lia_score": c.lia_score,
        "lia_insights": c.lia_insights or {},
        "skills_match_percentage": c.skills_match_percentage,
        "status": c.status,
        "is_active": c.is_active,
        "is_blacklisted": c.is_blacklisted,
        "blacklist_reason": c.blacklist_reason,
        "preferred_contact_method": c.preferred_contact_method,
        "best_time_to_contact": c.best_time_to_contact,
        "communication_consent": c.communication_consent,
        "completed_register": c.completed_register,
        "accept_terms": c.accept_terms,
        "work_history": c.work_history or [],
        **extract_company_info_from_work_history(c.work_history or []),
        "tags": c.tags or [],
        "notes": c.notes,
        "additional_data": c.additional_data or {},
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "last_contacted_at": c.last_contacted_at.isoformat() if c.last_contacted_at else None,
        "last_activity_at": c.last_activity_at.isoformat() if c.last_activity_at else None,
    }
    if full:
        base["resume_text"] = c.resume_text
        base["cover_letter"] = c.cover_letter
    return base


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=None)
async def list_candidates(
    search: str | None = None,
    status: str | None = None,
    source: str | None = None,
    seniority: str | None = None,
    ids: str | None = None,
    offset: int = Query(default=0, ge=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
    sort_by: str | None = None,
    sort_order: str | None = None,
    full: bool = Query(
        default=False,
        description=(
            "Quando true retorna o payload completo de cada candidato (inclui JSONs "
            "pesados: work_history, pearch_insights, lia_insights, additional_data, "
            "resume_text etc). Por padrão (false) é retornado payload enxuto ~3x menor "
            "adequado para o hot path da listagem."
        ),
    ),
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
    current_user: User = Depends(get_current_user_or_demo),
):
    """List candidates. When RAILS_API_URL is configured, tries Rails first then falls back to local DB.

    Security contract (tasks #290 + #295):
      1. Endpoint depends on `get_current_user_or_demo`, which raises 401
         outside DEV_MODE when no valid token is presented. The upstream
         `AuthEnforcementMiddleware` provides a second line of defence.
      2. The authenticated user's `company_id` is propagated to BOTH
         `count_candidates` and `list_candidates`; the repo layer applies
         `Candidate.company_id == cid` so a recruiter in tenant A can never
         see rows belonging to tenant B.
      3. Any exception raised below the repo boundary is logged with full
         context and re-raised as a sanitized HTTP 500 — the global
         StarletteHTTPException handler in `app.main` further rewrites the
         body to `{"message": "Internal server error", ...}` so DB driver
         strings, DSNs and tracebacks never reach the client.
      Regression coverage: tests/integration/test_candidates_tenant_isolation.py
    """
    _company_id = str(current_user.company_id) if current_user.company_id else None
    _request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    # Only call Rails when explicitly enabled — avoids adapter's own DB fallback
    # bypassing endpoint-level filters and authorization.
    if RAILS_ENABLED:
        try:
            page = (offset or skip) // limit + 1 if limit else 1
            rails_items = await rails_adapter.list_candidates_from_rails_only(
                search=search or "*",
                page=page,
                limit=limit,
                status=status,
                source=source,
                seniority=seniority,
            )
            if rails_items is not None:
                logger.debug("[list_candidates] Returning %d candidates from Rails", len(rails_items))
                return {
                    "total": len(rails_items),
                    "skip": offset or skip,
                    "limit": limit,
                    "source": "rails",
                    "items": rails_items,
                }
        except Exception as e:
            logger.warning("[list_candidates] Rails unavailable, falling back to local DB: %s", e)

    try:
        id_list: list[str] | None = None
        if ids:
            import re
            uuid_pattern = re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                re.IGNORECASE,
            )
            id_list = [
                i.strip() for i in ids.split(",")
                if i.strip() and uuid_pattern.match(i.strip())
            ]
            if not id_list:
                id_list = None

        effective_skip = offset if offset > 0 else skip

        # Instrumentação de perf (task #276): mede cada etapa separadamente para
        # detectar regressões futuras (count lento, list lento ou serialização
        # pesada). p95 alvo: <1s com limit=20. Logs estruturados para grep.
        import time as _time
        _t_total = _time.perf_counter()
        _t0 = _time.perf_counter()
        total = await candidate_repo.count_candidates(
            search=search, status=status, source=source, seniority=seniority, ids=id_list,
            company_id=_company_id,
        )
        _t_count_ms = (_time.perf_counter() - _t0) * 1000.0

        _t0 = _time.perf_counter()
        candidates = await candidate_repo.list_candidates(
            search=search, status=status, source=source, seniority=seniority, ids=id_list,
            skip=effective_skip, limit=limit, sort_by=sort_by, sort_order=sort_order,
            slim=not full, company_id=_company_id,
        )
        _t_list_ms = (_time.perf_counter() - _t0) * 1000.0

        _t0 = _time.perf_counter()
        if full:
            items = [_serialize_candidate(c, full=True) for c in candidates]
        else:
            items = [_serialize_candidate_light(c) for c in candidates]
        _t_ser_ms = (_time.perf_counter() - _t0) * 1000.0
        _t_total_ms = (_time.perf_counter() - _t_total) * 1000.0

        logger.info(
            "[list_candidates] total=%d returned=%d limit=%d full=%s "
            "count=%.1fms list=%.1fms serialize=%.1fms endpoint=%.1fms",
            total, len(items), limit, full,
            _t_count_ms, _t_list_ms, _t_ser_ms, _t_total_ms,
        )

        return {
            "total": total,
            "skip": effective_skip,
            "limit": limit,
            "source": "local",
            "items": items,
        }
    except Exception:
        logger.exception(
            "[list_candidates] failed request_id=%s user_id=%s company_id=%s search=%r status=%r",
            _request_id, getattr(current_user, "id", None), _company_id, search, status,
        )
        raise HTTPException(status_code=500, detail="Falha ao listar candidatos.")


def _assert_tenant_scope(candidate, current_user: User) -> None:
    """Enforce tenant scope on a candidate row (task #295).

    No-op enquanto `Candidate.company_id` não existir (ver auditoria #287
    causa raiz #4 e follow-up de migração). Quando a coluna landar, qualquer
    acesso cross-tenant por id vira 404 (em vez de 403, para não vazar
    existência da row para outros tenants).
    """
    row_company = getattr(candidate, "company_id", None)
    if row_company is None:
        return
    user_company = str(current_user.company_id) if current_user.company_id else None
    if user_company and str(row_company) != user_company:
        raise HTTPException(status_code=404, detail="Candidate not found")


@router.get("/{candidate_id}", response_model=None)
async def get_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Get a candidate by ID. When RAILS_API_URL is configured, tries Rails first then falls back to local DB."""
    # Only call Rails when explicitly enabled — avoids adapter's own DB fallback
    # returning unscoped/unfiltered data.
    if RAILS_ENABLED:
        try:
            rails_result = await rails_adapter.get_candidate_from_rails_only(candidate_id)
            if rails_result:
                logger.debug("[get_candidate] Returning candidate %s from Rails", candidate_id)
                return rails_result
        except Exception as e:
            logger.warning("[get_candidate] Rails unavailable for %s, falling back to local DB: %s", candidate_id, e)

    try:
        try:
            uuid.UUID(candidate_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Candidate not found")
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)
        return _serialize_candidate(candidate, full=True)
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[get_candidate] failed request_id=%s candidate_id=%s user_id=%s",
            _rid, candidate_id, getattr(current_user, "id", None),
        )
        raise HTTPException(status_code=500, detail="Falha ao carregar o candidato.")


async def _background_enrich_candidate(candidate_id: uuid.UUID, linkedin_url: str):
    """Background task to enrich candidate from LinkedIn."""
    from app.core.database import AsyncSessionLocal
    from app.domains.candidates.services.candidate_enrichment_service import candidate_enrichment_service
    try:
        async with AsyncSessionLocal() as db:
            result = await candidate_enrichment_service.enrich_candidate(
                db=db, candidate_id=candidate_id, linkedin_url=linkedin_url,
                include_experiences=True, include_education=True,
                include_email_discovery=True,
            )
            if result.get("success"):
                logger.info(
                    f"Background enrichment completed for candidate {candidate_id}: "
                    f"{len(result.get('fields_updated', []))} fields updated"
                )
            else:
                logger.warning(
                    f"Background enrichment failed for candidate {candidate_id}: {result.get('error')}"
                )
    except Exception as e:
        logger.error(f"Background enrichment error for candidate {candidate_id}: {e}")


@router.post("", response_model=None)
async def create_candidate(
    candidate_data: CandidateCreate,
    background_tasks: BackgroundTasks,
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
):
    """Create a new candidate. If auto_enrich=True and linkedin_url is provided, enrichment runs in background."""
    try:
        logger.info(f"Creating candidate: {candidate_data.name}")
        # Task #346 — toda criação propaga o tenant do usuário autenticado.
        # Em DEV/demo, `current_user.company_id` cai no UUID demo canônico
        # (ver app.core.tenant.DEMO_COMPANY_UUID).
        company_id = str(current_user.company_id) if current_user.company_id else None
        if not company_id:
            raise HTTPException(status_code=400, detail="company_id obrigatório.")
        # Task #478 / ADR 003 — drop double-submit retries before they hit
        # the DB. `generate_idempotency_key_async` collapses dual-ID retries
        # via `RailsAdapter`; here the params are email-keyed but we still
        # route through the async variant for consistency.
        await reject_duplicate_async(
            "create_candidate",
            {"email": (candidate_data.email or "").lower(), "company_id": company_id},
            rails_adapter,
            scope=f"company:{company_id}",
        )
        candidate = Candidate(
            id=uuid.uuid4(),
            company_id=company_id,
            name=candidate_data.name,
            email=candidate_data.email,
            phone=candidate_data.phone,
            linkedin_url=candidate_data.linkedin_url,
            github_url=candidate_data.github_url,
            portfolio_url=candidate_data.portfolio_url,
            current_title=candidate_data.current_title,
            current_company=candidate_data.current_company,
            seniority_level=candidate_data.seniority_level,
            years_of_experience=candidate_data.years_of_experience,
            technical_skills=candidate_data.technical_skills or [],
            soft_skills=candidate_data.soft_skills or [],
            languages=candidate_data.languages or {},
            certifications=candidate_data.certifications or [],
            location_city=candidate_data.location_city,
            location_state=candidate_data.location_state,
            location_country=candidate_data.location_country,
            is_remote=candidate_data.is_remote,
            willing_to_relocate=candidate_data.willing_to_relocate,
            desired_salary_min=candidate_data.desired_salary_min,
            desired_salary_max=candidate_data.desired_salary_max,
            salary_currency=candidate_data.salary_currency or "BRL",
            work_model_preference=candidate_data.work_model_preference,
            contract_type_preference=candidate_data.contract_type_preference,
            source=candidate_data.source or "manual",
            notes=candidate_data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        candidate = await candidate_repo.create(candidate)
        logger.info(f"Candidate created: {candidate.id}")

        enrichment_scheduled = False
        if candidate_data.auto_enrich and candidate_data.linkedin_url:
            background_tasks.add_task(
                _background_enrich_candidate, candidate.id, candidate_data.linkedin_url
            )
            enrichment_scheduled = True
            logger.info(f"Background enrichment scheduled for candidate {candidate.id}")

        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "seniority_level": candidate.seniority_level,
            "location_city": candidate.location_city,
            "source": candidate.source,
            "status": candidate.status,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "message": "Candidate created successfully",
            "enrichment_scheduled": enrichment_scheduled,
        }
    except HTTPException:
        # Preserva semântica 4xx (ex.: tenant ausente vira 400, não 500).
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[create_candidate] failed request_id=%s user_id=%s name=%s",
            _rid, getattr(current_user, "id", None), candidate_data.name,
        )
        raise HTTPException(status_code=500, detail="Falha ao criar o candidato.")


@router.put("/{candidate_id}", response_model=None)
async def update_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_data: CandidateUpdate,
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
):
    """Update an existing candidate."""
    try:
        # Task #478 / ADR 003 — collapse retries that switch between fork
        # UUID and Rails bigint onto the same idempotency key so the update
        # only runs once.
        company_scope = str(getattr(current_user, "company_id", "") or "global")
        update_payload = candidate_data.model_dump(exclude_unset=True)
        await reject_duplicate_async(
            "update_candidate",
            {"candidate_id": candidate_id, "payload": update_payload},
            rails_adapter,
            scope=f"company:{company_scope}",
        )
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)
        update_data = update_payload
        for field, value in update_data.items():
            if hasattr(candidate, field):
                setattr(candidate, field, value)
        candidate.updated_at = datetime.utcnow()
        candidate = await candidate_repo.update(candidate)
        logger.info(f"Candidate updated: {candidate_id}")
        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "status": candidate.status,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "message": "Candidate updated successfully",
        }
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[update_candidate] failed request_id=%s candidate_id=%s user_id=%s",
            _rid, candidate_id, getattr(current_user, "id", None),
        )
        raise HTTPException(status_code=500, detail="Falha ao atualizar o candidato.")


@router.patch("/{candidate_id}/stage", response_model=None)
async def update_candidate_stage(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    stage_data: CandidateStageUpdate,
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    vc_repo: VacancyCandidateRepository = Depends(get_vacancy_candidate_repo),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
):
    """Update candidate pipeline stage (used when moving candidates in Kanban)."""
    try:
        # Task #478 / ADR 003 — same-stage transitions retried with both ID
        # formats must collapse so we don't double-write the Kanban move.
        company_scope = str(getattr(current_user, "company_id", "") or "global")
        await reject_duplicate_async(
            "update_candidate_stage",
            {
                "candidate_id": candidate_id,
                "job_vacancy_id": str(stage_data.job_vacancy_id) if stage_data.job_vacancy_id else None,
                "stage": stage_data.stage,
                "sub_status": stage_data.sub_status,
                "user_id": stage_data.user_id,
            },
            rails_adapter,
            scope=f"company:{company_scope}",
        )
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)

        vacancy_candidate = await vc_repo.get_for_candidate_and_job(
            candidate_id=candidate_id,
            job_vacancy_id=str(stage_data.job_vacancy_id) if stage_data.job_vacancy_id else None,
        )

        if not vacancy_candidate:
            if get_stage_rank(stage_data.stage) == -1 and not stage_data.user_id:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "human_review_required",
                        "message": (
                            "Rejeição de candidato requer identificação do revisor humano (user_id). "
                            "Rejeições automatizadas sem revisão humana não são permitidas."
                        ),
                        "compliance": ["LGPD art. 20", "EU AI Act art. 14"],
                    },
                )
            previous_stage = candidate.status or "unknown"
            candidate.status = stage_data.stage
            candidate.updated_at = datetime.utcnow()
            candidate = await candidate_repo.update(candidate)
            logger.info(f"Candidate {candidate_id} status updated (no vacancy): {previous_stage} -> {stage_data.stage}")
            return {
                "id": str(candidate.id),
                "name": candidate.name,
                "stage": stage_data.stage,
                "previous_stage": previous_stage,
                "sub_status": stage_data.sub_status,
                "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
                "message": "Candidate status updated successfully (no vacancy association)",
            }

        is_rejection = get_stage_rank(stage_data.stage) == -1
        if is_rejection and not stage_data.user_id:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "human_review_required",
                    "message": (
                        "Rejeição de candidato requer identificação do revisor humano (user_id). "
                        "Rejeições automatizadas sem revisão humana não são permitidas."
                    ),
                    "compliance": ["LGPD art. 20", "EU AI Act art. 14"],
                },
            )

        if is_rejection and stage_data.sub_status:
            fg_rejection = check_rejection_reason(
                reason=stage_data.sub_status,
                candidate_name=candidate.name or "",
                company_id=str(vacancy_candidate.company_id) if hasattr(vacancy_candidate, "company_id") else "",
            )
            if fg_rejection.is_blocked:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "fairness_blocked",
                        "message": fg_rejection.blocked_result.educational_message if fg_rejection.blocked_result else "Viés detectado no motivo da rejeição.",
                        "category": fg_rejection.blocked_result.category if fg_rejection.blocked_result else None,
                        "compliance": ["Lei 9.029/95", "CLT Art. 373-A"],
                    },
                )

        previous_stage = vacancy_candidate.stage or "unknown"
        lia_score_at_transition = vacancy_candidate.lia_score
        vacancy_candidate.stage = stage_data.stage
        if is_rejection:
            vacancy_candidate.rejected_by_human = True
            vacancy_candidate.human_reviewer_id = stage_data.user_id
        if stage_data.sub_status:
            vacancy_candidate.status = stage_data.sub_status
        vacancy_candidate.updated_at = datetime.utcnow()
        vacancy_candidate = await vc_repo.update(vacancy_candidate)
        logger.info(
            f"Candidate {candidate_id} stage updated for vacancy {vacancy_candidate.vacancy_id}: "
            f"{previous_stage} -> {stage_data.stage}"
        )

        feedback_action = determine_feedback_action(previous_stage, stage_data.stage)
        if feedback_action != "neutral":
            try:
                calibration_service = CalibrationService(candidate_repo.db)
                await calibration_service.record_implicit_feedback(
                    candidate_id=candidate_id,
                    job_id=str(vacancy_candidate.vacancy_id),
                    user_id=stage_data.user_id or "system",
                    action=feedback_action,
                    stage_from=previous_stage,
                    stage_to=stage_data.stage,
                    lia_score=lia_score_at_transition,
                    lia_ranking=None,
                    context={
                        "sub_status": stage_data.sub_status,
                        "candidate_name": candidate.name,
                        "transition_type": "kanban_move",
                    },
                )
                logger.info(
                    f"Implicit feedback recorded: {feedback_action} for candidate {candidate_id} "
                    f"(LIA score: {lia_score_at_transition})"
                )
                if lia_score_at_transition is not None:
                    from uuid import uuid4
                    from app.domains.cv_screening.services.rubric_evaluation_service import calibration_feedback
                    if feedback_action == "advance":
                        adjusted_score = min(99.0, lia_score_at_transition + 10.0)
                        recruiter_decision = "approved"
                    else:
                        adjusted_score = max(0.0, lia_score_at_transition - 15.0)
                        recruiter_decision = "rejected"
                    calibration_feedback.record_feedback(
                        evaluation_id=str(uuid4()),
                        candidate_id=candidate_id,
                        job_id=str(vacancy_candidate.vacancy_id),
                        original_score=lia_score_at_transition,
                        recruiter_adjusted_score=adjusted_score,
                        recruiter_decision=recruiter_decision,
                    )
                    logger.info(
                        f"Scoring calibration updated for job {vacancy_candidate.vacancy_id}: "
                        f"{recruiter_decision} (score {lia_score_at_transition:.1f} -> {adjusted_score:.1f})"
                    )
                try:
                    import asyncio as _asyncio
                    from app.shared.services.ml_feedback_service import ml_feedback_service as _ml_fb
                    _decision_map = {"advance": "hire", "reject": "reject"}
                    _ml_decision = _decision_map.get(feedback_action)
                    if _ml_decision:
                        _company_id = str(getattr(vacancy_candidate, "company_id", "") or "")
                        _job_id = str(vacancy_candidate.vacancy_id)
                        _asyncio.create_task(
                            _ml_fb.record_decision(
                                db=candidate_repo.db,
                                company_id=_company_id,
                                job_id=_job_id,
                                candidate_id=candidate_id,
                                lia_score=float(lia_score_at_transition or 0),
                                decision=_ml_decision,
                            )
                        )
                except Exception as _ml_err:
                    logger.debug("[D6-G2] ml_feedback record_decision skipped: %s", _ml_err)
            except Exception as calibration_error:
                logger.warning(f"Failed to record implicit feedback: {calibration_error}")

        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "stage": vacancy_candidate.stage,
            "previous_stage": previous_stage,
            "sub_status": vacancy_candidate.status,
            "vacancy_id": vacancy_candidate.vacancy_id,
            "updated_at": vacancy_candidate.updated_at.isoformat() if vacancy_candidate.updated_at else None,
            "message": "Candidate stage updated successfully",
            "feedback_recorded": feedback_action if feedback_action != "neutral" else None,
        }
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[update_candidate_stage] failed request_id=%s candidate_id=%s user_id=%s stage=%s",
            _rid, candidate_id, getattr(current_user, "id", None),
            getattr(stage_data, "stage", None),
        )
        raise HTTPException(status_code=500, detail="Falha ao atualizar a etapa do candidato.")


@router.delete("/{candidate_id}", response_model=None)
async def delete_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
    rails_adapter: RailsAdapter = Depends(get_rails_adapter),
):
    """Soft delete (deactivate) a candidate."""
    try:
        company_scope = str(getattr(current_user, "company_id", "") or "global")
        await reject_duplicate_async(
            "delete_candidate",
            {"candidate_id": candidate_id},
            rails_adapter,
            scope=f"company:{company_scope}",
        )
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)
        await candidate_repo.soft_delete(candidate)
        logger.info(f"Candidate deactivated: {candidate_id}")
        return {"message": "Candidate deactivated successfully", "id": candidate_id}
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[delete_candidate] failed request_id=%s candidate_id=%s user_id=%s",
            _rid, candidate_id, getattr(current_user, "id", None),
        )
        raise HTTPException(status_code=500, detail="Falha ao remover o candidato.")


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------

class EnrichmentRequest(BaseModel):
    linkedin_url: str | None = None
    include_experiences: bool = True
    include_education: bool = True
    include_email_discovery: bool = True


@router.post("/{candidate_id}/enrich", response_model=None)
async def enrich_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    enrichment_request: EnrichmentRequest = EnrichmentRequest(),
    http_request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Enrich candidate data from LinkedIn using Apify scrapers."""
    try:
        existing = await candidate_repo.get_by_id_str(candidate_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(existing, current_user)
        from app.domains.candidates.services.candidate_enrichment_service import candidate_enrichment_service
        result = await candidate_enrichment_service.enrich_candidate(
            db=candidate_repo.db,
            candidate_id=uuid.UUID(candidate_id),
            linkedin_url=enrichment_request.linkedin_url,
            include_experiences=enrichment_request.include_experiences,
            include_education=enrichment_request.include_education,
            include_email_discovery=enrichment_request.include_email_discovery,
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Enrichment failed"))
        logger.info(
            f"Candidate enriched: {candidate_id} - {len(result.get('fields_updated', []))} fields updated"
        )
        return {
            "success": True,
            "candidate_id": candidate_id,
            "fields_updated": result.get("fields_updated", []),
            "experiences_added": result.get("experiences_added", 0),
            "education_added": result.get("education_added", 0),
            "source": result.get("source", "apify"),
            "message": f"Enrichment completed: {len(result.get('fields_updated', []))} fields updated",
        }
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(http_request.state, "request_id", "unknown") if http_request else "unknown"
        logger.exception(
            "[enrich_candidate] failed request_id=%s candidate_id=%s user_id=%s",
            _rid, candidate_id, getattr(current_user, "id", None),
        )
        raise HTTPException(status_code=500, detail="Falha ao enriquecer o candidato.")
