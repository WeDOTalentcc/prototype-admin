"""
WhatsApp Conversation Model

Manages the state of WhatsApp conversations for candidate applications.
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from lia_config.database import Base
import uuid
import enum


class ConversationState(str, enum.Enum):
    """
    States for the WhatsApp conversation flow.
    
    Phase 1 (Inscription): INITIAL → WAITING_LGPD → WAITING_CV → CONFIRMING_CV →
          CONFIRMING_EMAIL → PRE_QUALIFICATION (Rubric)
    
    PAUSE: Saturation check after rubric evaluation
    - Score < 55: automatic rejection with feedback
    - Saturated: AWAITING_SCREENING (queued, "dados registrados")
    - Not saturated: proceed to Phase 2
    
    Phase 2 (Screening): SCREENING → ELIGIBILITY_CHECK →
          (WAITING_RECONSIDERATION | WAITING_CONFIRMATION) →
          ADDITIONAL_INFO → COMPLETED → FEEDBACK_SENT
    
    Eligibility states handle eliminatory questions with reconsideration:
    - ELIGIBILITY_CHECK: Asking eligibility questions
    - WAITING_RECONSIDERATION: Candidate got incompatible answer, waiting for 1/2 choice
    - WAITING_CONFIRMATION: Candidate chose to reconsider, confirming new answer
    - REDIRECTED_TALENT_POOL: Candidate kept incompatible answer → talent pool
    - AWAITING_SCREENING: Candidate queued due to pipeline saturation
    """
    INITIAL = "initial"
    WAITING_LGPD = "waiting_lgpd"
    WAITING_CV = "waiting_cv"
    CONFIRMING_CV = "confirming_cv"
    CONFIRMING_EMAIL = "confirming_email"
    PRE_QUALIFICATION = "pre_qualification"
    ELIGIBILITY_CHECK = "eligibility_check"
    WAITING_RECONSIDERATION = "waiting_reconsideration"
    WAITING_CONFIRMATION = "waiting_confirmation"
    REDIRECTED_TALENT_POOL = "redirected_talent_pool"
    AWAITING_SCREENING = "awaiting_screening"
    SCREENING = "screening"
    ADDITIONAL_INFO = "additional_info"
    COMPLETED = "completed"
    FEEDBACK_SENT = "feedback_sent"
    EXPIRED = "expired"


class WhatsAppConversation(Base):
    """
    Stores the state and data of WhatsApp conversations for job applications.
    
    Each conversation is tied to a phone number and optionally to a job vacancy.
    The conversation progresses through defined states as the candidate
    provides information and answers questions.
    """
    __tablename__ = "whatsapp_conversations"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    phone_number = Column(String(20), nullable=False, index=True)
    whatsapp_id = Column(String(100), nullable=True)
    
    company_id = Column(String(255), nullable=False, index=True)
    job_vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id"), nullable=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=True)
    
    state = Column(
        SQLEnum(ConversationState, name="conversation_state_enum"),
        nullable=False,
        default=ConversationState.INITIAL
    )
    current_question_index = Column(Integer, default=0)
    
    lgpd_accepted = Column(Boolean, default=False)
    lgpd_accepted_at = Column(DateTime(timezone=True), nullable=True)
    lgpd_ip_address = Column(String(50), nullable=True)
    
    cv_received = Column(Boolean, default=False)
    cv_received_at = Column(DateTime(timezone=True), nullable=True)
    cv_file_url = Column(Text, nullable=True)
    cv_file_type = Column(String(50), nullable=True)
    cv_parsed_data = Column(JSON, nullable=True)
    
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_linkedin = Column(String(500), nullable=True)
    
    screening_answers = Column(JSON, nullable=True)
    lia_score = Column(String(10), nullable=True)
    lia_opinion = Column(Text, nullable=True)
    
    pre_qualification_score = Column(Integer, nullable=True)
    pre_qualification_result = Column(String(50), nullable=True)
    pre_qualification_matched = Column(JSON, nullable=True)
    pre_qualification_missing = Column(JSON, nullable=True)
    pre_qualification_decision = Column(String(50), nullable=True)
    pre_qualification_at = Column(DateTime(timezone=True), nullable=True)
    
    eligibility_answers = Column(JSON, nullable=True)
    eligibility_question_index = Column(Integer, default=0)
    reconsideration_count = Column(Integer, default=0)
    reconsideration_context = Column(JSON, nullable=True)
    had_reconsiderations = Column(Boolean, default=False)
    
    is_existing_candidate = Column(Boolean, default=False)
    existing_candidate_since = Column(DateTime(timezone=True), nullable=True)
    
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_direction = Column(String(10), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<WhatsAppConversation {self.id} - {self.phone_number} - {self.state.value}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "phone_number": self.phone_number,
            "company_id": self.company_id,
            "job_vacancy_id": str(self.job_vacancy_id) if self.job_vacancy_id else None,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "state": self.state.value,
            "current_question_index": self.current_question_index,
            "lgpd_accepted": self.lgpd_accepted,
            "cv_received": self.cv_received,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "screening_answers": self.screening_answers,
            "lia_score": self.lia_score,
            "pre_qualification_score": self.pre_qualification_score,
            "pre_qualification_result": self.pre_qualification_result,
            "pre_qualification_matched": self.pre_qualification_matched,
            "pre_qualification_missing": self.pre_qualification_missing,
            "pre_qualification_decision": self.pre_qualification_decision,
            "pre_qualification_at": self.pre_qualification_at.isoformat() if self.pre_qualification_at else None,
            "eligibility_answers": self.eligibility_answers,
            "eligibility_question_index": self.eligibility_question_index,
            "reconsideration_count": self.reconsideration_count,
            "had_reconsiderations": self.had_reconsiderations,
            "is_existing_candidate": self.is_existing_candidate,
            "existing_candidate_since": self.existing_candidate_since.isoformat() if self.existing_candidate_since else None,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WhatsAppMessage(Base):
    """
    Log of all WhatsApp messages sent and received.
    Used for audit, debugging, and conversation history.
    """
    __tablename__ = "whatsapp_messages"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_conversations.id"), nullable=False, index=True)
    
    whatsapp_message_id = Column(String(100), nullable=True)
    
    direction = Column(String(10), nullable=False)
    
    message_type = Column(String(20), nullable=False, default="text")
    content = Column(Text, nullable=True)
    media_url = Column(Text, nullable=True)
    media_type = Column(String(50), nullable=True)
    
    status = Column(String(20), default="sent")
    status_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<WhatsAppMessage {self.id} - {self.direction} - {self.message_type}>"
