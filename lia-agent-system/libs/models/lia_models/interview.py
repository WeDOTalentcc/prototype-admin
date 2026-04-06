"""
Interview scheduling models with Microsoft Graph Calendar integration.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class Interview(Base):
    """
    Interview scheduling and management.
    Syncs with Microsoft Graph Calendar for automatic calendar creation.
    """
    __tablename__ = "interviews"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Interview details
    title = Column(String(255), nullable=False)  # "Entrevista Técnica - João Silva"
    description = Column(Text, nullable=True)  # Additional notes
    interview_type = Column(String(50), nullable=False)  # technical, behavioral, cultural, final
    interview_mode = Column(String(50), default="video")  # video, in_person, phone
    
    # Participants
    candidate_id = Column(UUID(as_uuid=True), nullable=True)  # Link to candidates table
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    
    interviewer_name = Column(String(255), nullable=False)
    interviewer_email = Column(String(255), nullable=False)
    additional_interviewers = Column(JSON, default=[])  # [{"name": "...", "email": "..."}]
    
    # Scheduling
    start_time = Column(DateTime, nullable=False)  # Interview start datetime
    end_time = Column(DateTime, nullable=False)  # Interview end datetime
    timezone = Column(String(100), default="America/Sao_Paulo")
    duration_minutes = Column(Integer, default=60)
    
    # Location/Meeting details
    location = Column(String(500), nullable=True)  # Physical location
    meeting_url = Column(String(1000), nullable=True)  # Teams/Zoom/Meet link
    meeting_platform = Column(String(50), nullable=True)  # teams, zoom, meet, google_meet
    meeting_id = Column(String(255), nullable=True)  # Platform-specific meeting ID
    
    # Microsoft Graph integration
    graph_event_id = Column(String(255), nullable=True, index=True)  # Calendar event ID
    graph_calendar_id = Column(String(255), nullable=True)  # Calendar ID
    graph_organizer_email = Column(String(255), nullable=True)  # Who created the event
    is_synced_to_calendar = Column(Boolean, default=False)
    calendar_sync_error = Column(Text, nullable=True)  # Last sync error message
    last_synced_at = Column(DateTime, nullable=True)

    # Google Calendar integration (Sprint 5)
    google_event_id = Column(String(255), nullable=True, index=True)
    google_meet_link = Column(String(500), nullable=True)
    
    # Status tracking
    status = Column(String(50), default="scheduled", index=True)  
    # scheduled, confirmed, rescheduled, completed, cancelled, no_show
    
    confirmation_status = Column(String(50), default="pending")  
    # pending, confirmed_by_candidate, declined_by_candidate
    
    # Notifications
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    confirmation_request_sent = Column(Boolean, default=False)
    confirmation_request_sent_at = Column(DateTime, nullable=True)
    
    # Job context
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=True)  # Link to job_vacancies table
    job_title = Column(String(255), nullable=True)
    application_stage = Column(String(100), nullable=True)  # triagem, tecnica, final, etc
    recruitment_stage_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Feedback & Results
    feedback = Column(JSON, default={})  # {"technical_score": 8, "notes": "..."}
    interviewer_notes = Column(Text, nullable=True)
    recording_url = Column(String(1000), nullable=True)  # If interview was recorded
    
    # AI-generated content
    lia_preparation_notes = Column(JSON, default={})  # LIA suggestions for interviewer
    lia_suggested_questions = Column(JSON, default=[])  # ["Explique sua experiência com...", ...]
    
    # Metadata
    created_by = Column(String(255), nullable=False, default="system")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Interview {self.id} - {self.candidate_name} ({self.status})>"


class InterviewFeedback(Base):
    """
    Detailed feedback from interview participants.
    """
    __tablename__ = "interview_feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Feedback provider
    interviewer_name = Column(String(255), nullable=False)
    interviewer_email = Column(String(255), nullable=False)
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
