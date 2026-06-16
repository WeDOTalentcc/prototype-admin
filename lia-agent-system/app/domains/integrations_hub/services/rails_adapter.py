"""
Rails Adapter — Field mapping and data source abstraction.

Maps between fork models (UUID, 275 tables) and Rails models (bigint, 12 tables).
Provides a unified interface: tries Rails first, falls back to local DB.

Auth: Uses RAILS_API_TOKEN env var for service-to-service calls when no user
token is provided. The token is injected automatically by the dependency.

Usage:
    from app.domains.integrations_hub.services.rails_adapter import RailsAdapter
    adapter = RailsAdapter(db_session)
    candidate = await adapter.get_candidate(candidate_id)
    jobs = await adapter.list_jobs(search="developer", page=1)
"""
import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Whether to try Rails first (set RAILS_API_URL to enable)
RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL"))
RAILS_API_TOKEN = os.environ.get("RAILS_API_TOKEN", "")


# ----------------------------------------------------------------
# Field Mapping: Fork ↔ Rails
# ----------------------------------------------------------------

CANDIDATE_FORK_TO_RAILS = {
    # Fork field → Rails field (complete mapping)
    # --- IDs ---
    "id": "id",                              # UUID (fork) ↔ bigint (Rails)
    # --- Basic Info ---
    "name": "name",                          # Fork has single name field
    "email": "email",
    "secondary_email": "secondary_email",
    "phone": "phone",
    "mobile_phone": "mobile_phone",
    "secondary_phone": "secondary_phone",
    "linkedin_url": "linkedin",
    "github_url": "github",
    "portfolio_url": "portfolio",
    "avatar_url": "avatar_url",
    # --- Personal ---
    "date_of_birth": "date_birth",
    "gender": "gender",                      # Fork: string, Rails: integer enum
    "nationality": "nationality",
    "marital_status": "marital_status",      # Fork: string, Rails: integer enum
    "cpf": "cpf",                            # Fork may encrypt, Rails plaintext
    # --- Professional ---
    "current_title": "role_name",
    "current_company": "current_company",
    "seniority_level": "seniority_level",  # Work C: Rails now has this column directly
    "self_introduction": "self_introduction",
    "resume_text": "curriculum_text",
    "resume_url": "curriculum_pdf_url",
    # --- Location ---
    "location_city": "city",
    "location_state": "state",
    "location_country": "country",
    "address_street": "street",
    "address_number": "number",              # Fork: String, Rails: Integer
    "address_district": "district",
    "address_zip": "zip",
    "address_complement": "complement",
    # --- Salary ---
    "current_salary": "current_salary",
    "desired_salary_min": "desired_salary",
    "salary_expectation_clt": "clt_expectation",
    "salary_expectation_pj": "pj_expectation",
    "salary_expectation_freelance": "freelance_expectation",
    "salary_currency": "currency",
    # --- Preferences ---
    "is_remote": "remote_work",
    "willing_to_relocate": "mobility",
    # --- Meta ---
    "source": "source",
    # --- Expanded fields (Work C — now in both fork and Rails) ---
    "technical_skills": "technical_skills",
    "soft_skills": "soft_skills",
    "languages": "languages",
    "certifications": "certifications",
    "years_of_experience": "years_of_experience",
    "diversity_race_ethnicity": "diversity_race_ethnicity",
    "diversity_disability": "diversity_disability",
    "diversity_disability_type": "diversity_disability_type",
    "diversity_lgbtqia": "diversity_lgbtqia",
    "diversity_refugee": "diversity_refugee",
    "diversity_age_50_plus": "diversity_age_50_plus",
    "diversity_indigenous": "diversity_indigenous",
    "diversity_documents": "diversity_documents",
    "diversity_self_declared_at": "diversity_self_declared_at",
    "diversity_document_deadline": "diversity_document_deadline",
    # --- Fork-only (remain local) ---
    # timezone, embeddings, pearch_profile_id, ats_candidate_id,
    # cover_letter, is_open_to_work, is_decision_maker, headline
    # --- Rails-only (no Fork equivalent) ---
    # uid, completed_register, accept_terms, interests (string vs array), comments
}

CANDIDATE_RAILS_TO_FORK = {v: k for k, v in CANDIDATE_FORK_TO_RAILS.items()
                           if isinstance(v, str)}

JOB_FORK_TO_RAILS = {
    # Fork field → Rails field (complete mapping)
    "id": "id",                              # UUID ↔ bigint
    "title": "title",
    "description": "description",
    "location": "city",                      # Fork single, Rails city/state/country
    "work_model": "workplace_type",
    "is_confidential": "is_confidential",    # Fork legacy field
    "open_date": "published_date",
    "deadline": "application_deadline",
    "is_affirmative": "disabilities",        # Approximate mapping
    "published_linkedin": "provider",        # Fork: bool, Rails: string "linkedin"
    # --- Rails-only ---
    # user_id, account_id, provider_job_id, company_id (bigint FK),
    # job_url, career_page_*, friendly_badge
    # --- Expanded fields (Work C — now in both fork and Rails) ---
    "status": "status",
    "department": "department",
    "employment_type": "employment_type",
    "seniority_level": "seniority_level",
    "priority": "priority",
    "urgency_level": "urgency_level",
    "technical_requirements": "technical_requirements",
    "behavioral_competencies": "behavioral_competencies",
    "screening_questions": "screening_questions",
    "interview_stages": "interview_stages",
    "languages": "languages",
    "salary_range": "salary_range",
    "bonus_range": "bonus_range",
    "benefits": "benefits",
    "deadline_screening": "deadline_screening",
    "deadline_shortlist": "deadline_shortlist",
    "deadline_closing": "deadline_closing",
    "manager": "manager",
    "manager_email": "manager_email",
    "recruiter": "recruiter",
    "recruiter_email": "recruiter_email",
    "created_by": "created_by",
    "organizational_structure": "organizational_structure",
    "tags": "tags",
    "visibility": "visibility",
    "public_slug": "public_slug",
    "budget": "budget",
    "budget_used": "budget_used",
    "fork_uuid": "fork_uuid",
}

