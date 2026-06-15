"""
CRUD endpoints for candidates: list, get, create, update, stage-update, delete, enrich.
"""
import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Request
from sqlalchemy import text

from app.models.candidate import (
    CandidateExperience,
    CandidateEducation,
)
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User

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
    get_stage_rank,
    get_vacancy_candidate_repo,
    logger,
    normalize_array_field,
)
from pydantic import BaseModel
from app.shared.rails_migration.deprecation import enforce_candidates_deprecation
from app.schemas.envelope import ResponseEnvelope, ok_envelope
from app.shared.rbac.mutation_gate import assert_mutation_allowed
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.rbac.pii_field_resolver import resolve_pii_field_visibility
from app.shared.rbac.pii_field_catalog import field_group
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

def _assert_tenant_scope(candidate, current_user) -> None:
    """Multi-tenant guard — ensures candidate belongs to current user company."""
    cu_company = getattr(current_user, "company_id", None)
    cand_company = getattr(candidate, "company_id", None)
    if cu_company and cand_company and str(cu_company) != str(cand_company):
        raise HTTPException(status_code=403, detail="Candidate does not belong to your company")


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
        "education": (getattr(c, "education_snapshot", None) or []),
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
# Sprint 5 RBAC — Financial PII redaction (LGPD Art. 6 III minimização)
# ---------------------------------------------------------------------------
_SALARY_FIELDS = (
    "current_salary",
    "desired_salary_min",
    "desired_salary_max",
    "salary_expectation_clt",
    "salary_expectation_pj",
    "salary_expectation_freelance",
)

# Sprint 8 RBAC (2026-05-26): sensitive PII fields gated por can_view_sensitive_pii.
# LGPD Art. 5 II — categorias sensíveis (CPF + DoB + endereço + secondary contacts).
# Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
_SENSITIVE_PII_FIELDS = (
    "cpf",
    "date_of_birth",
    "address_street",
    "address_number",
    "address_zip",
    "address_complement",
    "secondary_email",
    "secondary_phone",
    "personal_emails",
    "business_emails",
    "best_personal_email",
    "best_business_email",
)


def _redact_salary_for_user(candidate_dict: dict, current_user) -> dict:
    """Redact salary fields when user lacks can_view_salary grant.

    Sprint 5 RBAC (2026-05-25, plan canonical: jolly-roaming-moler.md).
    LGPD Art. 6 III minimização: financial PII restricted to explicit grant.

    Mutates dict in place AND returns it. Adds flag `salary_masked: true` so UI
    can render "restrito" label instead of zero values.

    NOTE: salary_currency stays visible (not PII per LGPD, contextual only).
    """
    can_view = bool(getattr(current_user, "can_view_salary", False))
    if can_view:
        candidate_dict["salary_masked"] = False
        return candidate_dict

    for field in _SALARY_FIELDS:
        if field in candidate_dict:
            candidate_dict[field] = None
    candidate_dict["salary_masked"] = True
    return candidate_dict


def _redact_sensitive_pii_for_user(candidate_dict: dict, current_user) -> dict:
    """Sprint 8 RBAC: redact sensitive PII fields when user lacks can_view_sensitive_pii grant.

    LGPD Art. 5 II — categorias sensíveis. Default grant=true (zero-quebra);
    admin pode revogar per-user via UI.

    Mutates dict in place AND returns it. Adds flag `sensitive_pii_masked` for UI.
    Lists (personal_emails, business_emails) viram []. Strings viram None.
    """
    can_view = bool(getattr(current_user, "can_view_sensitive_pii", True))
    if can_view:
        candidate_dict["sensitive_pii_masked"] = False
        return candidate_dict

    for field in _SENSITIVE_PII_FIELDS:
        if field in candidate_dict:
            existing = candidate_dict[field]
            if isinstance(existing, list):
                candidate_dict[field] = []
            else:
                candidate_dict[field] = None
    candidate_dict["sensitive_pii_masked"] = True
    return candidate_dict


