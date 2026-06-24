"""
Company Setup models for platform configuration.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, Numeric, Index, CheckConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class Company(Base):
    """Tenant root row in ``companies`` (Task #969 / T-C).

    This is the canonical SQLAlchemy mapping for the tenant-id table that
    underlies every multi-tenant query — it was previously accessed only
    via raw SQL plus ``ensure_default_company``, which is why
    ``TenantContextService`` silently fell back to ``"sua empresa"``
    for every tenant (``ImportError`` swallowed by its broad ``except``).

    Migration ``127_enrich_companies_schema`` enriched the schema with
    ``sector / industry_segment / plan / timezone / headcount_range /
    lia_persona_override``; this model exposes those fields so the
    persona prompt actually reflects per-tenant context.

    ``id`` is intentionally ``String(255)`` (not ``UUID``) because
    Demo Company uses a UUID v4 *string* and tenants may also use slugs
    — both shapes are validated server-side by ``CompanyId.parse()``
    and at the DB layer by ``ck_companies_id_format_canonical``.
    """

    __tablename__ = "companies"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Enriched persona-context columns (migration 127 / Task #969):
    sector = Column(String(100), nullable=True)
    industry_segment = Column(String(100), nullable=True)
    plan = Column(String(50), nullable=True, default="standard")
    timezone = Column(String(64), nullable=True, default="America/Sao_Paulo")
    headcount_range = Column(String(50), nullable=True)
    lia_persona_override = Column(Text, nullable=True)


class CompanyProfile(Base):
    """
    Main company profile and general information.
    Core of the Phase 0 Setup & Calibration.
    """
    __tablename__ = "company_profiles"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=True, unique=True, index=True)
    
    name = Column(String(255), nullable=False)
    trading_name = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(Text, nullable=True)
    
    cnpj = Column(String(18), nullable=True)
    industry = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    founded_year = Column(Integer, nullable=True)
    
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    
    headquarters_city = Column(String(100), nullable=True)
    headquarters_state = Column(String(100), nullable=True)
    headquarters_country = Column(String(100), default="Brasil")
    address = Column(Text, nullable=True)
    
    main_phone = Column(String(50), nullable=True)
    hr_phone = Column(String(50), nullable=True)
    main_email = Column(String(255), nullable=True)
    hr_email = Column(String(255), nullable=True)
    
    linkedin_url = Column(String(500), nullable=True)
    glassdoor_url = Column(String(500), nullable=True)
    
    employee_count = Column(Integer, nullable=True)
    revenue_range = Column(String(100), nullable=True)

    # Modelos de contratacao que a empresa usa (CLT, PJ, Estagio, Temporario,
    # Freelancer). Fonte company-wide para heranca na criacao de vaga (FASE 1,
    # audit 2026-06-06). A vaga (JobVacancy.employment_type) escolhe UM desta lista.
    employment_types = Column(ARRAY(String), nullable=False, server_default="{}", default=list)
    # Contratacao primaria (default herdado pela vaga quando o recrutador nao
    # especifica). E3 (audit 2026-06-06).
    primary_employment_type = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, default=True)
    # PR-B (Task #1016) — `is_default` precisa ser NOT NULL com default
    # `false`. Em produção alguns rows legados nasceram com NULL
    # (pré-default), o que quebrava `GET /api/v1/company/profile` com
    # `ResponseValidationError` (response model declara `bool`
    # não-nullable) e o frontend interpretava como "save falhou".
    # Migration `128_company_profile_is_default_not_null.py` faz o
    # backfill + ALTER COLUMN no DB.
    is_default = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa_text("false"),
    )
    
    culture_analyzed = Column(Boolean, default=False)
    culture_analysis_date = Column(DateTime, nullable=True)
    culture_insights = Column(JSON, default={})
    
    ats_history_analyzed = Column(Boolean, default=False)
    ats_analysis_date = Column(DateTime, nullable=True)
    ats_insights = Column(JSON, default={})
    
    additional_data = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    benefits = relationship("Benefit", back_populates="company", cascade="all, delete-orphan")
    culture_values = relationship("CultureValue", back_populates="company", cascade="all, delete-orphan")
    compensation_policies = relationship("CompensationPolicy", back_populates="company", cascade="all, delete-orphan")


class Department(Base):
    """
    Company departments/areas with hierarchical structure.
    """
    __tablename__ = "departments"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    manager_name = Column(String(255), nullable=True)
    manager_email = Column(String(255), nullable=True)
    manager_title = Column(String(255), nullable=True)
    manager_phone = Column(String(50), nullable=True)
    manager_id = Column(UUID(as_uuid=True), nullable=True)
    
    headcount = Column(Integer, default=0)
    budget_annual = Column(Float, nullable=True)
    
    cost_center = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    hiring_priority = Column(String(50), default="normal")
    color = Column(String(100), nullable=True)

    # Defaults/template por departamento (work_model, pipeline_template_id,
    # tech_stack, employment_types, ...). Cadeia de heranca: a criacao de vaga
    # resolve departamento.defaults[campo] > empresa. JSONB extensivel sem
    # migration por campo (FASE 1, audit 2026-06-06).
    defaults = Column(JSONB, nullable=False, server_default="{}", default=dict)

    # Filial / subsidiaria (Fase 2 matching 2026-06-18) -- migration 293.
    subsidiary_name = Column(String(255), nullable=True)
    subsidiary_cnpj = Column(String(18), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("CompanyProfile", back_populates="departments")
    children = relationship("Department", backref="parent", remote_side=[id])
    members = relationship("DepartmentMember", back_populates="department", cascade="all, delete-orphan")


class DepartmentMember(Base):
    """
    Members/employees within a department for org chart building.
    """
    __tablename__ = "department_members"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    # Bug 1 fix (2026-05-25): linkage to users when member is platform user.
    # NULL = external contact (consultant, hiring manager without login).
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    linkedin_url = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    level = Column(String(50), default="outros")
    
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    department = relationship("Department", back_populates="members")


class Benefit(Base):
    """
    Company benefits offered to employees.
    Supports: monetary (R$), percentage (%), or informative (description only)
    """
    __tablename__ = "benefits"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    
    icon = Column(String(50), nullable=True)
    value = Column(Float, nullable=True)
    value_type = Column(String(50), default="monetary")
    value_details = Column(Text, nullable=True)
    percentage_value = Column(Float, nullable=True)
    
    applicable_to = Column(ARRAY(String), default=[])
    seniority_levels = Column(ARRAY(String), default=[])
    contract_types = Column(ARRAY(String), default=[])
    departments = Column(JSONB, default=[])
    
    waiting_period_days = Column(Integer, default=0)
    
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_highlighted = Column(Boolean, default=False)
    is_discount = Column(Boolean, default=False)
    
    order = Column(Integer, default=0)
    
    provider = Column(String(255), nullable=True)
    provider_contact = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("CompanyProfile", back_populates="benefits")


class CultureValue(Base):
    """
    Company culture values and principles.
    """
    __tablename__ = "culture_values"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="value")
    
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    
    behavioral_indicators = Column(ARRAY(String), default=[])
    interview_questions = Column(ARRAY(String), default=[])
    
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    ai_generated = Column(Boolean, default=False)
    source = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("CompanyProfile", back_populates="culture_values")


class IdealProfile(Base):
    """
    Ideal candidate profiles by role/department.
    Generated by AI analysis of company culture, historical hiring, and job requirements.
    """
    __tablename__ = "ideal_profiles"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    role_type = Column(String(100), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    
    technical_requirements = Column(JSON, default={})
    behavioral_requirements = Column(JSON, default={})
    experience_requirements = Column(JSON, default={})
    education_requirements = Column(JSON, default={})
    
    big_five_ideal = Column(JSON, default={})
    
    evaluation_weights = Column(JSON, default={})
    
    mandatory_skills = Column(ARRAY(String), default=[])
    preferred_skills = Column(ARRAY(String), default=[])
    languages = Column(JSON, default={})
    
    salary_range_min = Column(Float, nullable=True)
    salary_range_max = Column(Float, nullable=True)
    
    culture_fit_criteria = Column(JSON, default={})
    
    ai_generated = Column(Boolean, default=False)
    ai_analysis_date = Column(DateTime, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    
    validated = Column(Boolean, default=False)
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class BigFiveQuestion(Base):
    """
    Big Five personality assessment questions bank.
    """
    __tablename__ = "big_five_questions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    text = Column(Text, nullable=False)
    text_en = Column(Text, nullable=True)
    
    trait = Column(String(50), nullable=False)
    facet = Column(String(100), nullable=True)
    
    polarity = Column(String(10), default="positive")
    
    scale_min = Column(Integer, default=1)
    scale_max = Column(Integer, default=5)
    scale_labels = Column(JSON, default={})
    
    category = Column(String(100), default="general")
    role_specific = Column(ARRAY(String), default=[])
    
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    is_core = Column(Boolean, default=False)
    
    validation_stats = Column(JSON, default={})
    
    ai_generated = Column(Boolean, default=False)
    
    order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BigFiveRoleProfile(Base):
    """
    Big Five ideal profiles for specific roles.
    """
    __tablename__ = "big_five_role_profiles"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: BigFiveRoleProfile com company_id NULL = template canonical compartilhado
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    role_category = Column(String(100), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    
    openness_min = Column(Float, default=1.0)
    openness_max = Column(Float, default=5.0)
    openness_ideal = Column(Float, default=3.0)
    openness_weight = Column(Float, default=1.0)
    
    conscientiousness_min = Column(Float, default=1.0)
    conscientiousness_max = Column(Float, default=5.0)
    conscientiousness_ideal = Column(Float, default=3.0)
    conscientiousness_weight = Column(Float, default=1.0)
    
    extroversion_min = Column(Float, default=1.0)
    extroversion_max = Column(Float, default=5.0)
    extroversion_ideal = Column(Float, default=3.0)
    extroversion_weight = Column(Float, default=1.0)
    
    agreeableness_min = Column(Float, default=1.0)
    agreeableness_max = Column(Float, default=5.0)
    agreeableness_ideal = Column(Float, default=3.0)
    agreeableness_weight = Column(Float, default=1.0)
    
    neuroticism_min = Column(Float, default=1.0)
    neuroticism_max = Column(Float, default=5.0)
    neuroticism_ideal = Column(Float, default=3.0)
    neuroticism_weight = Column(Float, default=1.0)
    
    facet_requirements = Column(JSON, default={})
    
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=True)
    
    usage_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class TechnicalQuestion(Base):
    """
    Technical assessment questions bank.
    """
    __tablename__ = "technical_questions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    question_type = Column(String(50), nullable=False)
    difficulty = Column(String(20), default="medium")
    estimated_time = Column(Integer, default=5)
    
    area = Column(String(100), nullable=False)
    tags = Column(ARRAY(String), default=[])
    
    options = Column(JSON, default=[])
    correct_answer = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    
    code_template = Column(Text, nullable=True)
    code_solution = Column(Text, nullable=True)
    code_language = Column(String(50), nullable=True)
    test_cases = Column(JSON, default=[])
    
    rubric = Column(JSON, default={})
    
    ai_generated = Column(Boolean, default=False)
    ai_correction_enabled = Column(Boolean, default=True)
    
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    usage_count = Column(Integer, default=0)
    avg_score = Column(Float, nullable=True)
    avg_time = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class TechnicalTestTemplate(Base):
    """
    Templates for technical assessments.
    """
    __tablename__ = "technical_test_templates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: TechnicalTestTemplate com company_id NULL = template publico do marketplace
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    area = Column(String(100), nullable=True)
    role_type = Column(String(100), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    
    question_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    question_config = Column(JSON, default={})
    
    total_time = Column(Integer, default=60)
    passing_score = Column(Float, default=70.0)
    
    instructions = Column(Text, nullable=True)
    instructions_en = Column(Text, nullable=True)
    
    randomize_questions = Column(Boolean, default=True)
    randomize_options = Column(Boolean, default=True)
    show_score = Column(Boolean, default=True)
    
    proctoring_enabled = Column(Boolean, default=False)
    webcam_required = Column(Boolean, default=False)
    
    ai_correction_enabled = Column(Boolean, default=True)
    ai_correction_prompt = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    usage_count = Column(Integer, default=0)
    avg_score = Column(Float, nullable=True)
    completion_rate = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class BenefitTemplate(Base):
    """
    Pre-registered benefit templates for recruiters.
    Global templates not linked to any specific company.
    """
    __tablename__ = "benefit_templates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlobalSearchSettings(Base):
    """
    Global search configuration settings per company.
    """
    __tablename__ = "global_search_settings"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: GlobalSearchSettings (tabela explicitamente global, nome confirma)
    company_id = Column(String(255), nullable=True, index=True)
    
    default_limit = Column(Integer, default=50)
    search_type = Column(String(20), default='fast')
    show_emails = Column(Boolean, default=False)
    show_phone_numbers = Column(Boolean, default=False)
    high_freshness = Column(Boolean, default=False)
    auto_expand_global = Column(Boolean, default=False)
    confirm_before_search = Column(Boolean, default=True)
    global_search_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Approver(Base):
    """
    Approval workflow levels for job vacancies and hiring decisions.
    """
    __tablename__ = "approvers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    
    level = Column(Integer, nullable=False, default=1)
    
    # P0.D2 (audit Wave 2 2026-05-22): per-department + amount-threshold routing.
    # NULL department_id = company-wide approver (backward-compat default).
    # NULL can_approve_above_amount = approver pode aprovar qualquer valor.
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    can_approve_above_amount = Column(Numeric(12, 2), nullable=True)

    # Sprint 2 (2026-06-21): 'platform' = usuario interno; 'email_link' = externo magic link.
    approval_method = Column(String(20), nullable=False, default="email_link")

    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_approvers_company_department", "company_id", "department_id"),
        CheckConstraint(
            "can_approve_above_amount IS NULL OR can_approve_above_amount >= 0",
            name="ck_approver_amount_nonneg",
        ),
    {"extend_existing": True}, )
