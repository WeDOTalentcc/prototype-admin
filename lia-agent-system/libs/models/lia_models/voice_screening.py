"""
Voice Screening Database Models (Twilio Voice Integration)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from lia_config.database import Base


class VoiceScreeningCall(Base):
    """
    Voice screening call record (Twilio Voice integration).
    Stores call metadata, transcript, and candidate information.
    """
    __tablename__ = "voice_screening_calls"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Voice call identifiers
    call_id = Column(String(255), nullable=False, unique=True, index=True)
    agent_id = Column(String(255), nullable=True)
    
    # Call metadata
    call_type = Column(String(50), nullable=False)  # outbound, inbound
    call_status = Column(String(50), nullable=False)  # completed, failed, in_progress
    direction = Column(String(20), nullable=False)  # outbound, inbound
    
    # Phone numbers
    from_number = Column(String(50), nullable=True)
    to_number = Column(String(50), nullable=True)
    
    # Duration
    start_timestamp = Column(DateTime, nullable=True)
    end_timestamp = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Disconnection
    disconnection_reason = Column(String(100), nullable=True)
    
    # Candidate information
    candidate_name = Column(String(255), nullable=False, index=True)
    candidate_id = Column(String(255), nullable=True, index=True)
    candidate_phone = Column(String(50), nullable=True)  # Nullable because inbound/anonymized calls may not have it
    candidate_email = Column(String(255), nullable=True)
    
    # Job information
    job_title = Column(String(500), nullable=False, index=True)
    job_description = Column(Text, nullable=True)
    required_skills = Column(JSON, default=[])  # List of required skills
    
    # Transcript
    transcript = Column(Text, nullable=True)
    transcript_object = Column(JSON, default=[])  # Structured transcript with timestamps
    
    # Webhook metadata
    webhook_event = Column(String(100), nullable=True)  # call.started, call.ended
    webhook_timestamp = Column(DateTime, nullable=True)
    webhook_payload = Column(JSON, nullable=True)  # Full webhook payload for debugging
    
    # Status
    processing_status = Column(String(50), default="pending")  # pending, analyzing, completed, failed
    is_analyzed = Column(Boolean, default=False)
    
    # Relationships
    analysis = relationship("VoiceScreeningAnalysis", back_populates="call", uselist=False, cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<VoiceScreeningCall {self.call_id} - {self.candidate_name}>"


class VoiceScreeningAnalysis(Base):
    """
    AI-powered analysis of voice screening call.
    Stores both basic keyword analysis and deep LIA AI analysis.
    """
    __tablename__ = "voice_screening_analyses"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to screening call
    screening_call_id = Column(UUID(as_uuid=True), ForeignKey("voice_screening_calls.id"), nullable=False, unique=True, index=True)
    
    # Analysis type
    analysis_model = Column(String(100), nullable=True)  # claude-sonnet-4.5, gemini-flash-2.5, gpt-4
    analysis_method = Column(String(100), default="lia_ai_deep_analysis")
    
    # BASIC ANALYSIS (keyword-based, fast)
    basic_skills_mentioned = Column(JSON, default=[])
    basic_overall_score = Column(Integer, nullable=True)  # 0-100
    basic_recommendation = Column(String(50), nullable=True)  # proceed, review, reject
    
    # TECHNICAL ASSESSMENT (AI)
    tech_skills_mentioned = Column(JSON, default=[])
    tech_skills_matched = Column(JSON, default=[])
    tech_skills_missing = Column(JSON, default=[])
    tech_experience_years = Column(String(50), nullable=True)
    tech_projects_mentioned = Column(JSON, default=[])
    tech_score = Column(Integer, nullable=True)  # 0-100
    
    # COMMUNICATION ASSESSMENT (AI)
    comm_clarity = Column(String(20), nullable=True)  # baixa, média, alta
    comm_confidence = Column(String(20), nullable=True)  # baixa, média, alta
    comm_engagement = Column(String(20), nullable=True)  # baixo, médio, alto
    comm_professionalism = Column(String(20), nullable=True)  # baixo, médio, alto
    comm_score = Column(Integer, nullable=True)  # 0-100
    comm_notes = Column(Text, nullable=True)
    
    # CULTURAL FIT (AI)
    fit_motivation = Column(Text, nullable=True)
    fit_work_preferences = Column(Text, nullable=True)
    fit_red_flags = Column(JSON, default=[])
    fit_green_flags = Column(JSON, default=[])
    fit_score = Column(Integer, nullable=True)  # 0-100
    
    # OVERALL EVALUATION (AI)
    overall_score = Column(Integer, nullable=False, index=True)  # 0-100
    overall_recommendation = Column(String(50), nullable=False, index=True)  # reject, maybe, interview, strong_yes
    overall_confidence = Column(String(20), nullable=True)  # baixa, média, alta
    key_strengths = Column(JSON, default=[])
    key_concerns = Column(JSON, default=[])
    next_steps = Column(Text, nullable=True)
    
    # Summaries
    summary = Column(Text, nullable=True)  # Executive summary
    detailed_notes = Column(Text, nullable=True)  # Detailed notes for recruiter
    
    # Full analysis payload (for debugging/auditing)
    full_analysis_payload = Column(JSON, nullable=True)
    
    # Status
    analysis_status = Column(String(50), default="completed")  # completed, failed, partial
    error_message = Column(Text, nullable=True)
    
    # Relationships
    call = relationship("VoiceScreeningCall", back_populates="analysis")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<VoiceScreeningAnalysis {self.id} - Score: {self.overall_score}/100>"
