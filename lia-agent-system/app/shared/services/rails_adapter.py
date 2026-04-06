"""
Rails Adapter — Field mapping and data source abstraction.

Maps between fork models (UUID, 275 tables) and Rails models (bigint, 12 tables).
Provides a unified interface: tries Rails first, falls back to local DB.

Usage:
    from app.services.rails_adapter import RailsAdapter
    adapter = RailsAdapter(db_session, rails_token)
    candidate = await adapter.get_candidate(candidate_id)
    jobs = await adapter.list_jobs(search="developer", page=1)
"""
import logging
import os

from sqlalchemy import Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Whether to try Rails first (set RAILS_API_URL to enable)
RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL"))


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
    result = {
        # IDs
        "rails_id": data.get("id"),
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
    """Convert Rails job JSON to fork format."""
    if not data:
        return {}
    return {
        "rails_id": data.get("id"),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "location": f"{data.get('city', '')}, {data.get('state', '')}".strip(", "),
        "work_model": "remoto" if data.get("is_remote") else data.get("workplace_type", "presencial"),
        "status": "Ativa" if data.get("status") else "Rascunho",
        # Rails-only
        "provider": data.get("provider"),
        "provider_job_id": data.get("provider_job_id"),
        "application_deadline": data.get("application_deadline"),
    }


def rails_apply_to_fork(data: dict) -> dict:
    """Convert Rails apply JSON to fork format."""
    if not data:
        return {}
    return {
        "rails_id": data.get("id"),
        "candidate_id": data.get("candidate_id"),
        "job_id": data.get("job_id"),
        "stage_id": data.get("selective_process_id"),
        "is_active": not data.get("is_deleted", False),
    }


# ----------------------------------------------------------------
# RailsAdapter — Unified data source
# ----------------------------------------------------------------

class RailsAdapter:
    """
    Unified data access: Rails first, local DB fallback.

    When RAILS_API_URL is configured:
      get_candidate(id) → calls Rails → maps to fork format
      If Rails fails → falls back to local DB

    When RAILS_API_URL is NOT configured:
      get_candidate(id) → uses local DB directly (current behavior)
    """

    def __init__(
        self,
        db: AsyncSession | None = None,
        rails_token: str | None = None,
    ):
        self.db = db
        self._rails_client = None
        self._rails_token = rails_token

    async def _get_rails_client(self):
        if self._rails_client is None and RAILS_ENABLED:
            from app.services.ats_clients.wedotalent_rails import WeDOTalentATSClient
            self._rails_client = WeDOTalentATSClient(token=self._rails_token)
        return self._rails_client

    # ---- Candidates ----

    async def get_candidate(self, candidate_id: str) -> dict | None:
        """Get candidate: Rails first, local DB fallback."""
        # Try Rails
        client = await self._get_rails_client()
        if client:
            try:
                data = await client.get_candidate(int(candidate_id) if candidate_id.isdigit() else 0)
                if data:
                    logger.debug("[RailsAdapter] Candidate %s from Rails", candidate_id)
                    return rails_candidate_to_fork(data)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails failed for candidate %s: %s", candidate_id, e)

        # Fallback: local DB
        if self.db:
            try:
                from libs.models.lia_models.candidate import Candidate
                result = await self.db.execute(
                    select(Candidate).where(Candidate.id == candidate_id)
                )
                candidate = result.scalar_one_or_none()
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

        # Fallback: local DB
        if self.db:
            try:
                from libs.models.lia_models.candidate import Candidate
                result = await self.db.execute(
                    select(Candidate).limit(limit).offset((page - 1) * limit)
                )
                return [{"source": "local", "id": str(c.id)} for c in result.scalars().all()]
            except Exception:
                pass

        return []

    # ---- Jobs ----

    async def get_job(self, job_id: str) -> dict | None:
        """Get job: Rails first, local DB fallback."""
        client = await self._get_rails_client()
        if client:
            try:
                data = await client.get_job(int(job_id) if job_id.isdigit() else 0)
                if data:
                    return rails_job_to_fork(data)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails failed for job %s: %s", job_id, e)

        if self.db:
            try:
                from libs.models.lia_models.job_vacancy import JobVacancy
                result = await self.db.execute(
                    select(JobVacancy).where(JobVacancy.id == job_id)
                )
                job = result.scalar_one_or_none()
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
                from libs.models.lia_models.job_vacancy import JobVacancy
                result = await self.db.execute(
                    select(JobVacancy).limit(limit).offset((page - 1) * limit)
                )
                return [{"source": "local", "id": str(j.id), "title": j.title}
                        for j in result.scalars().all()]
            except Exception:
                pass

        return []

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


    # ---- Write Operations (Work C) ----

    async def create_candidate(self, candidate_data: dict) -> dict | None:
        """Create candidate: Rails first, local DB fallback."""
        # Map fork fields to Rails fields
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

        # Fallback: local DB
        if self.db:
            try:
                from libs.models.lia_models.candidate import Candidate
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
            try:
                result = await client.update_candidate(int(candidate_id) if candidate_id.isdigit() else 0, rails_data)
                if result:
                    return rails_candidate_to_fork(result)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails update_candidate failed: %s", e)

        return None

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
                from libs.models.lia_models.job_vacancy import JobVacancy
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
        """Update job: Rails first, local DB fallback."""
        rails_data = {}
        for fork_field, rails_field in JOB_FORK_TO_RAILS.items():
            if fork_field in job_data and rails_field != "id":
                rails_data[rails_field] = job_data[fork_field]

        client = await self._get_rails_client()
        if client:
            try:
                result = await client.update_job(int(job_id) if job_id.isdigit() else 0, rails_data)
                if result:
                    return rails_job_to_fork(result)
            except Exception as e:
                logger.warning("[RailsAdapter] Rails update_job failed: %s", e)

        return None

    # ---- Cleanup ----

    async def close(self):
        if self._rails_client:
            await self._rails_client.close()