APPLY_FORK_TO_RAILS = {
    "id": "id",                              # UUID ↔ bigint
    "candidate_id": "candidate_id",
    "job_id": "job_id",
    "stage_id": "selective_process_id",
    "is_active": "is_deleted",               # Inverted logic
    # --- Rails-only ---
    # (simple model — only 5 fields)
    # --- Fork-only ---
    # screening_score, interview_report, lia_recommendation,
    # status (more granular than Rails selective_process)
}

# Selective Process mapping (Rails pipeline stages)
SELECTIVE_PROCESS_FORK_TO_RAILS = {
    "id": "id",
    "name": "name",
    "position": "position",                  # Order in pipeline
    "job_id": "job_id",
    "status": "status",                      # Rails: integer enum (0-4)
    "sub_stages": "sub_status",              # Rails: JSONB
    # Fork equivalent: recruitment_stages table
    # Fork-only: automation rules, SLA tracking, sub_statuses with richer schema
}

# User mapping
USER_FORK_TO_RAILS = {
    "id": "id",                              # UUID ↔ bigint
    "email": "email",
    # Rails also has: password_digest, account_id
    # Fork also has: name, role, company_id, is_active, WorkOS fields
}

# Message mapping
MESSAGE_FORK_TO_RAILS = {
    # Fork has 3 message systems: conversations, whatsapp_conversations, teams_conversations
    # Rails has 1: messages (with JSONB metadata)
    "id": "id",
    "content": "content",
    "company_id": "account_id",
    # Rails: entity (enum), status (enum), parent_message_id, reference_type, reference_id, metadata
    # Fork: channel-specific fields, state machine, threading
}


def rails_candidate_to_fork(data: dict) -> dict:
    """Convert Rails candidate JSON to fork format (complete mapping)."""
    if not data:
        return {}
    rails_int_id = data.get("id")
    result = {
        # IDs — `id` must be a string for FastAPI response contracts
        "id": str(rails_int_id) if rails_int_id is not None else "",
        "rails_id": rails_int_id,
        "_source": "rails",
        # Basic
        "name": data.get("name", ""),
        "surname": data.get("surname", ""),
        "full_name": f"{data.get('name', '')} {data.get('surname', '')}".strip(),
        "email": data.get("email", ""),
        "secondary_email": data.get("secondary_email"),
        "phone": data.get("phone"),
        "mobile_phone": data.get("mobile_phone"),
        "secondary_phone": data.get("secondary_phone"),
        "linkedin_url": data.get("linkedin"),
        "github_url": data.get("github"),
        "portfolio_url": data.get("portfolio"),
        "avatar_url": data.get("avatar_url"),
        # Personal
        "date_of_birth": data.get("date_birth"),
        "gender": data.get("gender"),
        "nationality": data.get("nationality"),
        "marital_status": data.get("marital_status"),
        "cpf": data.get("cpf"),
        # Professional
        "current_title": data.get("role_name"),
        "current_company": data.get("current_company"),
        "seniority_level": data.get("position_level"),
        "self_introduction": data.get("self_introduction"),
        "resume_text": data.get("curriculum_text"),
        "resume_url": data.get("curriculum_pdf_url"),
        # Location
        "location_city": data.get("city"),
        "location_state": data.get("state"),
        "location_country": data.get("country"),
        "address_street": data.get("street"),
        "address_number": str(data.get("number", "")) if data.get("number") else None,
        "address_district": data.get("district"),
        "address_zip": data.get("zip"),
        "address_complement": data.get("complement"),
        # Salary
        "current_salary": data.get("current_salary"),
        "desired_salary_min": data.get("desired_salary"),
        "salary_expectation_clt": data.get("clt_expectation"),
        "salary_expectation_pj": data.get("pj_expectation"),
        "salary_expectation_freelance": data.get("freelance_expectation"),
        "salary_currency": data.get("currency", "BRL"),
        # Preferences
        "is_remote": data.get("remote_work"),
        "willing_to_relocate": data.get("mobility"),
        # Meta
        "source": data.get("source"),
        # Rails-only (preserved)
        "uid": data.get("uid"),
        "completed_register": data.get("completed_register"),
        "accept_terms": data.get("accept_terms"),
        "interests": data.get("interests"),
        "comments": data.get("comments"),
    }
    return {k: v for k, v in result.items() if v is not None}


