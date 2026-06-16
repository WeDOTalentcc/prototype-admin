"""
Job Vacancy models for conversational job creation system.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class JobVacancy(Base):
    """
    Represents a job vacancy created through conversational flow with LIA.
    Supports both traditional fields and new conversational creation features.
    """
    __tablename__ = "job_vacancies"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant scoping (multi-tenancy)
    company_id = Column(String(255), nullable=False, index=True)
    
    # Basic Information
    job_id = Column(String(50), nullable=True, index=True)  # WDT-2025-001
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    # RBAC Sprint 2 (2026-05-25): FK to Department (coexiste com 'department' string display).
    # NULL = legacy (no scope filter). Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)  # Onda 2B: cidade canonica (dataset global IBGE), separada de location/Endereco
    work_model = Column(String(50), nullable=True)  # presencial, híbrido, remoto
    employment_type = Column(String(50), nullable=True)  # CLT, PJ, Temporary
    seniority_level = Column(String(50), nullable=True)  # Júnior, Pleno, Sênior, Especialista
    
    # Description & Requirements
    description = Column(Text, nullable=True)
    requirements = Column(ARRAY(String), default=list)  # Basic requirements (legacy)

    # T-1166 — Responsibilities (job duties), separated from requirements.
    # `imported_job_descriptions.responsibilities` and IntakeExtractor's
    # `JobIntakePayload.responsibilities` already separate this from
    # `technical_skills`/`requirements`; this column closes the schema gap
    # so persist callsites stop collapsing both lists into `requirements`.
    # Backfill via scripts/backfill_job_vacancy_responsibilities.py.
    responsibilities = Column(ARRAY(String), default=list)
    
    # NEW: Structured Technical Requirements (from documents)
    technical_requirements = Column(JSON, default=list)  # [{"category": "Linguagens", "technology": "Python", "level": "Avançado", "required": true}]
    
    # NEW: Languages
    languages = Column(JSON, default=list)  # [{"language": "Inglês", "level": "Intermediário", "required": true}]
    
    # NEW: Behavioral Competencies
    behavioral_competencies = Column(JSON, default=list)  # [{"competency": "Liderança", "weight": "Essencial"}]
    
    # Salary Information
    salary = Column(String(100), nullable=True)  # Legacy string format
    # NEW: Structured salary range
    salary_range = Column(JSON, nullable=True)  # {"min": 12000, "max": 18000, "currency": "BRL"}
    
    # NEW: Structured bonus range
    bonus_range = Column(JSON, nullable=True)  # {"min": 5000, "max": 8000, "currency": "BRL"}
    # Verbas variaveis estruturadas (snapshot+ref) — mirror benefits. Migration 230.
    variable_compensation = Column(JSON, default=list)
    
    benefits = Column(JSON, default=list)
    
    # Status & Workflow
    status = Column(String(50), default="Rascunho", index=True)  # Ativa, Rascunho, Pausada, Concluída, etc
    stage = Column(String(50), default="Planejamento", index=True)  # Planejamento, Aprovação, Publicada, etc
    priority = Column(String(20), default="média")  # alta, média, baixa
    urgency_level = Column(Integer, default=3)  # 1-5
    
    # Dates
    open_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    
    # NEW: Detailed Deadlines for recruitment stages
    deadline_screening = Column(DateTime, nullable=True)  # Prazo de triagem
    deadline_shortlist = Column(DateTime, nullable=True)  # Data da shortlist
    deadline_closing = Column(DateTime, nullable=True)    # Prazo final de fechamento
    
    # People
    manager = Column(String(255), nullable=True)
    manager_email = Column(String(255), nullable=True)
    recruiter = Column(String(255), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    # T10 — Stakeholders/envolvidos adicionais (HRBP, líder de área, comitê, etc.)
    # Format: [{"name": "Ana Silva", "email": "ana@co.com", "role": "hr_bp"}, ...]
    stakeholders = Column(JSON, default=list, server_default="[]", nullable=False)
    created_by = Column(String(255), nullable=True)  # User who created via LIA
    
    # NEW: Organizational Structure
    organizational_structure = Column(JSON, nullable=True)  # {"directManager": "...", "teamSize": 6, "teamComposition": [...]}
    
    # NEW: Interview Stages (detailed from documents)
    interview_stages = Column(JSON, default=list)  # [{"stageName": "RH", "interviewers": [...], "format": "Comportamental", "duration": 45, "schedulingWindow": "..."}]
    
    # NEW: Screening Questions (for LIA to ask candidates)
    screening_questions = Column(JSON, default=list)  # [{"id": "1", "question": "...", "type": "text", "weight": 5}]

    # Eligibility questions opt-out: IDs of CompanyScreeningQuestion records disabled for this job
    # Empty list = all company defaults are active. Add an ID here to disable it.
    disabled_eligibility_question_ids = Column(JSON, default=list)
    
    # Publishing
    published_linkedin = Column(Boolean, default=False)
    published_website = Column(Boolean, default=False)
    published_indeed = Column(Boolean, default=False)
    
    # Job Board Integration IDs
    linkedin_post_id = Column(String(255), nullable=True)
    indeed_job_id = Column(String(255), nullable=True)
    last_published_at = Column(DateTime, nullable=True)
    
    # Confidentiality & Affirmative Action
    is_confidential = Column(Boolean, default=False)  # Legacy - use visibility instead
    is_affirmative = Column(Boolean, default=False)
    
    # NEW: Affirmative Action Criteria
    affirmative_criteria_primary = Column(String(50), nullable=True)  # gender, race_ethnicity, disability, age, lgbtqia, refugee, indigenous, other
    affirmative_criteria_secondary = Column(String(50), nullable=True)  # Optional second criterion
    affirmative_description = Column(Text, nullable=True)  # Free text description (ex: "Mulheres negras")
    affirmative_document_required = Column(Boolean, default=True)  # If document is required
    affirmative_document_types = Column(ARRAY(String), default=list)  # Types accepted: laudo_pcd, autodeclaracao_racial, etc
    
    # NEW: Visibility Control (replaces is_confidential)
    # public: todos recrutadores da empresa veem
    # internal: só equipe interna, não publica em job boards
    # confidential: só owner + access_list + admin veem
    # hidden: só admin vê
    visibility = Column(String(50), default="public", index=True)
    
    # Lista de acesso para vagas confidenciais (user_ids/emails que podem ver)
    access_list = Column(ARRAY(String), default=list)
    
    # Nome mascarado para publicação anônima (ex: "Empresa líder no segmento")
    masked_company_name = Column(String(255), nullable=True)
    
    # Controle de exclusão de sincronização com ATS
    exclude_from_sync = Column(Boolean, default=False)
    
    # Public sharing
    public_slug = Column(String(100), nullable=True, unique=True, index=True)  # URL-friendly slug for public sharing
    
    # NEW: WhatsApp Template Type (conditional based on confidentiality)
    whatsapp_template_type = Column(String(50), nullable=True)  # cold, reengagement, confidential
    
    # Budget
    budget = Column(Float, nullable=True)
    budget_used = Column(Float, default=0.0)
    
    # Approval
    approval_status = Column(String(50), default="pendente")  # pendente, aprovada, rejeitada
    approval_requested_at = Column(DateTime, nullable=True)
    approval_requested_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Tags & Targeting
    tags = Column(ARRAY(String), default=list)
    hiring_process = Column(ARRAY(String), default=list)  # Legacy stage names
    target_audience = Column(String(500), nullable=True)
    
    # NEW: Target Sector/Segment (for sourcing strategy)
    target_sector = Column(String(255), nullable=True)  # "Fintechs", "Bancos Digitais"
    target_segment = Column(String(255), nullable=True)  # "Meios de Pagamento"
    
    # Metrics & Analytics
    nps = Column(Integer, nullable=True)
    funnel_data = Column(JSON, default={})  # {"total": 0, "screening": 0, "interview": 0, ...}
    lia_metrics = Column(JSON, default={})  # {"pipeline_lia": 0, "triagens_agendadas": 0, "triagens_realizadas": 0, "sem_resposta": 0, "entrevistas_agendadas": 0}
    view_count = Column(Integer, default=0)  # Public page view count
    
    # Next Actions
    next_actions = Column(ARRAY(String), default=list)
    
    # NEW: Timeline (calculated chronogram)
    timeline = Column(JSON, nullable=True)  # {"shortlistDeadline": "...", "totalWeeks": 4, "weeklyBreakdown": [...]}
    
    # NEW: Governance Rules (LIA autonomy levels)
    governance_rules = Column(JSON, nullable=True)  # {"autoScheduleInterviews": true, "autoSendNegativeFeedback": true, ...}
    
    # NEW: Screening Configuration (channels, settings, metrics, scheduling)
    screening_config = Column(JSON, nullable=True)  # {"channels": {...}, "settings": {...}, "metrics": {...}, "scheduling": {...}}
    
    # NEW: Eligibility Questions - Pre-screening questions that determine if candidate advances
    # These are asked BEFORE the WSI screening questions and are eliminatory
    # Format: [{"id": "lang_en", "type": "language", "question": "Você possui fluência em inglês?", 
    #           "criteria": {"language": "Inglês", "min_level": "Avançado"}, "required": true, 
    #           "disqualify_on_fail": true, "order": 1}]
    eligibility_questions = Column(JSON, default=list)
    
    # NEW: Confidentiality Configuration - Controls what LIA can reveal during conversations
    # Format: {"can_reveal_company_name": false, "reveal_after_stage": "shortlist", 
    #          "masked_intro": "uma empresa líder no segmento de pagamentos", 
    #          "can_discuss_salary": true, "can_discuss_benefits": true}
    confidentiality_config = Column(JSON, nullable=True)
    
    # Enriched JD - Stores the AI-enriched version of the Job Description
    # Created during WSI screening question configuration flow
    # Format: {"description": "...", "responsibilities": [...], "technical_skills": [...], 
    #          "behavioral_competencies": [...], "generated_jd_text": "...", "updated_at": "..."}
    enriched_jd = Column(JSON, nullable=True)
    
    # Per-job pipeline customization (overrides company default)
    # Format: [{"stage_name": "screening", "stage_order": 2, "is_active": true, "sla_hours": 48, "display_name": "Triagem", "color": "#8B5CF6", "icon": "file-text"}]
    pipeline_config = Column(JSON, nullable=True)
    is_pipeline_customized = Column(Boolean, default=False, nullable=False)

    # Additional data
    additional_data = Column(JSON, default={})  # Flexible field for future expansion

    # Phase 4H — Source tracking + Wizard stage persistence (migration 107)
    # source: who created this vaga? Values:
    #   'wizard'       — canonical JobCreationGraph flow (default)
    #   'ats_import'   — POST /api/v1/jobs/bulk-import (manual upload, spreadsheet)
    #   'ats_external' — future ATS sync (Gupy, Greenhouse, Lever, …)
    #   'manual'       — direct REST POST /api/v1/jobs (no wizard)
    source = Column(String(50), nullable=False, default="wizard",
                    server_default="wizard", index=True)
    # wizard_stage: persists current LangGraph node when source='wizard'.
    # Synced by WizardSessionService.process_message after each node:
    #   intake|jd_enrichment|bigfive|salary|competency|wsi_questions|
    #   eligibility|review|published|calibration|handoff
    # NULL for non-wizard sources.
    wizard_stage = Column(String(50), nullable=True, index=True)

    # Task #435 — source_system slug for lifecycle classification (Recrutar page).
    # Column already exists in DB; adding here so SQLAlchemy ORM can read/write.
    # Values: 'gupy' | 'pandape' | 'merge' | 'kenoby' | 'solides' | 'abler' |
    #         'greenhouse' | 'ats_other' (catch-all for non-listed ATS)
    # NULL for vacancies created via wizard/manual REST.
    # Used by analytics.py:_classify_job_lifecycle_stage to assign
    # 'ats_importada' stage in the Recrutar page rail.
    source_system = Column(String(50), nullable=True, index=True)

    # Sprint G #27 D2 follow-up — Job Readiness Hub (Task #429) state columns.
    # DB schema already has these (varchar(40), json, timestamp); adding to ORM
    # so SQLAlchemy actually persists writes. Without these declarations,
    # job_readiness_service.py:239,240,322 mutates transient attributes that
    # silently no-op (D2a ORM bypass failure mode).
    # readiness_stage values: importada | sem_jd | jd_rascunho | jd_enriquecido |
    #                        perguntas_triagem | pronta_disparo | em_triagem
    readiness_stage = Column(String(40), nullable=True, index=True)
    readiness_blockers = Column(JSON, nullable=True)
    last_readiness_event_at = Column(DateTime, nullable=True)

    
    # Talent Funnel - Job Qualification Classification (WDT-009)
    qualification_level = Column(String(20), nullable=True, index=True)  # "alta", "media", "baixa"
    qualification_confidence = Column(Float, nullable=True)  # 0.0 - 1.0
    qualification_reasoning = Column(Text, nullable=True)  # LLM reasoning
    qualification_override = Column(Boolean, default=False)  # True if recruiter manually overrode
    qualification_classified_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Foreign key to conversation (if created via LIA chat)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    
    # Relationships
    # conversation = relationship("Conversation", back_populates="job_vacancies")
    
    def __repr__(self):
        return f"<JobVacancy {self.id} - {self.title} ({self.status})>"


class JobVacancyInterviewStage(Base):
    """
    Represents a detailed interview stage for a job vacancy.
    Separated table for better normalization and querying.
    """
    __tablename__ = "job_vacancy_interview_stages"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id"), nullable=False, index=True)
    
    # Stage details
    stage_name = Column(String(100), nullable=False)  # "Entrevista RH", "Entrevista Técnica"
    stage_order = Column(Integer, default=1)  # Order in the process
    interviewers = Column(ARRAY(String), default=list)  # ["Ana Silva", "João Costa"]
    format = Column(String(100), nullable=True)  # "Comportamental", "Técnica", "Cultural"
    duration = Column(Integer, nullable=True)  # Minutes
    scheduling_window = Column(String(255), nullable=True)  # "Terças e Quintas à tarde"
    has_script = Column(Boolean, default=False)
    script_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<InterviewStage {self.id} - {self.stage_name}>"


class JobVacancyTemplate(Base):
    """
    Templates for job vacancies (for Admin configuration).
    Allows clients to configure standard recruitment journeys.
    """
    __tablename__ = "job_vacancy_templates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # "Tech", "Sales", "HR"
    
    # Template configuration
    default_interview_stages = Column(JSON, default=list)
    default_screening_questions = Column(JSON, default=list)
    default_timeline_weeks = Column(Integer, default=4)
    default_governance_rules = Column(JSON, default={})
    
    # Visibility
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # Available to all clients
    created_by = Column(String(255), nullable=True)  # Admin who created
    
    # Usage stats
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<JobVacancyTemplate {self.id} - {self.name}>"
