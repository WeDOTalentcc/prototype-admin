"""
Candidate models for recruitment platform.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Date, Text, JSON, Boolean, Float, UniqueConstraint, ForeignKey, LargeBinary, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, validates
import uuid

from lia_config.database import Base
from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin


class CandidateExperience(Base):
    """
    Detailed professional experience for a candidate.
    Stores rich company data including industries for sector-based search.
    """
    __tablename__ = "candidate_experiences"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    company_name = Column(String(255), nullable=False, index=True)
    company_linkedin_url = Column(String(500), nullable=True)
    company_domain = Column(String(255), nullable=True)
    
    title = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    duration_years = Column(Float, nullable=True)
    is_current = Column(Boolean, default=False)
    
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    
    industries = Column(ARRAY(String), default=list, index=True)
    company_size = Column(String(50), nullable=True)
    company_size_range = Column(String(50), nullable=True)
    technologies = Column(ARRAY(String), default=list)
    is_startup = Column(Boolean, nullable=True)
    company_founded_year = Column(Integer, nullable=True)
    company_annual_revenue = Column(Float, nullable=True)
    
    funding_stage = Column(String(50), nullable=True, index=True)
    company_tags = Column(ARRAY(String), default=list)
    company_hq_city = Column(String(100), nullable=True)
    company_hq_state = Column(String(100), nullable=True)
    company_hq_country = Column(String(100), nullable=True, index=True)
    
    sequence_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CandidateExperience {self.id} - {self.company_name}: {self.title}>"


class CandidateEducation(Base):
    """Educational background for a candidate."""
    __tablename__ = "candidate_education"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    institution = Column(String(255), nullable=False, index=True)
    degree = Column(String(100), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    is_completed = Column(Boolean, default=True)
    
    description = Column(Text, nullable=True)
    gpa = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    
    institution_city = Column(String(100), nullable=True)
    institution_state = Column(String(100), nullable=True)
    institution_country = Column(String(100), nullable=True, index=True)
    institution_ranking = Column(Integer, nullable=True)
    institution_tier = Column(String(50), nullable=True, index=True)
    
    sequence_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CandidateEducation {self.id} - {self.institution}: {self.degree}>"


class Candidate(EncryptedFieldMixin, Base):
    """
    Represents a candidate in the recruitment system.
    Candidates can come from: ATS (via Merge.dev), manual entry, or Pearch AI global search.

    PII encryption (post-migration 060+111, via EncryptedFieldMixin):
      - Every write to ``email`` sets ``email_encrypted`` (Fernet bytes), ``email_hash``
        (SHA-256 hex), and NULLS the ``email`` plaintext column.
      - Every write to ``cpf`` sets ``cpf_encrypted`` (Fernet bytes) and NULLS ``cpf``.
      - Every write to ``name`` sets ``name_encrypted`` (Fernet bytes) and NULLS ``name``.
        NOTE: name is used in ILIKE queries in _handler_hooks.py and sourcing_actions.py.
        Those queries will only work on pre-migration rows (plaintext) during the transition.
        Post-backfill, name search must use a separate search index (PG trigram / full-text).
        Compliance requirement (LGPD) takes precedence over convenience.
      - Every write to ``phone`` sets ``phone_encrypted`` (Fernet bytes) and NULLS ``phone``.
      - Pre-migration rows retain plaintext until pii.backfill_encrypt_existing runs.
      - Lookups: OR(email_hash == hash, email == plaintext) during transition period.
    """
    __tablename__ = "candidates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    # _pii_encrypt_fields: (raw_attr, enc_attr, hash_attr)
    # raw_attr  = Python attribute of the underlying DB column (nullable=True; NULL for new writes)
    # enc_attr  = Python attribute of the Fernet-encrypted LargeBinary column
    # hash_attr = Python attribute of the SHA-256 hash column (None if no hash needed)
    # Public attribute name is derived by stripping leading "_" and "_raw" suffix:
    #   "_email_raw" → hybrid_property "email"; "_cpf_raw" → hybrid_property "cpf"
    _pii_encrypt_fields = [
        ("_email_raw", "_email_encrypted", "email_hash"),
        ("_cpf_raw",   "_cpf_encrypted",   None),
        # UC-P1-15: name and phone encrypted at rest (migration 111)
        ("_name_raw",  "_name_encrypted",  None),
        ("_phone_raw", "_phone_encrypted", None),
    ]

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic Information
    # UC-P1-15: name is PII — stored encrypted (migration 111).
    # DB column "name" kept for schema compat. New writes always NULL here (encrypted in _name_encrypted).
    # Pre-migration rows retain plaintext until pii.backfill_encrypt_existing completes.
    # Access via hybrid_property "name" registered by EncryptedFieldMixin.
    # WARNING: ILIKE searches on name (see _handler_hooks.py, sourcing_actions.py) will only
    # match pre-migration rows. Post-backfill, use full-text / trigram search index.
    _name_raw = Column("name", String(255), nullable=True, index=True)
    # PII-encrypted name (added by migration 111)
    _name_encrypted = Column("name_encrypted", LargeBinary, nullable=True)
    # Raw DB columns for PII fields — always NULL for new writes (post-migration 060).
    # Pre-migration rows retain plaintext here until pii.backfill_encrypt_existing completes.
    # Access via hybrid_property "email" (registered by EncryptedFieldMixin) which decrypts
    # from _email_encrypted transparently. DB column name kept as "email" for schema compat.
    _email_raw = Column("email", String(255), nullable=True, index=True)
    secondary_email = Column(String(255), nullable=True)
    # PII-encrypted backing columns (added by migration 060)
    _email_encrypted = Column("email_encrypted", LargeBinary, nullable=True)
    email_hash = Column(String(64), nullable=True, index=True)
    # UC-P1-15: phone is PII — stored encrypted (migration 111).
    # DB column "phone" kept for schema compat. New writes always NULL here.
    # Access via hybrid_property "phone" registered by EncryptedFieldMixin.
    _phone_raw = Column("phone", String(50), nullable=True)
    # PII-encrypted phone (added by migration 111)
    _phone_encrypted = Column("phone_encrypted", LargeBinary, nullable=True)
    mobile_phone = Column(String(50), nullable=True)
    secondary_phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Personal Information
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(50), nullable=True)
    
    # Diversity Information (for affirmative action tracking)
    diversity_race_ethnicity = Column(String(50), nullable=True)  # white, black, brown, indigenous, asian, other
    diversity_disability = Column(Boolean, default=False)  # Has disability
    diversity_disability_type = Column(String(100), nullable=True)  # physical, visual, hearing, intellectual, multiple
    diversity_lgbtqia = Column(Boolean, default=False)  # Identifies as LGBTQIA+
    diversity_refugee = Column(Boolean, default=False)  # Is refugee
    diversity_age_50_plus = Column(Boolean, default=False)  # 50+ years old
    diversity_indigenous = Column(Boolean, default=False)  # Is indigenous
    diversity_documents = Column(JSON, default=list)  # [{type, url, uploaded_at, verified, verified_by, deadline}]
    diversity_self_declared_at = Column(DateTime, nullable=True)  # Date of self-declaration
    diversity_document_deadline = Column(DateTime, nullable=True)  # 24h deadline for document upload
    
    nationality = Column(String(100), nullable=True)
    marital_status = Column(String(50), nullable=True)
    # CPF raw DB column — NULL for new writes; pre-migration rows retain plaintext.
    # Access via hybrid_property "cpf" registered by EncryptedFieldMixin.
    _cpf_raw = Column("cpf", String(14), nullable=True)
    # PII-encrypted CPF (added by migration 060)
    _cpf_encrypted = Column("cpf_encrypted", LargeBinary, nullable=True)
    
    # Professional Profile
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    self_introduction = Column(Text, nullable=True)
    
    # Skills & Competencies
    technical_skills = Column(ARRAY(String), default=list)
    soft_skills = Column(ARRAY(String), default=list)
    languages = Column(JSON, default={})
    certifications = Column(ARRAY(String), default=list)
    interests = Column(ARRAY(String), default=list)
    
    # Location - City/State/Country
    location_city = Column(String(100), nullable=True, index=True)
    location_state = Column(String(100), nullable=True)
    location_country = Column(String(100), nullable=True, index=True)
    
    # Location - Full Address
    address_street = Column(String(255), nullable=True)
    address_number = Column(String(20), nullable=True)
    address_district = Column(String(100), nullable=True)
    address_zip = Column(String(20), nullable=True)
    address_complement = Column(String(255), nullable=True)
    
    # Location - Timezone & History
    timezone = Column(String(50), nullable=True, index=True)
    past_locations = Column(JSON, default=[])
    
    # Work Preferences
    is_remote = Column(Boolean, default=False)
    willing_to_relocate = Column(Boolean, default=False)
    mobility = Column(Boolean, default=False)
    work_model_preference = Column(String(50), nullable=True)
    contract_type_preference = Column(String(50), nullable=True)
    
    # Salary - Current
    current_salary = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="BRL")
    
    # Salary - Expectations by contract type
    desired_salary_min = Column(Float, nullable=True)
    desired_salary_max = Column(Float, nullable=True)
    salary_expectation_clt = Column(Float, nullable=True)
    salary_expectation_pj = Column(Float, nullable=True)
    salary_expectation_freelance = Column(Float, nullable=True)
    
    # Resume & Documents
    resume_url = Column(String(500), nullable=True)
    resume_text = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    
    # Source & Integration Metadata
    source = Column(String(50), nullable=False, index=True)
    ats_source_name = Column(String(100), nullable=True)
    ats_candidate_id = Column(String(255), nullable=True)
    pearch_profile_id = Column(String(255), nullable=True)
    
    # Pearch/Global Search Data (campos exclusivos da busca global)
    is_open_to_work = Column(Boolean, nullable=True)
    is_decision_maker = Column(Boolean, nullable=True)
    is_top_universities = Column(Boolean, nullable=True)
    is_hiring = Column(Boolean, nullable=True)
    headline = Column(String(500), nullable=True)
    expertise = Column(ARRAY(String), default=list)
    linkedin_followers_count = Column(Integer, nullable=True)
    linkedin_connections_count = Column(Integer, nullable=True)
    pearch_insights = Column(JSON, default={})  # match_reasoning, overall_summary, query_insights
    outreach_message = Column(Text, nullable=True)
    
    # Pearch Advanced Contact & Profile Data
    best_personal_email = Column(String(255), nullable=True)  # Melhor email pessoal - ALTO VALOR
    best_business_email = Column(String(255), nullable=True)  # Melhor email corporativo - ALTO VALOR
    personal_emails = Column(JSON, default=[])  # Lista de emails pessoais
    business_emails = Column(JSON, default=[])  # Lista de emails corporativos
    phone_types = Column(JSON, default={})  # Tipos de telefone: {mobile: true, work: true, etc.}
    estimated_age = Column(Integer, nullable=True)  # Idade estimada do Pearch
    middle_name = Column(String(100), nullable=True)  # Nome do meio
    company_followers_count = Column(Integer, nullable=True)  # Seguidores da empresa atual
    company_keywords = Column(JSON, default=[])  # Palavras-chave da empresa atual
    
    # AI-Generated Insights (from LIA analysis)
    lia_score = Column(Float, nullable=True)
    lia_insights = Column(JSON, default={})
    skills_match_percentage = Column(Float, nullable=True)
    
    # Multi-tenancy (migration 082 — Task #346, NOT NULL desde 164 — 2026-05-21).
    # Legacy NULL rows backfilled via vacancy_candidates.company_id ou deletadas.
    company_id = Column(String(255), nullable=False, index=True)

    # Status & Workflow
    status = Column(String(50), default="new", index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text, nullable=True)

    # Hired tracking (set when candidate accepts an offer; added by migration 057)
    is_hired = Column(Boolean, nullable=False, default=False, server_default="false")
    hired_at = Column(DateTime, nullable=True)
    hired_job_id = Column(String(255), nullable=True)
    hired_job_title = Column(String(500), nullable=True)

    # OFF LIMITS audit trail
    blacklisted_by = Column(String(255), nullable=True)
    blacklisted_at = Column(DateTime, nullable=True)
    
    # Communication preferences
    preferred_contact_method = Column(String(50), default="email")
    best_time_to_contact = Column(String(100), nullable=True)
    communication_consent = Column(Boolean, default=True)
    preferred_channels = Column(JSON, default=lambda: ["email"])  # Lista ordenada: ["email", "whatsapp", "sms"]
    channel_opt_out = Column(JSON, default=list)  # Canais excluídos: ["marketing_email", "whatsapp"]
    
    # Registration status
    completed_register = Column(Boolean, default=False)
    accept_terms = Column(Boolean, default=False)
    
    # Work History (JSON snapshot for fast access - denormalized from candidate_experiences)
    work_history = Column(JSON, default=[])
    
    # Additional Information
    tags = Column(ARRAY(String), default=list)
    notes = Column(Text, nullable=True)
    additional_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contacted_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    scheduled_deletion_at = Column(DateTime, nullable=True, index=True)  # LGPD retention policy

    # LGPD Art.18 — legal basis for data processing
    legal_basis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lgpd_legal_bases.id"),
        nullable=True,  # nullable initially — backfill happens separately
        index=True,
        comment="LGPD Art.7: legal basis authorizing data processing for this candidate",
    )
    consent_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lgpd_consent_versions.id"),
        nullable=True,  # nullable when legal basis is not consent
        index=True,
        comment="Version of consent form candidate agreed to (required when legal_basis=consent)",
    )

    # Relationships
    experiences = relationship("CandidateExperience", backref="candidate", cascade="all, delete-orphan", lazy="dynamic")
    education_records = relationship("CandidateEducation", backref="candidate", cascade="all, delete-orphan", lazy="dynamic")
    # applications = relationship("Application", back_populates="candidate")
    # interviews = relationship("Interview", back_populates="candidate")
    
    def __repr__(self):
        return f"<Candidate {self.id} - {self.name} ({self.email})>"


class CandidateSearch(Base):
    """
    Tracks search queries and results for analytics.
    Used to understand search patterns and improve matching algorithms.
    """
    __tablename__ = "candidate_searches"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Link to chat
    
    # Search parameters
    search_query = Column(Text, nullable=False)  # Original natural language query
    search_filters = Column(JSON, default={})  # Structured filters applied
    
    # Search results
    local_results_count = Column(Integer, default=0)  # Results from proprietary DB
    global_results_count = Column(Integer, default=0)  # Results from Pearch AI
    total_results = Column(Integer, default=0)
    
    # Source & Credits
    used_global_search = Column(Boolean, default=False, index=True)
    credits_consumed = Column(Integer, default=0)
    search_source = Column(String(50), default="local")  # local, pearch, both
    
    # Performance metrics
    search_duration_ms = Column(Integer, nullable=True)
    candidates_clicked = Column(ARRAY(String), default=list)  # IDs of candidates clicked
    candidates_contacted = Column(ARRAY(String), default=list)  # IDs of candidates contacted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<CandidateSearch {self.id} - {self.user_id}>"


class CreditsUsage(Base):
    """
    Tracks Pearch AI credits consumption per company/client.
    Used for billing and usage analytics.
    """
    __tablename__ = "credits_usage"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)  # Organization/company identifier
    user_id = Column(String(255), nullable=False, index=True)
    
    # Transaction details
    action_type = Column(String(50), nullable=False, index=True)  # 'search', 'profile_view', 'contact_reveal'
    credits_amount = Column(Integer, nullable=False)  # Credits consumed (negative) or added (positive)
    credits_balance_before = Column(Integer, nullable=False)
    credits_balance_after = Column(Integer, nullable=False)
    
    # Context
    search_id = Column(UUID(as_uuid=True), nullable=True)  # Link to CandidateSearch
    candidate_id = Column(UUID(as_uuid=True), nullable=True)  # Link to Candidate
    conversation_id = Column(UUID(as_uuid=True), nullable=True)  # Link to conversation
    
    # Additional Information
    description = Column(Text, nullable=True)  # Human-readable description
    additional_data = Column(JSON, default={})  # Additional context
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<CreditsUsage {self.id} - {self.company_id}: {self.credits_amount}>"


class ViewedCandidate(Base):
    """
    Tracks which candidates have been viewed by users.
    Used to show visual indicators for viewed/unviewed candidates in the UI.
    """
    __tablename__ = "viewed_candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, default="default_user", index=True)
    viewed_at = Column(DateTime, server_default=func.now())
    source = Column(String(50), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('candidate_id', 'user_id', name='uq_viewed_candidate_user'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ViewedCandidate {self.id} - user:{self.user_id} candidate:{self.candidate_id}>"


class VacancyCandidate(Base):
    """
    Tracks candidates assigned to a job vacancy.
    Used for managing the pipeline of candidates per vacancy and goal tracking (50-70 candidates).
    """
    __tablename__ = "vacancy_candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vacancy_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    source = Column(String(50), nullable=False, default="local")
    origin = Column(String(50), nullable=True, default="web", index=True)
    lia_score = Column(Float, nullable=True)
    match_percentage = Column(Float, nullable=True)
    
    status = Column(String(50), default="sourced", index=True)
    stage = Column(String(50), default="initial", index=True)
    # Structural link to RecruitmentStage (Task #1303). Nullable for legacy rows
    # that only carry the textual `stage`. New transitions populate this so the
    # SLA detector can join by id instead of fragile name matching.
    recruitment_stage_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    previous_status = Column(String(50), nullable=True)
    
    added_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    additional_data = Column(JSON, default={})

    # Human Review Gate (L3 — LGPD art. 20 / EU AI Act art. 14)
    # Rejection without a human_reviewer_id is blocked at the API layer.
    rejected_by_human = Column(Boolean, nullable=True, default=None)
    human_reviewer_id = Column(String(255), nullable=True)
    scheduled_deletion_at = Column(DateTime, nullable=True, index=True)  # LGPD retention policy
    stage_entered_at = Column(DateTime, nullable=True, index=True)  # When candidate entered current stage

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    VALID_STATUSES = [
        "sourced", "approved", "rejected", "pending",
        "hired", "not_selected", "on_hold", "cancelled",
        "shortlisted", "screening", "interview", "offer",
    ]

    __table_args__ = (
        UniqueConstraint('vacancy_id', 'candidate_id', name='uq_vacancy_candidate'),
    {"extend_existing": True}, )

    @validates('status')
    def validate_status(self, key, value):
        if value and value not in self.VALID_STATUSES:
            raise ValueError(f"Invalid VacancyCandidate status: '{value}'. Valid: {self.VALID_STATUSES}")
        return value
    
    def __repr__(self):
        return f"<VacancyCandidate vacancy:{self.vacancy_id} candidate:{self.candidate_id}>"


class CandidateFavorite(Base):
    """
    Tracks favorited candidates per user.
    Used to persist the favorites list across sessions.
    """
    __tablename__ = "candidate_favorites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, default="default_user", index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    note = Column(Text, nullable=True)
    is_pinned = Column(Boolean, default=False)
    source = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('candidate_id', 'user_id', name='uq_favorite_candidate_user'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<CandidateFavorite {self.id} - user:{self.user_id} candidate:{self.candidate_id}>"


class CandidateHidden(Base):
    """
    Tracks hidden candidates per user.
    Hidden candidates are not shown in search results for that specific user.
    """
    __tablename__ = "candidate_hidden"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, default="default_user", index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    reason = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    __table_args__ = (
        UniqueConstraint('candidate_id', 'user_id', name='uq_hidden_candidate_user'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<CandidateHidden {self.id} - user:{self.user_id} candidate:{self.candidate_id}>"


class ExternalCandidateProfile(Base):
    """
    Staging table for discovered candidates from external sources (Pearch, LinkedIn Recruiter).
    
    These candidates appear ONLY in search results, not in the main candidate base.
    They can be "promoted" to the main candidates table when a recruiter explicitly saves them.
    
    This separation prevents:
    - Pollution of the client's proprietary database with contacts without email/phone
    - Duplicate entries when multiple external sources find the same person
    - Confusion between owned candidates and discovered profiles
    """
    __tablename__ = "external_candidate_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    source = Column(String(50), nullable=False, index=True)
    source_profile_id = Column(String(255), nullable=False, index=True)
    linkedin_url = Column(String(500), nullable=True, index=True)
    
    raw_payload = Column(JSON, default={})
    
    name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    headline = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    current_title = Column(String(255), nullable=True, index=True)
    current_company = Column(String(255), nullable=True, index=True)
    
    location_city = Column(String(100), nullable=True, index=True)
    location_state = Column(String(100), nullable=True)
    location_country = Column(String(100), nullable=True, index=True)
    location_raw = Column(String(255), nullable=True)
    
    years_of_experience = Column(Integer, nullable=True)
    seniority_level = Column(String(50), nullable=True)
    
    skills = Column(ARRAY(String), default=list)
    expertise = Column(ARRAY(String), default=list)
    languages = Column(JSON, default={})
    
    experiences_snapshot = Column(JSON, default=[])
    education_snapshot = Column(JSON, default=[])
    
    is_open_to_work = Column(Boolean, nullable=True)
    is_decision_maker = Column(Boolean, nullable=True)
    is_top_universities = Column(Boolean, nullable=True)
    is_hiring = Column(Boolean, nullable=True)
    
    # Campos avançados de contato e perfil do Pearch
    best_personal_email = Column(String(255), nullable=True)
    best_business_email = Column(String(255), nullable=True)  # Melhor email corporativo - ALTO VALOR
    personal_emails = Column(JSON, default=[])  # Lista de emails pessoais
    business_emails = Column(JSON, default=[])  # Lista de emails corporativos
    phone_types = Column(JSON, default={})  # {mobile: true, work: true, etc.}
    estimated_age = Column(Integer, nullable=True)
    middle_name = Column(String(100), nullable=True)  # Nome do meio
    company_followers_count = Column(Integer, nullable=True)  # Seguidores da empresa atual
    company_keywords = Column(JSON, default=[])  # Palavras-chave da empresa atual
    outreach_message = Column(Text, nullable=True)
    pearch_insights = Column(JSON, default={})  # match_reasoning, overall_summary, query_insights
    linkedin_followers_count = Column(Integer, nullable=True)
    linkedin_connections_count = Column(Integer, nullable=True)
    
    has_email = Column(Boolean, default=False, index=True)
    has_phone = Column(Boolean, default=False, index=True)
    contact_revealed = Column(Boolean, default=False, index=True)
    
    fingerprint_hash = Column(String(64), nullable=True, index=True)
    similarity_score = Column(Float, nullable=True)
    
    status = Column(String(50), default="discovered", index=True)
    
    search_query = Column(Text, nullable=True)
    discovered_by = Column(String(255), nullable=True)
    # Fase 4 snapshot: fingerprint da busca que trouxe este perfil (LGPD Art. 7 IX)
    search_fingerprint = Column(String(64), nullable=True, index=True)
    
    promoted_to_candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    promoted_at = Column(DateTime, nullable=True)
    promoted_by = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('source', 'source_profile_id', 'company_id', name='uq_external_source_profile'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ExternalCandidateProfile {self.id} - {self.name} ({self.source})>"


class CandidateSource(Base):
    """
    Maps candidates to their external source identifiers.
    
    Used for:
    - Tracking which external sources a candidate came from
    - Deduplication: avoid importing the same person from multiple sources
    - Linking promoted candidates back to their original discovered profiles
    """
    __tablename__ = "candidate_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source = Column(String(50), nullable=False, index=True)
    source_profile_id = Column(String(255), nullable=False, index=True)
    linkedin_url = Column(String(500), nullable=True, index=True)
    
    fingerprint_hash = Column(String(64), nullable=True, index=True)
    
    is_primary = Column(Boolean, default=False)
    
    external_profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('source', 'source_profile_id', name='uq_candidate_source_profile'),
        UniqueConstraint('candidate_id', 'source', name='uq_candidate_per_source'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<CandidateSource candidate:{self.candidate_id} source:{self.source}>"


class CandidateMergeAudit(Base):
    """
    Audit trail for candidate merge/deduplication decisions.
    
    Records when profiles are merged, who approved, and the rationale.
    Used for transparency and to allow reverting incorrect merges.
    """
    __tablename__ = "candidate_merge_audit"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    canonical_candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True)
    
    merged_profile_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    merged_profile_source = Column(String(50), nullable=True)
    merged_profile_source_id = Column(String(255), nullable=True)
    
    decision = Column(String(50), nullable=False)
    decision_source = Column(String(50), nullable=False)
    similarity_score = Column(Float, nullable=True)
    
    rationale = Column(Text, nullable=True)
    matched_fields = Column(JSON, default={})
    
    reviewer_id = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<CandidateMergeAudit {self.id} - {self.decision}>"
