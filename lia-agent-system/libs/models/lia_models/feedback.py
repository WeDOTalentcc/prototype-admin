"""
Feedback models for capturing user feedback on LIA interactions.

Enables LIA to learn from:
- Thumbs up/down feedback on responses
- Star ratings with optional text feedback
- User corrections to LIA responses
- Learning patterns extracted from feedback
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class InteractionFeedback(Base):
    """
    User feedback on LIA interactions.
    
    Captures various types of feedback:
    - Thumbs up/down for quick approval/disapproval
    - Star ratings (1-5) for more nuanced feedback
    - Corrections when user provides better response
    - Free-form feedback text
    """
    __tablename__ = "interaction_feedback"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(String(100), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    
    message_id = Column(String(100), nullable=True)
    user_message = Column(Text, nullable=True)
    lia_response = Column(Text, nullable=True)
    intent = Column(String(50), nullable=True)
    stage = Column(String(50), nullable=True)
    
    rating = Column(Integer, nullable=True)
    thumbs = Column(String(10), nullable=True)
    correction = Column(Text, nullable=True)
    feedback_text = Column(Text, nullable=True)
    feedback_category = Column(String(50), nullable=True)
    
    response_time_ms = Column(Integer, nullable=True)
    tools_used = Column(JSON, default=list)
    confidence_score = Column(Float, nullable=True)
    
    processed = Column(Boolean, default=False)
    incorporated_to_rag = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "company_id": str(self.company_id) if self.company_id else None,
            "user_id": self.user_id,
            "message_id": self.message_id,
            "user_message": self.user_message,
            "lia_response": self.lia_response,
            "intent": self.intent,
            "stage": self.stage,
            "rating": self.rating,
            "thumbs": self.thumbs,
            "correction": self.correction,
            "feedback_text": self.feedback_text,
            "feedback_category": self.feedback_category,
            "response_time_ms": self.response_time_ms,
            "tools_used": self.tools_used or [],
            "confidence_score": self.confidence_score,
            "processed": self.processed,
            "incorporated_to_rag": self.incorporated_to_rag,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LearningPattern(Base):
    """
    Patterns learned from feedback for improving LIA responses.
    
    Extracted from aggregated feedback to identify:
    - What response styles work well for certain intents
    - Which tools are preferred for specific tasks
    - Common corrections that can be proactively applied
    - Trigger phrases that indicate specific user needs
    """
    __tablename__ = "learning_patterns"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    pattern_type = Column(String(50), nullable=False, index=True)
    pattern_key = Column(String(255), nullable=False, index=True)
    
    trigger_phrases = Column(JSON, default=list)
    expected_response_style = Column(Text, nullable=True)
    preferred_tools = Column(JSON, default=list)
    example_good_responses = Column(JSON, default=list)
    example_bad_responses = Column(JSON, default=list)
    
    positive_feedback_count = Column(Integer, default=0)
    negative_feedback_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)
    confidence = Column(Float, default=0.5)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "pattern_type": self.pattern_type,
            "pattern_key": self.pattern_key,
            "trigger_phrases": self.trigger_phrases or [],
            "expected_response_style": self.expected_response_style,
            "preferred_tools": self.preferred_tools or [],
            "example_good_responses": self.example_good_responses or [],
            "example_bad_responses": self.example_bad_responses or [],
            "positive_feedback_count": self.positive_feedback_count,
            "negative_feedback_count": self.negative_feedback_count,
            "success_rate": self.success_rate,
            "is_active": self.is_active,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def calculate_success_rate(self) -> float:
        """Calculate and update success rate based on feedback counts."""
        total = self.positive_feedback_count + self.negative_feedback_count
        if total == 0:
            return 0.5
        self.success_rate = self.positive_feedback_count / total
        return self.success_rate
    
    def update_confidence(self) -> float:
        """Update confidence based on sample size and success rate."""
        total = self.positive_feedback_count + self.negative_feedback_count
        if total < 5:
            self.confidence = 0.3
        elif total < 10:
            self.confidence = 0.5
        elif total < 20:
            self.confidence = 0.7
        else:
            self.confidence = min(0.95, 0.7 + (total - 20) * 0.01)
        return self.confidence