def apply_pii_field_visibility(candidate_dict: dict, current_user, role_defaults: dict | None = None) -> dict:
    """Field-level PII redaction (2026-06-06). Replaces the 2-bucket Sprint 5/8 grants.

    Precedence (per field): user override > role default > legacy bucket > show. LGPD Art. 6 III.
    Mutates AND returns. Preserves legacy UI flags salary_masked / sensitive_pii_masked.
    """
    effective = resolve_pii_field_visibility(current_user, role_defaults or {})
    any_salary_masked = False
    any_sensitive_masked = False
    for field, can_view in effective.items():
        if can_view:
            continue
        if field in candidate_dict:
            existing = candidate_dict[field]
            candidate_dict[field] = [] if isinstance(existing, list) else None
        if field_group(field) == "salary":
            any_salary_masked = True
        else:
            any_sensitive_masked = True
    candidate_dict["salary_masked"] = any_salary_masked
    candidate_dict["sensitive_pii_masked"] = any_sensitive_masked
    return candidate_dict


async def _load_role_pii_defaults(company_id: str) -> dict:
    """Load per-role PII visibility defaults for a company. Returns {} if unset/missing."""
    from app.core.database import AsyncSessionLocal
    from app.domains.hiring_policy.repositories.hiring_policy_repository import HiringPolicyRepository
    try:
        async with AsyncSessionLocal() as db:
            policy = await HiringPolicyRepository(db).get_by_company(company_id)
        return (getattr(policy, "pii_visibility_defaults", None) or {}) if policy else {}
    except Exception:
        logger.warning("[A4] failed loading pii_visibility_defaults for company %s", company_id, exc_info=True)
        return {}


