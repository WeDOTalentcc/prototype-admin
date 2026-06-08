"""
Interview scheduling models with Microsoft Graph Calendar integration.

P0.B (audit 2026-05-21): emails encriptados at-rest via EncryptedFieldMixin
canonical (Fernet + SHA-256 hash). Migration 160 adicionou colunas
``*_encrypted`` + ``*_hash`` + flipou ``candidate_email`` /
``interviewer_email`` (interviews + interview_feedbacks) NOT NULL →
nullable=True (transition phase dual-write).

Caller-side: NENHUMA mudança necessária. ``interview.candidate_email = "x@y"``
continua funcionando via hybrid_property registrada pelo mixin —
encryption + hash são automáticos. ``interview.candidate_email`` (read)
retorna plaintext decrypted transparentemente.

Pre-migration rows preservam plaintext em ``_candidate_email_raw`` /
``_interviewer_email_raw`` / ``_graph_organizer_email_raw`` até a
Celery task ``pii.backfill_encrypt_interview_offer_existing`` rodar
(Phase 2 — separate commit).
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from lia_config.database import Base
from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin


class Interview(EncryptedFieldMixin, Base):
    """
    Interview scheduling and management.
    Syncs with Microsoft Graph Calendar for automatic calendar creation.

    PII encryption (P0.B audit 2026-05-21, migration 160):
      - candidate_email       → encrypted at rest + SHA-256 hash for lookup
      - interviewer_email     → encrypted at rest + SHA-256 hash for lookup
      - graph_organizer_email → encrypted at rest (no hash; Graph API path)
    """
    __tablename__ = "interviews"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    # _pii_encrypt_fields: (raw_attr, enc_attr, hash_attr)
    # Pattern canonical alinhado com Candidate (libs/models/lia_models/candidate.py).
    _pii_encrypt_fields = [
        ("_candidate_email_raw",       "_candidate_email_encrypted",       "candidate_email_hash"),
        ("_interviewer_email_raw",     "_interviewer_email_encrypted",     "interviewer_email_hash"),
        ("_graph_organizer_email_raw", "_graph_organizer_email_encrypted", None),
    ]

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant (NOT NULL desde migration 165 — 2026-05-21).
    # Legacy NULL rows backfilled via candidates.company_id ou deletadas.
    company_id = Column(String(255), nullable=False, index=True)

    # Interview details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    interview_type = Column(String(50), nullable=False)
    interview_mode = Column(String(50), default="video")

    # Participants
    candidate_id = Column(UUID(as_uuid=True), nullable=True)
    candidate_name = Column(String(255), nullable=False)
    # P0.B (migration 160): plaintext column kept for back-compat (dual-write phase).
    # nullable=True por causa do transition — hybrid_property grava NULL aqui
    # e encrypted bytes em _candidate_email_encrypted. Access via hybrid_property
    # ``candidate_email`` (registered by EncryptedFieldMixin) retorna plaintext.
    _candidate_email_raw = Column("candidate_email", String(255), nullable=True)
    _candidate_email_encrypted = Column("candidate_email_encrypted", LargeBinary, nullable=True)
    candidate_email_hash = Column(String(64), nullable=True, index=True)

    interviewer_name = Column(String(255), nullable=False)
    _interviewer_email_raw = Column("interviewer_email", String(255), nullable=True)
    _interviewer_email_encrypted = Column("interviewer_email_encrypted", LargeBinary, nullable=True)
    interviewer_email_hash = Column(String(64), nullable=True, index=True)

    additional_interviewers = Column(JSON, default=[])
    
    # Scheduling
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    timezone = Column(String(100), default="America/Sao_Paulo")
    duration_minutes = Column(Integer, default=60)
    
    # Location/Meeting details
    location = Column(String(500), nullable=True)
    meeting_url = Column(String(1000), nullable=True)
    meeting_platform = Column(String(50), nullable=True)
    meeting_id = Column(String(255), nullable=True)
    
    # Microsoft Graph integration
    graph_event_id = Column(String(255), nullable=True, index=True)
    graph_calendar_id = Column(String(255), nullable=True)
    # P0.B (migration 160): encrypted at rest. Access via hybrid_property
    # ``graph_organizer_email`` (registered by EncryptedFieldMixin).
    _graph_organizer_email_raw = Column("graph_organizer_email", String(255), nullable=True)
    _graph_organizer_email_encrypted = Column("graph_organizer_email_encrypted", LargeBinary, nullable=True)
    is_synced_to_calendar = Column(Boolean, default=False)
    calendar_sync_error = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)

    # Google Calendar integration (Sprint 5)
    google_event_id = Column(String(255), nullable=True, index=True)
    google_meet_link = Column(String(500), nullable=True)
    
    # Status tracking
    status = Column(String(50), default="scheduled", index=True)
    # scheduled, confirmed, rescheduled, completed, cancelled, no_show, transcribing, transcribed
    
    confirmation_status = Column(String(50), default="pending")
    # pending, confirmed_by_candidate, declined_by_candidate
    
    # Notifications
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    confirmation_request_sent = Column(Boolean, default=False)
    confirmation_request_sent_at = Column(DateTime, nullable=True)
    
    # Job context
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=True)
    job_title = Column(String(255), nullable=True)
    application_stage = Column(String(100), nullable=True)
    recruitment_stage_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Feedback & Results
    feedback = Column(JSON, default={})
    scorecard = Column(JSONB, nullable=True)
    interviewer_notes = Column(Text, nullable=True)
    recording_url = Column(String(1000), nullable=True)
    
    # Transcript (dedicated columns for Interview Intelligence)
    transcript = Column(Text, nullable=True)
    transcript_language = Column(String(10), nullable=True, default="pt-BR")
    transcript_source = Column(String(50), nullable=True)  # teams, gemini, manual
    transcribed_at = Column(DateTime, nullable=True)
    
    # AI-generated content
    lia_preparation_notes = Column(JSON, default={})
    lia_suggested_questions = Column(JSON, default=[])
    
    # Extended metadata
    interview_metadata = Column("metadata", JSONB, default={})
    
    # Metadata
    created_by = Column(String(255), nullable=False, default="system")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Interview {self.id} - {self.candidate_name} ({self.status})>"


class InterviewFeedback(EncryptedFieldMixin, Base):
    """
    Detailed feedback from interview participants.

    P0.B (audit 2026-05-21): interviewer_email encrypted at rest via
    EncryptedFieldMixin canonical. Caller-side: nenhuma mudança.
    """
    __tablename__ = "interview_feedbacks"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    _pii_encrypt_fields = [
        ("_interviewer_email_raw", "_interviewer_email_encrypted", "interviewer_email_hash"),
    ]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Feedback provider
    interviewer_name = Column(String(255), nullable=False)
    # P0.B (migration 160): plaintext column nullable durante transition.
    # Access via hybrid_property ``interviewer_email`` do mixin.
    _interviewer_email_raw = Column("interviewer_email", String(255), nullable=True)
    _interviewer_email_encrypted = Column("interviewer_email_encrypted", LargeBinary, nullable=True)
    interviewer_email_hash = Column(String(64), nullable=True, index=True)
    interviewer_role = Column(String(100), nullable=True)  # "Tech Lead", "HR Manager"
    
    # Ratings (0-10 scale)
    technical_skills_rating = Column(Float, nullable=True)
    communication_rating = Column(Float, nullable=True)
    cultural_fit_rating = Column(Float, nullable=True)
    overall_rating = Column(Float, nullable=True)
    
    # Detailed feedback
    strengths = Column(JSON, default=[])  # ["Excelente conhecimento em Python", ...]
    weaknesses = Column(JSON, default=[])  # ["Poderia melhorar comunicação", ...]
    notes = Column(Text, nullable=True)
    
    # Recommendation
    recommendation = Column(String(50), nullable=True)  
    # strong_yes, yes, maybe, no, strong_no
    
    next_steps_suggested = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<InterviewFeedback {self.id} - {self.interviewer_name}>"


class InterviewNote(Base):
    """
    Full interview note with WSI Score Card, questions, answers and LIA parecer.
    Replaces the in-memory dict previously used in interview_notes.py.
    """
    __tablename__ = "interview_notes"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Context
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=True)
    job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    job_title = Column(String(255), nullable=True)
    scheduled_interview_id = Column(String(255), nullable=True, index=True)

    # Interviewer
    interviewer_id = Column(String(255), nullable=True)
    recruiter_name = Column(String(255), nullable=True)

    # Interview metadata
    interview_date = Column(DateTime, nullable=True)
    interview_type = Column(String(50), default="structured")  # structured, ad_hoc

    # Content (JSON — mirrors frontend InterviewNote type)
    questions = Column(JSON, default=[])   # List[QuestionWithAnswer]
    blocks = Column(JSON, default=[])      # List[QuestionBlock] with subtotals

    # Notes and transcription
    general_notes = Column(Text, nullable=True)
    transcription = Column(Text, nullable=True)
    transcription_source = Column(String(50), nullable=True)  # teams, meet, manual

    # LIA parecer
    lia_parecer = Column(Text, nullable=True)
    lia_parecer_editado = Column(Boolean, default=False)

    # WSI Score (JSON — mirrors WSIScore type)
    wsi_score = Column(JSON, nullable=True)
    # {technicalScore, behavioralScore, gapAnalysisScore, contextualScore, totalWSI, decision}

    # Decision
    recommendation = Column(String(50), nullable=True)  # approve, reject, pending
    next_stage = Column(String(100), nullable=True)

    # Feedback
    feedback_sent = Column(Boolean, default=False)
    feedback_scheduled_for = Column(DateTime, nullable=True)

    # Status
    status = Column(String(20), default="draft", index=True)  # draft, completed

    # Audit
    created_by = Column(String(255), nullable=False, default="system")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<InterviewNote {self.id} - candidate={self.candidate_id} status={self.status}>"


class CalendarAvailability(Base):
    """
    Track interviewer availability for smart scheduling.
    """
    __tablename__ = "calendar_availability"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User
    user_email = Column(String(255), nullable=False, index=True)
    user_name = Column(String(255), nullable=False)
    
    # Availability window
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(10), nullable=False)  # "09:00"
    end_time = Column(String(10), nullable=False)  # "18:00"
    timezone = Column(String(100), default="America/Sao_Paulo")
    
    # Settings
    is_active = Column(Boolean, default=True)
    max_interviews_per_day = Column(Integer, default=4)
    buffer_minutes = Column(Integer, default=15)  # Break between interviews
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CalendarAvailability {self.user_name} - Day {self.day_of_week}>"