def rails_job_to_fork(data: dict) -> dict:
    """Convert Rails job JSON to fork format.

    `id` is always a string so FastAPI response models (id: str) validate correctly.
    `rails_id` retains the original integer from Rails for reference.
    Visibility/auth fields (visibility, created_by, recruiter_email, access_list) are
    mapped so that defense-in-depth confidentiality checks in endpoints work correctly.
    """
    if not data:
        return {}
    rails_int_id = data.get("id")
    return {
        # `id` required by FastAPI response contracts (JobVacancyDetailResponse, JobVacancyListItemResponse)
        "id": str(rails_int_id) if rails_int_id is not None else "",
        "rails_id": rails_int_id,
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "location": f"{data.get('city', '')}, {data.get('state', '')}".strip(", "),
        "work_model": "remoto" if data.get("is_remote") else data.get("workplace_type", "presencial"),
        "status": "Ativa" if data.get("status") else "Rascunho",
        "_source": "rails",
        # Visibility / authorization fields — required for defense-in-depth confidentiality checks
        "visibility": data.get("visibility", "public"),
        "is_confidential": data.get("is_confidential", False),
        "created_by": data.get("created_by"),
        "recruiter_email": data.get("recruiter_email"),
        "access_list": data.get("access_list") or [],
        # Rails-only
        "provider": data.get("provider"),
        "provider_job_id": data.get("provider_job_id"),
        "application_deadline": data.get("application_deadline"),
    }


def rails_apply_to_fork(data: dict) -> dict:
    """Convert Rails apply JSON to fork format."""
    if not data:
        return {}
    rails_int_id = data.get("id")
    return {
        "id": str(rails_int_id) if rails_int_id is not None else "",
        "rails_id": rails_int_id,
        "candidate_id": data.get("candidate_id"),
        "job_id": data.get("job_id"),
        "stage_id": data.get("selective_process_id"),
        "is_active": not data.get("is_deleted", False),
    }


def rails_selective_process_to_fork(data: dict) -> dict:
    """Convert Rails selective_process JSON to fork format."""
    if not data:
        return {}
    rails_int_id = data.get("id")
    return {
        "id": str(rails_int_id) if rails_int_id is not None else "",
        "rails_id": rails_int_id,
        "name": data.get("name", ""),
        "position": data.get("position"),
        "job_id": data.get("job_id"),
        "status": data.get("status"),
        "sub_stages": data.get("sub_status"),
    }


def rails_message_to_fork(data: dict) -> dict:
    """Convert Rails message JSON to fork format."""
    if not data:
        return {}
    rails_int_id = data.get("id")
    return {
        "id": str(rails_int_id) if rails_int_id is not None else "",
        "rails_id": rails_int_id,
        "content": data.get("content", ""),
        "entity": data.get("entity"),
        "status": data.get("status"),
        "parent_message_id": data.get("parent_message_id"),
        "reference_type": data.get("reference_type"),
        "reference_id": data.get("reference_id"),
        "metadata": data.get("metadata"),
        "account_id": data.get("account_id"),
    }


# ----------------------------------------------------------------
# RailsAdapter — Unified data source
# ----------------------------------------------------------------