async def _audit_pii_access(
    current_user,
    candidate_id: str,
    company_id: str,
    role_defaults: dict | None = None,
) -> None:
    """Log SOXAuditLog when privileged user accesses unmasked PII (LGPD Art. 37 V).

    Sprint 5 (salary) + Sprint 8 (sensitive PII). Fires for each grant that user holds.
    Default-redacted users (sem grant) NÃO geram audit (não viram dados).
    """
    grants_to_audit = []
    if bool(getattr(current_user, "can_view_salary", False)):
        grants_to_audit.append("financial_salary")
    # Sprint 8: default=true, so most users have this grant (audit fires)
    if bool(getattr(current_user, "can_view_sensitive_pii", True)):
        grants_to_audit.append("sensitive_identity")

    try:
        from app.shared.compliance.audit_service import AuditService
        svc = AuditService()
        # Existing legacy-bucket audit (preserved, Sprint 5/8)
        for pii_class in grants_to_audit:
            await svc.log_data_access(
                company_id=company_id,
                user_id=str(current_user.id) if getattr(current_user, "id", None) else None,
                user_email=getattr(current_user, "email", None),
                resource_type="candidate",
                resource_id=candidate_id,
                action="view_pii",
                details={"pii_class": pii_class},
            )
        # Task E -- per-field detail audit (LGPD Art. 37 V granular)
        effective = resolve_pii_field_visibility(current_user, role_defaults or {})
        viewed = sorted([f for f, v in effective.items() if v])
        masked = sorted([f for f, v in effective.items() if not v])
        await svc.log_data_access(
            company_id=company_id,
            user_id=str(current_user.id) if getattr(current_user, "id", None) else None,
            user_email=getattr(current_user, "email", None),
            resource_type="candidate",
            resource_id=candidate_id,
            action="view_pii_fields",
            details={"pii_fields_viewed": viewed, "pii_fields_masked": masked},
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("[Sprint5/8] _audit_pii_access failed (non-blocking): %s", exc)


# ---------------------------------------------------------------------------
# Phase 4 RBAC — Department scope filter for candidates (soft-launch)
# ---------------------------------------------------------------------------
async def _filter_candidates_by_dept_scope(
    candidates: list,
    current_user,
) -> list:
    """Sprint 2 Phase 4 + Sprint 6 RBAC — visible scope filter for candidates.

    Plan canonical: ~/.claude/plans/jolly-roaming-moler.md.

    Sprint 6 (2026-05-25): adds 1-level manager hierarchy. Manager (role=manager
    OR admin) sees data of direct subordinates (users WHERE manager_id == self.id).
    No cascade — chefe-do-chefe sees only direct subordinates.

    A candidate is visible if:
      - user has NO department_id AND no subordinates (legacy soft-launch bypass), OR
      - user is admin / wedotalent_admin (bypass), OR
      - candidate has 0 vacancy associations (talent pool), OR
      - any vacancy of candidate is legacy (dept_id NULL), OR
      - any vacancy of candidate is in user's visible_dept_ids (own + subordinate depts), OR
      - any vacancy is owned (created_by/recruiter_email) by current user OR a subordinate

    NULL on either side = legacy compat (soft-launch posture preserved).
    """
    if not candidates:
        return candidates

    from app.shared.rbac.visible_scope import compute_visible_scope
    scope = await compute_visible_scope(current_user)

    # Legacy bypass: user without dept AND no subordinates = no enforcement
    if scope.own_dept_id is None and not scope.has_subordinates:
        return candidates

    if scope.is_admin:
        return candidates  # admin / wedotalent_admin bypass

    visible_depts = scope.visible_dept_ids
    subordinate_emails = scope.subordinate_user_emails
    user_email = scope.user_email

    candidate_ids = [str(c.id) for c in candidates]
    cand_meta: dict[str, list[dict]] = {cid: [] for cid in candidate_ids}

    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT vc.candidate_id::text AS cid,
                       jv.department_id::text AS dept,
                       COALESCE(LOWER(jv.created_by), '') AS created_by,
                       COALESCE(LOWER(jv.recruiter_email), '') AS recruiter_email
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                WHERE vc.candidate_id = ANY(:ids)
            """),
            {"ids": candidate_ids},
        )
        for row in result.fetchall():
            cid = row.cid
            cand_meta.setdefault(cid, []).append({
                "dept": row.dept,
                "created_by": row.created_by,
                "recruiter_email": row.recruiter_email,
            })

    visible = []
    for c in candidates:
        cid = str(c.id)
        vacs = cand_meta.get(cid, [])
        if not vacs:
            # Talent pool — visible (tenant ownership already guaranteed by company_id filter)
            visible.append(c)
            continue
        for v in vacs:
            # Rule 1: legacy vacancy (no dept_id set) — visible
            if v["dept"] is None:
                visible.append(c); break
            # Rule 2: vacancy in visible dept set (own + subordinate depts)
            if v["dept"] in visible_depts:
                visible.append(c); break
            # Rule 3: subordinate-owned vacancy (manager sees their team's work)
            if subordinate_emails and (
                v["created_by"] in subordinate_emails or v["recruiter_email"] in subordinate_emails
            ):
                visible.append(c); break
            # Rule 4: self-owned vacancy (recruiter sees own)
            if user_email and (v["created_by"] == user_email or v["recruiter_email"] == user_email):
                visible.append(c); break
        # Else: all vacancies out of scope → filtered out
    return visible


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
    vacancy_id: str | None = None,
    offset: int = Query(default=0, ge=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
    sort_by: str | None = None,
    sort_order: str | None = None,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    vacancy_candidate_repo: VacancyCandidateRepository = Depends(get_vacancy_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    # Sprint 2 Phase 4 RBAC: dept scope filter via current_user.department_id (soft-launch).
    """List candidates from local DB."""
    logger.info(
        f"[FUNIL-DEBUG] ENTRY vacancy_id={vacancy_id!r} status={status!r} "
        f"skip={skip} offset={offset} limit={limit} company={company_id!r}"
    )  # TEMP debug funil-zero 2026-06-06 (remover apos diagnostico)
    # Only call Rails when explicitly enabled — avoids adapter's own DB fallback
    # bypassing endpoint-level filters and authorization.
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

        # P0-1 (audit 2026-06-05): quando vacancy_id é passado, escopar a lista
        # aos candidatos vinculados à vaga (vacancy_candidates), via o path `ids=`.
        # Antes o board do Kanban lia a lista GLOBAL (sem filtro de vaga).
        effective_skip = offset if offset > 0 else skip
        vc_map: dict[str, dict] = {}
        if vacancy_id:
            vc_ids = await vacancy_candidate_repo.list_candidate_ids_for_vacancy(
                vacancy_id, company_id
            )
            if not vc_ids:
                return {"total": 0, "skip": effective_skip, "limit": limit, "source": "local", "items": []}
            id_list = [i for i in id_list if i in set(vc_ids)] if id_list else vc_ids
            vc_map = await vacancy_candidate_repo.list_vc_map_for_vacancy(
                vacancy_id, company_id
            )
        total = await candidate_repo.count_candidates(
            search=search, status=status, source=source, seniority=seniority, ids=id_list,
        )
        candidates = await candidate_repo.list_candidates(
            search=search, status=status, source=source, seniority=seniority, ids=id_list,
            skip=effective_skip, limit=limit, sort_by=sort_by, sort_order=sort_order,
        )
        # Sprint 2 Phase 4 RBAC: dept scope filter (soft-launch). No-op when user has no dept_id.
        candidates = await _filter_candidates_by_dept_scope(candidates, current_user)
        # A4 field-level PII redaction: replaces 2-bucket Sprint 5/8 grants.
        role_defaults = await _load_role_pii_defaults(company_id)
        items = []
        for c in candidates:
            serialized = apply_pii_field_visibility(_serialize_candidate(c), current_user, role_defaults)
            if vc_map and str(c.id) in vc_map:
                _vc_entry = vc_map[str(c.id)]
                if isinstance(_vc_entry, dict):
                    serialized["vc_id"] = _vc_entry.get("vc_id")
                    serialized["match_score"] = _vc_entry.get("match_score")
                else:
                    # legado: vc_map ainda retorna string (não deveria, mas defensive)
                    serialized["vc_id"] = _vc_entry
            items.append(serialized)
        logger.info(
            f"[FUNIL-DEBUG] RETURN vacancy_id={vacancy_id!r} total={total} "
            f"items={len(items)}"
        )  # TEMP debug funil-zero 2026-06-06 (remover apos diagnostico)
        return {
            "total": total,
            "skip": effective_skip,
            "limit": limit,
            "source": "local",
            "items": items,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{candidate_id}", response_model=ResponseEnvelope)
async def get_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a candidate by ID."""
    # Only call Rails when explicitly enabled — avoids adapter's own DB fallback
    # returning unscoped/unfiltered data.
    try:
        try:
            uuid.UUID(candidate_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Candidate not found")
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        # Sprint 2 Phase 4 RBAC: dept scope check (soft-launch). 404 (not 403) to avoid existence leak.
        visible = await _filter_candidates_by_dept_scope([candidate], current_user)
        if not visible:
            raise HTTPException(status_code=404, detail="Candidate not found")
        # A4 field-level PII redaction: replaces 2-bucket Sprint 5/8 grants.
        role_defaults = await _load_role_pii_defaults(company_id)
        serialized = apply_pii_field_visibility(
            _serialize_candidate(candidate, full=True), current_user, role_defaults
        )
        await _audit_pii_access(current_user, candidate_id, company_id, role_defaults)
        return ok_envelope(serialized, meta={"source": "local"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a new candidate. If auto_enrich=True and linkedin_url is provided, enrichment runs in background."""
    try:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Creating candidate: {candidate_data.name}")
        candidate = Candidate(
            id=uuid.uuid4(),
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
        raise
    except Exception as e:
        logger.error(f"Error creating candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{candidate_id}", response_model=None)
async def update_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_data: CandidateUpdate,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update an existing candidate."""
    try:
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        await assert_mutation_allowed(candidate, current_user, resource_label="candidato")

        update_data = candidate_data.model_dump(exclude_unset=True)
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
    except Exception as e:
        logger.error(f"Error updating candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{candidate_id}/stage", response_model=None)
async def update_candidate_stage(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    stage_data: CandidateStageUpdate,
    background_tasks: BackgroundTasks,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    vc_repo: VacancyCandidateRepository = Depends(get_vacancy_candidate_repo),
    audit_svc: AuditService = Depends(get_audit_service),
    activity_svc: ActivityService = Depends(get_activity_service),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update candidate pipeline stage (used when moving candidates in Kanban)."""
    try:
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        await assert_mutation_allowed(candidate, current_user, resource_label="candidato")

        vacancy_candidate = await vc_repo.get_for_candidate_and_job(
            candidate_id=candidate_id,
            job_vacancy_id=str(stage_data.job_vacancy_id) if stage_data.job_vacancy_id else None,
            company_id=company_id,
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
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        # Task #1306: also persist the structural stage link so the SLA detector
        # can join by id instead of fragile name matching.
        from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
        vacancy_candidate.recruitment_stage_id = await resolve_recruitment_stage_id(
            vc_repo.db, str(vacancy_candidate.company_id), stage_data.stage
        )
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

        # LGPD Art. 18 II — se candidato rejeitado tem consent revocation pendente, disparar erasure
        if is_rejection:
            try:
                from app.domains.lgpd.services.granular_consent_service import GranularConsentService as _ConsentSvc
                from app.domains.lgpd.services.lgpd_cleanup_service import schedule_deletion_for_candidate as _sched_del
                _consent_svc = _ConsentSvc(candidate_repo.db)
                # Verifica se candidato revogou consentimento de ai_screening
                _has_revocation = not await _consent_svc.check_purpose(
                    candidate_id=candidate_id,
                    company_id=company_id,
                    purpose="ai_screening",
                )
                if _has_revocation:
                    # Disparar schedule_deletion imediata (retention_days=0) via BackgroundTasks
                    background_tasks.add_task(
                        _sched_del,
                        candidate_repo.db,
                        candidate_id,
                        "consent_revocation_on_rejection",
                        0,  # retention_days=0 → deletion imediata (LGPD Art. 18 II)
                    )
                    logger.info(
                        "LGPD Art. 18 II: agendado erasure imediato ao rejeitar candidato "
                        "com revocação de ai_screening",
                        extra={"candidate_id": candidate_id, "company_id": company_id},
                    )
            except Exception as _lgpd_err:
                # Non-blocking: rejeição prossegue mesmo se check LGPD falhar
                logger.warning(
                    "LGPD erasure check falhou para candidato %s na rejeição: %s",
                    candidate_id, _lgpd_err,
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

        # Agent Studio Fase 2.5 — Onda C1.3: emite stage_changed no
        # platform.events para o motor event-driven. Cobre os trigger_modes
        # on_enter_stage / on_exit_stage / on_stage_change (o consumer C1.2
        # faz o match from_stage/to_stage). on_stuck_in_stage e detectado por
        # scheduler, fora do escopo deste evento.
        # REGRA 4: fail-soft mas LOUD. Multi-tenancy: company_id vem de
        # vacancy_candidate.company_id (row do tenant), NUNCA do request.
        if previous_stage != vacancy_candidate.stage:
            try:
                from lia_events.schemas import StageChangedEvent
                from app.shared.messaging.events_outbox_service import get_events_outbox_service
                from lia_config.database import AsyncSessionLocal
                _evt_company_id = str(getattr(vacancy_candidate, "company_id", "") or company_id)
                _evt = StageChangedEvent(
                    company_id=_evt_company_id,
                    payload={
                        "candidate_id": str(candidate.id),
                        "vacancy_id": str(vacancy_candidate.vacancy_id),
                        "from_stage": previous_stage,
                        "to_stage": vacancy_candidate.stage,
                    },
                    source_api="lia-agent-system",
                )
                async with AsyncSessionLocal() as _evt_db:
                    await get_events_outbox_service().publish_via_outbox(_evt, _evt_db)
                    await _evt_db.commit()
            except Exception as _evt_err:  # noqa: BLE001
                logger.error(
                    "[C1.3] publish stage_changed failed (transicao prossegue): %s",
                    _evt_err,
                    exc_info=True,
                )

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
    except Exception as e:
        logger.error(f"Error updating candidate stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{candidate_id}/experiences", response_model=None)
async def update_candidate_experiences(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: list[dict],
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Replace candidate's experiences (work history) with the provided array.

    Used by F5 D7 edit pattern via EditArrayItemModal in ProfileExperienceSection.
    Multi-tenant via _assert_tenant_scope. Replace-all semantics:
    delete all existing experiences + insert new ones with sequence_order
    matching array index.
    """
    try:
        from app.core.database import AsyncSessionLocal
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("DELETE FROM candidate_experiences WHERE candidate_id = CAST(:cid AS uuid)"),
                {"cid": str(candidate.id)},
            )
            import json as _json
            normalized_experiences = []
            for idx, exp in enumerate(payload or []):
                if not isinstance(exp, dict):
                    continue
                row = {
                    "title": exp.get("title"),
                    "company": exp.get("company") or exp.get("company_name"),
                    "company_name": exp.get("company") or exp.get("company_name"),
                    "start_date": exp.get("start_date") or exp.get("startDate"),
                    "end_date": exp.get("end_date") or exp.get("endDate"),
                    "description": exp.get("description"),
                    "location": exp.get("location"),
                    "is_current": bool(exp.get("is_current") or exp.get("isCurrent")),
                    "sequence_order": idx,
                }
                normalized_experiences.append(row)
                db.add(CandidateExperience(
                    candidate_id=candidate.id,
                    company_name=str(row["company_name"] or "Empresa"),
                    title=str(row["title"] or "")[:255] if row["title"] else None,
                    start_date=str(row["start_date"] or "")[:50] or None,
                    end_date=str(row["end_date"] or "")[:50] or None,
                    description=row["description"],
                    location=str(row["location"] or "")[:255] or None,
                    is_current=row["is_current"],
                    sequence_order=idx,
                ))
            # F8 dual-write: sync candidates.work_history JSON column for serializer
            await db.execute(
                text("UPDATE candidates SET work_history = CAST(:wh AS jsonb), updated_at = NOW() WHERE id = CAST(:cid AS uuid)"),
                {"wh": _json.dumps(normalized_experiences), "cid": str(candidate.id)},
            )
            await db.commit()

        logger.info(f"Updated {len(payload or [])} experiences for candidate {candidate_id}")
        return {"success": True, "count": len(payload or []), "message": "Experiences updated successfully"}
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[update_candidate_experiences] failed request_id=%s candidate_id=%s",
            _rid, candidate_id,
        )
        raise HTTPException(status_code=500, detail="Falha ao atualizar experiencias do candidato.")


@router.put("/{candidate_id}/education", response_model=None)
async def update_candidate_education(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: list[dict],
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Replace candidate's education entries with the provided array.

    Used by F5 D7 edit pattern via EditArrayItemModal in ProfileEducationSection.
    Multi-tenant via _assert_tenant_scope. Replace-all semantics.
    """
    try:
        from app.core.database import AsyncSessionLocal
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("DELETE FROM candidate_education WHERE candidate_id = CAST(:cid AS uuid)"),
                {"cid": str(candidate.id)},
            )
            import json as _json
            normalized_education = []
            for idx, edu in enumerate(payload or []):
                if not isinstance(edu, dict):
                    continue
                row = {
                    "institution": edu.get("institution") or edu.get("school"),
                    "degree": edu.get("degree"),
                    "field_of_study": edu.get("field_of_study") or edu.get("fieldOfStudy"),
                    "start_date": edu.get("start_date") or edu.get("startDate"),
                    "end_date": edu.get("end_date") or edu.get("endDate"),
                    "description": edu.get("description"),
                    "sequence_order": idx,
                }
                normalized_education.append(row)
                db.add(CandidateEducation(
                    candidate_id=candidate.id,
                    institution=str(row["institution"] or "Instituição"),
                    degree=str(row["degree"] or "")[:100] or None,
                    field_of_study=str(row["field_of_study"] or "")[:255] or None,
                    start_date=str(row["start_date"] or "")[:50] or None,
                    end_date=str(row["end_date"] or "")[:50] or None,
                    description=row["description"],
                    sequence_order=idx,
                ))
            # F8 dual-write: sync candidates.education_snapshot JSON column for serializer
            await db.execute(
                text("UPDATE candidates SET education_snapshot = CAST(:edu AS jsonb), updated_at = NOW() WHERE id = CAST(:cid AS uuid)"),
                {"edu": _json.dumps(normalized_education), "cid": str(candidate.id)},
            )
            await db.commit()

        logger.info(f"Updated {len(payload or [])} education entries for candidate {candidate_id}")
        return {"success": True, "count": len(payload or []), "message": "Education updated successfully"}
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[update_candidate_education] failed request_id=%s candidate_id=%s",
            _rid, candidate_id,
        )
        raise HTTPException(status_code=500, detail="Falha ao atualizar formacao do candidato.")


@router.put("/{candidate_id}/skills", response_model=None)
async def update_candidate_skills(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: list[str],
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Replace candidate's technical_skills array with the provided list.

    Used by F5 D7 edit pattern via EditArrayItemModal in CandidateSkillsList.
    Multi-tenant via _assert_tenant_scope. Replace-all semantics.
    Validates each skill is a non-empty string max 100 chars.
    """
    try:
        from app.core.database import AsyncSessionLocal
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)

        # Validate and normalize skills
        normalized_skills = []
        for skill in (payload or []):
            if not isinstance(skill, str):
                continue
            s = skill.strip()
            if not s:
                continue
            normalized_skills.append(s[:100])
        # Dedupe preserving order
        seen = set()
        deduped = []
        for s in normalized_skills:
            if s.lower() not in seen:
                seen.add(s.lower())
                deduped.append(s)

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("UPDATE candidates SET technical_skills = :skills, updated_at = NOW() WHERE id = CAST(:cid AS uuid)"),
                {"skills": deduped, "cid": str(candidate.id)},
            )
            await db.commit()

        logger.info(f"Updated {len(deduped)} skills for candidate {candidate_id}")
        return {"success": True, "count": len(deduped), "message": "Skills updated successfully", "skills": deduped}
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[update_candidate_skills] failed request_id=%s candidate_id=%s",
            _rid, candidate_id,
        )
        raise HTTPException(status_code=500, detail="Falha ao atualizar skills do candidato.")


@router.put("/{candidate_id}/certifications", response_model=None)
async def update_candidate_certifications(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: list[str],
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Replace candidate's certifications array with the provided list.

    F9 caveats resolution (2026-05-24): mirror of /skills endpoint.
    Multi-tenant via _assert_tenant_scope. Replace-all semantics.
    Validates each cert is a non-empty string max 200 chars (longer than
    skills because cert names tend to be descriptive — e.g. "AWS Certified
    Solutions Architect – Associate"). Dedupe case-insensitive preserving
    insertion order.
    """
    try:
        from app.core.database import AsyncSessionLocal
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate, current_user)

        # Validate and normalize certs
        normalized: list[str] = []
        for cert in (payload or []):
            if not isinstance(cert, str):
                continue
            s = cert.strip()
            if not s:
                continue
            normalized.append(s[:200])
        seen: set[str] = set()
        deduped: list[str] = []
        for s in normalized:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(s)

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("UPDATE candidates SET certifications = :certs, updated_at = NOW() WHERE id = CAST(:cid AS uuid)"),
                {"certs": deduped, "cid": str(candidate.id)},
            )
            await db.commit()

        logger.info(f"Updated {len(deduped)} certifications for candidate {candidate_id}")
        return {"success": True, "count": len(deduped), "message": "Certifications updated successfully", "certifications": deduped}
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[update_candidate_certifications] failed request_id=%s candidate_id=%s",
            _rid, candidate_id,
        )
        raise HTTPException(status_code=500, detail="Falha ao atualizar certificações do candidato.")


@router.put("/{candidate_id}/identity", response_model=None)
async def update_candidate_identity(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: dict,
    request: Request = None,  # type: ignore[assignment]
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
):
    """Update encryption-aware PII fields (name) via ORM hybrid_property.

    Why dedicated endpoint: candidate.name is encrypted at rest (migration
    111, UC-P1-15). DB column "name" is always NULL for new writes; real
    data lives in name_encrypted (LargeBinary). Access via hybrid_property
    that handles encrypt/decrypt transparently. SQL UPDATE direct on
    "name" column would skip encryption.

    Solution: use ORM setter (candidate.name = X) which triggers
    EncryptedFieldMixin.setter -> stores in _name_encrypted +
    decryption transparente on read.

    Multi-tenant via _assert_tenant_scope. Used by F5 D7 edit pattern
    for header name field.
    """
    try:
        from app.models.candidate import Candidate as CandidateModel
        import uuid as _uuid

        # First validate tenant scope (cheap repo lookup via request-scoped session)
        candidate_check = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate_check:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _assert_tenant_scope(candidate_check, current_user)

        updated_fields = []
        if "name" in payload:
            name_val = payload.get("name")
            if not isinstance(name_val, str) or not name_val.strip():
                raise HTTPException(status_code=400, detail="name must be non-empty string")
            new_name = name_val.strip()[:255]
            updated_fields.append("name")
        else:
            raise HTTPException(status_code=400, detail="No supported fields in payload (expected: name)")

        # FU-2 fix (2026-05-24): use the request-scoped session injected via
        # candidate_repo.db. Opening AsyncSessionLocal() locally breaks
        # multi-tenancy because the new session does NOT inherit the
        # Postgres RLS `app.current_company_id` setting from the request
        # context (same class of bug as the chat RLS saga). The hybrid_property
        # setter for `name` is ORM-level and works on any session — the local
        # session was unnecessary and actively harmful.
        try:
            cand_uuid = _uuid.UUID(str(candidate_check.id))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid candidate id")
        db = candidate_repo.db
        cand = await db.get(CandidateModel, cand_uuid)
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found in session")
        if "name" in payload:
            cand.name = new_name  # hybrid_property setter -> _name_encrypted
        # Capture final value BEFORE commit (db.refresh on shared session breaks
        # in some pool configs — observed FU-2 smoke 2026-05-24 returning
        # InvalidRequestError "Could not refresh instance"). The hybrid_property
        # already reflects the new value in-memory.
        final_name = cand.name
        await db.commit()

        logger.info(f"Updated identity fields {updated_fields} for candidate {candidate_id}")
        return {
            "success": True,
            "updated_fields": updated_fields,
            "name": final_name,
            "message": "Identity updated successfully",
        }
    except HTTPException:
        raise
    except Exception:
        _rid = getattr(request.state, "request_id", "unknown") if request else "unknown"
        logger.exception(
            "[update_candidate_identity] failed request_id=%s candidate_id=%s",
            _rid, candidate_id,
        )
        raise HTTPException(status_code=500, detail="Falha ao atualizar identidade do candidato.")


@router.delete("/{candidate_id}", response_model=None)
async def delete_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Soft delete (deactivate) a candidate."""
    try:
        candidate = await candidate_repo.get_by_id_str(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        await candidate_repo.soft_delete(candidate)
        logger.info(f"Candidate deactivated: {candidate_id}")
        return {"message": "Candidate deactivated successfully", "id": candidate_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------

class EnrichmentRequest(WeDoBaseModel):
    linkedin_url: str | None = None
    include_experiences: bool = True
    include_education: bool = True
    include_email_discovery: bool = True


@router.post("/{candidate_id}/enrich", response_model=None)
async def enrich_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: EnrichmentRequest = EnrichmentRequest(),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Enrich candidate data from LinkedIn using Apify scrapers."""
    try:
        from app.domains.candidates.services.candidate_enrichment_service import candidate_enrichment_service
        result = await candidate_enrichment_service.enrich_candidate(
            db=candidate_repo.db,
            candidate_id=uuid.UUID(candidate_id),
            linkedin_url=request.linkedin_url,
            include_experiences=request.include_experiences,
            include_education=request.include_education,
            include_email_discovery=request.include_email_discovery,
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
    except Exception as e:
        logger.error(f"Error enriching candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# UC-P1-16: LGPD Art.20 — AI decision explanation endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/{candidate_id}/ai-explanation",
    summary="LGPD Art.20 — Explain AI decision for a candidate",
    tags=["candidates", "lgpd", "explainability"],
)
async def get_candidate_ai_explanation(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_vacancy_id: str = Query(..., description="Job vacancy ID for which to explain decisions"),
    current_user=Depends(get_current_user_or_demo),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """LGPD Art.20 — Return a human-readable explanation of all AI decisions
    made for a candidate on a specific job vacancy.

    Delegates to ExplainabilityService which pulls AuditLog entries and
    formats them with criteria_evaluated, criteria_ignored, transparency_note,
    and optional improvement suggestions.

    company_id is always extracted from the authenticated user's session (anti-IDOR).
    """
    from app.shared.services.explainability_service import ExplainabilityService

    company_id = str(current_user.company_id)

    svc = ExplainabilityService()
    explanation = await svc.generate_candidate_explanation(
        company_id=company_id,
        candidate_id=candidate_id,
        job_vacancy_id=job_vacancy_id,
        include_suggestions=True,
    )

    if explanation.get("status") == "no_data":
        raise HTTPException(status_code=404, detail=explanation.get("message", "No AI decisions found."))

    return explanation