class RailsAdapter:
    """
    Unified data access: Rails first, local DB fallback.

    When RAILS_API_URL is configured:
      get_candidate(id) → calls Rails (via circuit-breaker-protected HTTP) → maps to fork format
      If Rails fails → falls back to local DB

    When RAILS_API_URL is NOT configured:
      get_candidate(id) → uses local DB directly (current behavior)

    Auth:
      User JWT is forwarded when available (rails_token arg).
      Falls back to RAILS_API_TOKEN service-to-service token automatically
      (handled in WeDOTalentATSClient constructor).
    """

    def __init__(
        self,
        db: AsyncSession | None = None,
        rails_token: str | None = None,
    ):
        self.db = db
        self._rails_client = None
        self._rails_token = rails_token or RAILS_API_TOKEN or None

    async def _get_rails_client(self):
        if self._rails_client is None and RAILS_ENABLED:
            from app.shared.integration.rails_client import WeDOTalentATSClient  # W2-010-B canonical
            self._rails_client = WeDOTalentATSClient(token=self._rails_token)
        return self._rails_client

    # ---- Auth / Session ----

    async def login(self, email: str, password: str) -> str | None:
        """Authenticate with Rails and get JWT. Returns token or None."""
        client = await self._get_rails_client()
        if client:
            try:
                token = await client.login(email, password)
                if token:
                    self._rails_token = token
                    self._rails_client = None
                    return token
            except Exception as e:
                logger.warning("[RailsAdapter] login failed: %s", e)
        return None

    async def get_current_user(self) -> dict | None:
        """Get current authenticated user profile from Rails (/v1/me)."""
        client = await self._get_rails_client()
        if client:
            try:
                return await client.get_current_user()
            except Exception as e:
                logger.warning("[RailsAdapter] get_current_user failed: %s", e)
        return None

    # ---- Event Publishing (UUID-safe) ----

    async def publish_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str | None = None,
        data: dict | None = None,
    ) -> bool:
        """Publish an event to Rails via /v1/events webhook endpoint.
        
        Unlike CRUD methods, this accepts UUID entity IDs and lets Rails
        handle ID mapping on its side. Returns True if accepted, False otherwise.
        """
        client = await self._get_rails_client()
        if not client:
            return False
        try:
            payload = {
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "data": data or {},
                "source": "lia_agent_system",
            }
            resp = await client._request("POST", "/v1/events", json_body=payload, retry=1)
            if resp.success:
                logger.info("[RailsAdapter] Event published: %s/%s id=%s", event_type, entity_type, entity_id)
                return True
            logger.warning("[RailsAdapter] Event publish returned %s for %s/%s", resp.status_code, event_type, entity_type)
            return False
        except Exception as e:
            logger.warning("[RailsAdapter] Event publish failed for %s/%s: %s", event_type, entity_type, e)
            return False

    # ---- Candidates ----

    @staticmethod
    def _to_rails_id(id_str: str) -> int | None:
        """Convert a string ID to Rails integer ID. Returns None if not a valid integer."""
        if id_str and id_str.isdigit():
            return int(id_str)
        return None

    @staticmethod
    def _looks_like_uuid(id_str: str) -> bool:
        """Return True if the string is shaped like a UUID (not a bigint).

        Used by the fork_uuid lookup path (MIGRATION_PLAN item 7.3). A UUID
        has exactly 36 chars with dashes at positions 8/13/18/23. We don't
        try to parse it rigorously — we just want to distinguish fork UUIDs
        from Rails bigint IDs.
        """
        if not id_str or len(id_str) != 36:
            return False
        return id_str[8] == "-" and id_str[13] == "-" and id_str[18] == "-" and id_str[23] == "-"

    async def _resolve_rails_candidate_id(self, candidate_id: str) -> int | None:
        """Resolve a candidate ID (bigint or fork UUID) to a Rails bigint ID.

        MIGRATION_PLAN item 7.3 — Rails now carries `candidates.fork_uuid`
        (added in migration 20260415120003). When the caller hands us a
        UUID instead of a bigint, we look it up on Rails via
        `GET /v1/candidates?fork_uuid=<uuid>` and return the discovered
        integer id. Result is cached per-request (via the client session)
        so subsequent operations on the same candidate reuse it.

        Returns:
            The Rails bigint id if resolvable; None if the candidate has
            no fork_uuid yet on Rails (e.g. before backfill completes)
            or if Rails is unavailable.
        """
        # Bigint path — no translation needed
        direct = self._to_rails_id(candidate_id)
        if direct is not None:
            return direct

        # UUID path — requires a Rails round-trip
        if not self._looks_like_uuid(candidate_id):
            return None

        client = await self._get_rails_client()
        if not client:
            return None

        lookup = getattr(client, "find_candidate_by_fork_uuid", None)
        if not callable(lookup):
            logger.debug(
                "[RailsAdapter] Rails client has no find_candidate_by_fork_uuid — "
                "falling back to None for UUID %s",
                candidate_id,
            )
            return None

        try:
            data = await lookup(candidate_id)
        except Exception as exc:
            logger.warning(
                "[RailsAdapter] fork_uuid lookup failed for %s: %s", candidate_id, exc
            )
            return None

        if not data:
            return None
        rails_id = data.get("id") if isinstance(data, dict) else None
        if isinstance(rails_id, int):
            return rails_id
        if isinstance(rails_id, str) and rails_id.isdigit():
            return int(rails_id)
        return None

    async def _resolve_rails_job_id(self, job_id: str) -> int | None:
        """Resolve a job ID (bigint or fork UUID) to a Rails bigint ID.

        Onda 2.1 fix (2026-05-23): espelho de ``_resolve_rails_candidate_id``
        pra jobs. Sumiu no merge incident (W2-009 dual-ID idempotency broken
        em camada Rails). Sem isso, retries com UUID vs bigint hashavam pra
        keys diferentes → operação dupla em produção (ADR 003 violation).

        Lookup via ``GET /v1/jobs?fork_uuid=<uuid>`` em Rails. Cached per-
        request via client session.

        Returns:
            Rails bigint id se resolvível; None se job sem fork_uuid em Rails
            (pre-backfill) ou se Rails indisponível.
        """
        direct = self._to_rails_id(job_id)
        if direct is not None:
            return direct

        if not self._looks_like_uuid(job_id):
            return None

        client = await self._get_rails_client()
        if not client:
            return None

        lookup = getattr(client, "find_job_by_fork_uuid", None)
        if not callable(lookup):
            logger.debug(
                "[RailsAdapter] Rails client has no find_job_by_fork_uuid — "
                "falling back to None for UUID %s",
                job_id,
            )
            return None

        try:
            data = await lookup(job_id)
        except Exception as exc:
            logger.warning(
                "[RailsAdapter] job fork_uuid lookup failed for %s: %s", job_id, exc
            )
            return None

        if not data:
            return None
        rails_id = data.get("id") if isinstance(data, dict) else None
        if isinstance(rails_id, int):
            return rails_id
        if isinstance(rails_id, str) and rails_id.isdigit():
            return int(rails_id)
        return None

    async def _resolve_rails_application_id(self, application_id: str) -> int | None:
        """Resolve an application (apply) ID (bigint or fork UUID) to Rails bigint.

        Onda 2.1 fix (2026-05-23): terceiro espelho — junto com candidate
        e job resolvers, completa o canonical dual-ID pattern.

        Lookup via ``GET /v1/applications?fork_uuid=<uuid>`` em Rails.

        Returns:
            Rails bigint id se resolvível; None se application sem fork_uuid
            em Rails ou se Rails indisponível.
        """
        direct = self._to_rails_id(application_id)
        if direct is not None:
            return direct

        if not self._looks_like_uuid(application_id):
            return None

        client = await self._get_rails_client()
        if not client:
            return None

        lookup = getattr(client, "find_application_by_fork_uuid", None)
        if not callable(lookup):
            logger.debug(
                "[RailsAdapter] Rails client has no find_application_by_fork_uuid — "
                "falling back to None for UUID %s",
                application_id,
            )
            return None

        try:
            data = await lookup(application_id)
        except Exception as exc:
            logger.warning(
                "[RailsAdapter] application fork_uuid lookup failed for %s: %s",
                application_id, exc,
            )
            return None

        if not data:
            return None
        rails_id = data.get("id") if isinstance(data, dict) else None
        if isinstance(rails_id, int):
            return rails_id
        if isinstance(rails_id, str) and rails_id.isdigit():
            return int(rails_id)
        return None

    async def get_candidate_from_rails_only(self, candidate_id: str) -> dict | None:
        """Fetch candidate from Rails only — no local DB fallback.

        Raises if Rails is unavailable so the caller's (endpoint) own fallback logic runs.
        Returns None if Rails returns nothing (e.g. 404), does not raise.
        """
        client = await self._get_rails_client()
        if not client:
            return None
        rails_id = self._to_rails_id(candidate_id)
        if rails_id is None:
            logger.debug("[RailsAdapter] get_candidate_from_rails_only: non-integer ID %r — skipping", candidate_id)
            return None
        data = await client.get_candidate(rails_id)
        if data:
            return rails_candidate_to_fork(data)
        return None

    async def list_candidates_from_rails_only(
        self,
        search: str = "*",
        page: int = 1,
        limit: int = 30,
        status: str | None = None,
        source: str | None = None,
        seniority: str | None = None,
    ) -> list[dict] | None:
        """Fetch candidates from Rails only — no local DB fallback.

        Returns None when Rails is unavailable, returns non-success (401/5xx/circuit-open),
        or the client itself is not configured. The caller should fall back to local repo.
        Returns an empty list [] only when Rails explicitly responded with zero records.
        """
        client = await self._get_rails_client()
        if not client:
            return None
        filters: dict = {}
        if status:
            filters["status"] = status
        if source:
            filters["source"] = source
        if seniority:
            filters["position_level"] = seniority
        try:
            # list_candidates_or_none returns None on non-success, [] on empty success
            results = await client.list_candidates_or_none(
                search=search, page=page, limit=limit, **filters
            )
        except Exception:
            return None
        if results is None:
            return None
        return [rails_candidate_to_fork(r) for r in results]

    async def get_candidate(self, candidate_id: str) -> dict | None:
        """Get candidate: Rails first, local DB fallback."""
        client = await self._get_rails_client()
        if client:
            rails_id = self._to_rails_id(candidate_id)
            if rails_id is not None:
                try:
                    data = await client.get_candidate(rails_id)
                    if data:
                        logger.debug("[RailsAdapter] Candidate %s from Rails", candidate_id)
                        return rails_candidate_to_fork(data)
                except Exception as e:
                    logger.warning("[RailsAdapter] Rails failed for candidate %s: %s", candidate_id, e)

        if self.db:
            try:
                from app.domains.candidates.repositories.candidate_repository import (
                    CandidateRepository,
                )
                candidate_repo = CandidateRepository(self.db)
                candidate = await candidate_repo.get_by_id_str(candidate_id)
                if candidate:
                    logger.debug("[RailsAdapter] Candidate %s from local DB", candidate_id)
                    return {"source": "local", "id": str(candidate.id), "email": candidate.email}
            except Exception as e:
                logger.warning("[RailsAdapter] Local DB failed for candidate %s: %s", candidate_id, e)

        return None

    async def list_candidates(
        self, search: str = "*", page: int = 1, limit: int = 30
    ) -> list[dict]:
        """List candidates: Rails first, local DB fallback."""
        client = await self._get_rails_client()
        if client:
            try:
                results = await client.list_candidates(search=search, page=page, limit=limit)
                if results:
                    return [rails_candidate_to_fork(r) for r in results]
            except Exception as e:
                logger.warning("[RailsAdapter] Rails list_candidates failed: %s", e)

        if self.db:
            try:
                from app.domains.candidates.repositories.candidate_repository import (
                    CandidateRepository,
                )
                candidate_repo = CandidateRepository(self.db)
                candidates = await candidate_repo.list_paginated_no_tenant(
                    limit=limit, offset=(page - 1) * limit
                )
                return [{"source": "local", "id": str(c.id)} for c in candidates]
            except Exception:
                pass

        return []

    async def create_candidate(self, candidate_data: dict) -> dict | None:
        """Create candidate: Rails first, local DB fallback."""
        rails_data = {}
        for fork_field, rails_field in CANDIDATE_FORK_TO_RAILS.items():
            if fork_field in candidate_data and rails_field != "id":
                rails_data[rails_field] = candidate_data[fork_field]

        client = await self._get_rails_client()
        if client:
            try:
                result = await client.create_candidate(rails_data)
                if result:
                    logger.info("[RailsAdapter] Candidate created in Rails: %s", result.get("id"))
                    return rails_candidate_to_fork(result)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails create_candidate failed: %s", e)

        if self.db:
            try:
                from lia_models.candidate import Candidate
                candidate = Candidate(**candidate_data)
                self.db.add(candidate)
                await self.db.commit()
                await self.db.refresh(candidate)
                return {"source": "local", "id": str(candidate.id)}
            except Exception as e:
                logger.warning("[RailsAdapter] Local create_candidate failed: %s", e)
                await self.db.rollback()

        return None

    async def update_candidate(self, candidate_id: str, candidate_data: dict) -> dict | None:
        """Update candidate: Rails first, local DB fallback."""
        rails_data = {}
        for fork_field, rails_field in CANDIDATE_FORK_TO_RAILS.items():
            if fork_field in candidate_data and rails_field != "id":
                rails_data[rails_field] = candidate_data[fork_field]

        client = await self._get_rails_client()
        if client:
            rails_id = self._to_rails_id(candidate_id)
            if rails_id is None:
                logger.warning("[RailsAdapter] update_candidate: non-integer ID %r — skipping Rails", candidate_id)
                return None
            try:
                result = await client.update_candidate(rails_id, rails_data)
                if result:
                    return rails_candidate_to_fork(result)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails update_candidate failed: %s", e)

        return None

    async def delete_candidate(self, candidate_id: str) -> bool:
        """Delete candidate from Rails."""
        client = await self._get_rails_client()
        if client:
            rails_id = self._to_rails_id(candidate_id)
            if rails_id is None:
                logger.warning("[RailsAdapter] delete_candidate: non-integer ID %r — skipping Rails", candidate_id)
                return False
            try:
                return await client.delete_candidate(rails_id)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails delete_candidate failed: %s", e)
        return False

    # ---- Jobs ----

    async def get_job_from_rails_only(self, job_id: str) -> dict | None:
        """Fetch job from Rails only — no local DB fallback.

        Returns None if Rails is unavailable or ID is not a valid integer.
        Does not raise so callers can run their own fallback without try/except.
        """
        client = await self._get_rails_client()
        if not client:
            return None
        rails_id = self._to_rails_id(job_id)
        if rails_id is None:
            logger.debug("[RailsAdapter] get_job_from_rails_only: non-integer ID %r — skipping", job_id)
            return None
        try:
            data = await client.get_job(rails_id)
        except Exception:
            return None
        if data:
            return rails_job_to_fork(data)
        return None

    async def list_jobs_from_rails_only(
        self,
        search: str = "*",
        page: int = 1,
        limit: int = 30,
        status: str | None = None,
        visibility: str | None = None,
    ) -> list[dict] | None:
        """Fetch jobs from Rails only — no local DB fallback.

        Returns None when Rails is unavailable, returns non-success (401/5xx/circuit-open),
        or the client itself is not configured. The caller should fall back to local repo.
        Returns an empty list [] only when Rails explicitly responded with zero records.
        """
        client = await self._get_rails_client()
        if not client:
            return None
        filters: dict = {}
        if status:
            filters["status"] = status
        if visibility:
            filters["visibility"] = visibility
        try:
            # list_jobs_or_none returns None on non-success, [] on empty success
            results = await client.list_jobs_or_none(
                search=search, page=page, limit=limit, **filters
            )
        except Exception:
            return None
        if results is None:
            return None
        return [rails_job_to_fork(r) for r in results]

    async def get_job(self, job_id: str) -> dict | None:
        """Get job: Rails first, local DB fallback."""
        client = await self._get_rails_client()
        if client:
            rails_id = self._to_rails_id(job_id)
            if rails_id is not None:
                try:
                    data = await client.get_job(rails_id)
                    if data:
                        return rails_job_to_fork(data)
                except Exception as e:
                    logger.warning("[RailsAdapter] Rails failed for job %s: %s", job_id, e)

        if self.db:
            try:
                from app.domains.job_management.repositories.job_vacancy_crud_repository import (
                    JobVacancyCRUDRepository,
                )
                job_repo = JobVacancyCRUDRepository(self.db)
                job = await job_repo.get_vacancy_by_id(job_id)
                if job:
                    return {"source": "local", "id": str(job.id), "title": job.title}
            except Exception:
                pass

        return None

    async def list_jobs(
        self, search: str = "*", page: int = 1, limit: int = 30
    ) -> list[dict]:
        """List jobs: Rails first, local DB fallback."""
        client = await self._get_rails_client()
        if client:
            try:
                results = await client.list_jobs(search=search, page=page, limit=limit)
                if results:
                    return [rails_job_to_fork(r) for r in results]
            except Exception as e:
                logger.warning("[RailsAdapter] Rails list_jobs failed: %s", e)

        if self.db:
            try:
                from app.domains.job_management.repositories.job_vacancy_crud_repository import (
                    JobVacancyCRUDRepository,
                )
                job_repo = JobVacancyCRUDRepository(self.db)
                jobs = await job_repo.list_paginated_no_tenant(
                    limit=limit, offset=(page - 1) * limit
                )
                return [{"source": "local", "id": str(j.id), "title": j.title}
                        for j in jobs]
            except Exception:
                pass

        return []

    async def create_job(self, job_data: dict) -> dict | None:
        """Create job: Rails first, local DB fallback."""
        rails_data = {}
        for fork_field, rails_field in JOB_FORK_TO_RAILS.items():
            if fork_field in job_data and rails_field != "id":
                rails_data[rails_field] = job_data[fork_field]

        client = await self._get_rails_client()
        if client:
            try:
                result = await client.create_job(rails_data)
                if result:
                    logger.info("[RailsAdapter] Job created in Rails: %s", result.get("id"))
                    return rails_job_to_fork(result)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails create_job failed: %s", e)

        if self.db:
            try:
                from lia_models.job_vacancy import JobVacancy
                job = JobVacancy(**job_data)
                self.db.add(job)
                await self.db.commit()
                await self.db.refresh(job)
                return {"source": "local", "id": str(job.id), "title": job.title}
            except Exception as e:
                logger.warning("[RailsAdapter] Local create_job failed: %s", e)
                await self.db.rollback()

        return None

    async def update_job(self, job_id: str, job_data: dict) -> dict | None:
        """Update job: Rails first, local DB fallback.

        Onda 2.1: usa _resolve_rails_job_id pra canonicalizar UUID → bigint
        (W2-009 dual-ID idempotency).
        """
        rails_data = {}
        for fork_field, rails_field in JOB_FORK_TO_RAILS.items():
            if fork_field in job_data and rails_field != "id":
                rails_data[rails_field] = job_data[fork_field]

        client = await self._get_rails_client()
        if client:
            rails_id = await self._resolve_rails_job_id(job_id)
            if rails_id is None:
                logger.warning("[RailsAdapter] update_job: unresolvable ID %r — skipping Rails", job_id)
                return None
            try:
                result = await client.update_job(rails_id, rails_data)
                if result:
                    return rails_job_to_fork(result)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails update_job failed: %s", e)

        return None

    async def delete_job(self, job_id: str) -> bool:
        """Delete job from Rails (Onda 2.1: dual-ID resolve)."""
        client = await self._get_rails_client()
        if client:
            rails_id = await self._resolve_rails_job_id(job_id)
            if rails_id is None:
                logger.warning("[RailsAdapter] delete_job: unresolvable ID %r — skipping Rails", job_id)
                return False
            try:
                return await client.delete_job(rails_id)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails delete_job failed: %s", e)
        return False

    # ---- Applies ----

    async def list_applies(
        self, search: str = "*", page: int = 1, limit: int = 30
    ) -> list[dict]:
        """List applies: Rails first, local DB fallback."""
        client = await self._get_rails_client()
        if client:
            try:
                results = await client.list_applies(search=search, page=page, limit=limit)
                if results:
                    return [rails_apply_to_fork(r) for r in results]
            except Exception as e:
                logger.warning("[RailsAdapter] Rails list_applies failed: %s", e)
        return []

    async def get_apply(self, apply_id: str) -> dict | None:
        """Get a single apply from Rails (Onda 2.1: dual-ID resolve)."""
        client = await self._get_rails_client()
        if client:
            rails_id = await self._resolve_rails_application_id(apply_id)
            if rails_id is None:
                logger.warning("[RailsAdapter] get_apply: unresolvable ID %r — skipping Rails", apply_id)
                return None
            try:
                data = await client.get_apply(rails_id)
                if data:
                    return rails_apply_to_fork(data)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails get_apply failed: %s", e)
        return None

    async def create_apply(self, candidate_id: str, job_id: str) -> dict | None:
        """Create an apply in Rails (Onda 2.1: dual-ID resolve for both IDs)."""
        client = await self._get_rails_client()
        if client:
            cand_rails_id = await self._resolve_rails_candidate_id(candidate_id)
            job_rails_id = await self._resolve_rails_job_id(job_id)
            if cand_rails_id is None or job_rails_id is None:
                logger.warning(
                    "[RailsAdapter] create_apply: unresolvable IDs candidate=%r job=%r — skipping Rails",
                    candidate_id, job_id,
                )
                return None
            try:
                data = await client.create_apply(cand_rails_id, job_rails_id)
                if data:
                    return rails_apply_to_fork(data)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails create_apply failed: %s", e)
        return None

    async def update_apply(self, apply_id: str, apply_data: dict) -> dict | None:
        """Update an apply in Rails (Onda 2.1: dual-ID resolve)."""
        client = await self._get_rails_client()
        if client:
            rails_id = await self._resolve_rails_application_id(apply_id)
            if rails_id is None:
                logger.warning("[RailsAdapter] update_apply: unresolvable ID %r — skipping Rails", apply_id)
                return None
            try:
                data = await client.update_apply(rails_id, apply_data)
                if data:
                    return rails_apply_to_fork(data)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails update_apply failed: %s", e)
        return None

    # ---- Selective Processes ----

    async def _resolve_reference_id_by_type(
        self,
        reference_type: str | None,
        reference_id: str | None,
    ) -> int | None:
        """Resolve a reference_id (UUID/bigint) to Rails bigint based on type.

        Onda 2.1 helper (2026-05-23): dispatcher canonical pra reference-
        typed APIs (list_messages, send_message). Mapping:
          - Job/job        → _resolve_rails_job_id
          - Apply/apply    → _resolve_rails_application_id
          - Candidate/candidate → _resolve_rails_candidate_id
          - Outros types   → fallback bigint passthrough (legacy compat)

        Returns:
            Bigint resolvido OU None se reference_id ausente/unresolvable.
        """
        if not reference_id:
            return None

        type_lower = (reference_type or "").lower()
        if type_lower in ("job", "vacancy"):
            return await self._resolve_rails_job_id(reference_id)
        if type_lower in ("apply", "application"):
            return await self._resolve_rails_application_id(reference_id)
        if type_lower == "candidate":
            return await self._resolve_rails_candidate_id(reference_id)

        # Unknown type → legacy bigint passthrough (no fork_uuid lookup)
        return self._to_rails_id(reference_id)

    async def list_selective_processes(
        self, job_id: str | None = None
    ) -> list[dict]:
        """List selective processes (pipeline stages) from Rails.

        Onda 2.1: resolve job_id UUID → bigint antes do call Rails.
        Unresolvable UUID retorna [] sem chamar Rails.
        """
        client = await self._get_rails_client()
        if client:
            try:
                job_id_int: int | None = None
                if job_id is not None:
                    job_id_int = await self._resolve_rails_job_id(job_id)
                    # UUID unresolvable → return early sem chamar Rails
                    if job_id_int is None and self._looks_like_uuid(job_id):
                        return []
                results = await client.list_selective_processes(job_id=job_id_int)
                if results:
                    return [rails_selective_process_to_fork(r) for r in results]
            except Exception as e:
                logger.warning("[RailsAdapter] Rails list_selective_processes failed: %s", e)
        return []

    # ---- Messages ----

    async def list_messages(
        self,
        page: int = 1,
        limit: int = 30,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> list[dict]:
        """List messages from Rails (Onda 2.1: type-based dual-ID resolve)."""
        client = await self._get_rails_client()
        if client:
            try:
                ref_id_int = await self._resolve_reference_id_by_type(
                    reference_type, reference_id
                )
                results = await client.list_messages(
                    page=page,
                    limit=limit,
                    reference_type=reference_type,
                    reference_id=ref_id_int,
                )
                if results:
                    return [rails_message_to_fork(r) for r in results]
            except Exception as e:
                logger.warning("[RailsAdapter] Rails list_messages failed: %s", e)
        return []

    async def send_message(
        self,
        content: str,
        entity: str | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
        parent_message_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict | None:
        """Send a message via Rails (Onda 2.1: type-based dual-ID resolve)."""
        client = await self._get_rails_client()
        if client:
            try:
                ref_id_int = await self._resolve_reference_id_by_type(
                    reference_type, reference_id
                )
                parent_id_int = int(parent_message_id) if parent_message_id and parent_message_id.isdigit() else None
                result = await client.send_message(
                    content=content,
                    entity=entity,
                    reference_type=reference_type,
                    reference_id=ref_id_int,
                    parent_message_id=parent_id_int,
                    metadata=metadata,
                )
                if result:
                    return rails_message_to_fork(result)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails send_message failed: %s", e)
        return None

    # ---- Health ----

    async def health_check(self) -> dict:
        """Check Rails API connectivity and return status dict."""
        from app.shared.resilience.circuit_breaker import RAILS_CIRCUIT
        circuit_stats = RAILS_CIRCUIT.get_stats()

        client = await self._get_rails_client()
        if not client:
            return {
                "rails_enabled": False,
                "status": "disabled",
                "message": "RAILS_API_URL not configured",
                "circuit_breaker": circuit_stats,
            }

        probe = await client.health_check()
        probe["rails_enabled"] = True
        probe["circuit_breaker"] = circuit_stats
        return probe

    # ---- Cleanup ----

    async def close(self):
        if self._rails_client:
            await self._rails_client.close()

    # ---- Bias Audit (UC-P0-13) ----
    # TODO(UC-P0-13): Rails has bias_audit_reports table (migration 20250716000039)
    # but no API endpoints yet. Once GET /api/v1/bias_audits/job/:job_id is live
    # in ats-api, replace Python delegates below with Rails HTTP calls.
    # Deadline: 2026-07-16 (same as @remove-after on the deprecated service).

    async def get_adverse_impact_by_job(
        self,
        db,
        job_id,
        company_id=None,
    ):
        """Returns adverse impact report for a job.

        Delegates to Python BiasAuditService until Rails GET /api/v1/bias_audits/job/:job_id
        is implemented. Multi-tenant: company_id validated by caller endpoint via JWT.
        LGPD-safe: only aggregate stats returned, no PII.
        """
        from app.shared.services.bias_audit_service import bias_audit_service as _svc
        return await _svc.get_adverse_impact_by_job(db, job_id, company_id=company_id)

    async def get_bias_audit_snapshot_history(
        self,
        db,
        company_id,
        job_id: str,
        limit: int = 10,
    ):
        """Returns historical bias audit snapshots for a job, newest-first.

        Delegates to Python BiasAuditService until Rails endpoint is live.
        Multi-tenant isolation enforced via company_id filter.
        """
        from app.shared.services.bias_audit_service import bias_audit_service as _svc
        return await _svc.get_snapshot_history(db, company_id, job_id, limit)

    def audit_ranking_results(
        self,
        results: list,
        dimension: str = "gender",
        top_n: int = 10,
        company_id=None,
    ) -> dict:
        """FAR-5: Real-time disparate impact audit on a ranked candidate list.

        Delegates to Python BiasAuditService (sync, no DB needed).
        Applies Four-Fifths Rule to top-N results.
        Returns dict with fairness_ok, group_counts, adverse_impact_ratios, flagged_groups.
        """
        from app.shared.services.bias_audit_service import bias_audit_service as _svc
        return _svc.audit_ranking_results(
            results, dimension=dimension, top_n=top_n, company_id=company_id
        )

