"""
Activity Feed Database Model
Tracks all activities in the recruitment system (voice screening, emails, interviews, etc.)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON, Index

from lia_config.database import Base


class ActivityFeed(Base):
    """
    Activity Feed - Timeline of all recruitment activities.
    Used in:
    1. Painel de Controle (general feed, all activities)
    2. Candidate Preview (filtered by candidate_id)
    """
    __tablename__ = "activity_feed"
    
    # CRITICAL: ID must be String (VARCHAR) to match existing database schema
    # Database has character varying(255) - NEVER change primary key types
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Activity type (voice_screening, email_sent, interview_completed, etc.)
    activity_type = Column(String(50), nullable=False, index=True)
    
    # Actor (who performed the action)
    actor_id = Column(String(255), nullable=True, index=True)  # User ID or "system" or "lia"
    # TENANT-EXEMPT: feed system-wide (actor inclui system/lia, nao apenas user-tenant)
    company_id = Column(String(255), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)  # "Ana Costa", "LIA", "Sistema"
    actor_type = Column(String(50), nullable=True)  # "recruiter", "system", "candidate", "ai"
    
    # Target (what/who was affected)
    target_id = Column(String(255), nullable=True, index=True)  # Candidate ID, Job ID, etc.
    target_name = Column(String(255), nullable=True)  # "João Silva", "Backend Sênior"
    target_type = Column(String(50), nullable=True)  # "candidate", "job", "email", "test"
    
    # Content
    title = Column(String(255), nullable=False)  # "Voice Screening Completado"
    description = Column(Text, nullable=True)  # Longer description
    summary = Column(Text, nullable=True)  # Short summary for cards
    
    # Extra data (JSON with activity-specific data)
    # Renamed from 'metadata' to avoid SQLAlchemy conflict
    # For voice_screening: {score, recommendation, key_strengths, etc.}
    # For email_sent: {subject, recipient, email_type, etc.}
    # For interview: {feedback, interviewer, decision, etc.}
    extra_data = Column(JSON, default={})
    
    # Priority/Category
    priority = Column(String(20), default="normal", index=True)  # urgent, normal, low
    category = Column(String(50), nullable=True)  # screening, hiring, communication, testing
    
    # Action link (CTA button)
    action_url = Column(String(500), nullable=True)  # "/voice-screening/123"
    action_label = Column(String(100), nullable=True)  # "Ver Análise Completa"
    
    # Visibility control
    is_visible = Column(Boolean, default=True, index=True)
    visible_to = Column(JSON, default=[])  # Array of user_ids who can see this activity
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)  # User who triggered this activity

    # LGPD compliance columns (Task 2.C, 2026-05-25)
    # Art. 15: retention period. Null = system event / indefinite.
    retention_expires_at = Column(DateTime, nullable=True)
    # Art. 7: legal basis. Values: consent | contract | legal_obligation |
    #   vital_interests | public_task | legitimate_interests
    legal_basis = Column(String(50), nullable=True)
    # Art. 20: automated decision transparency.
    # Values: automated | human_review | human_final | no_decision
    decision_type = Column(String(50), nullable=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_activity_candidate', 'target_id', 'activity_type', 'created_at'),
        Index('idx_activity_priority_date', 'priority', 'created_at'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ActivityFeed {self.activity_type} - {self.title}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        actor_dict = None
        if self.actor_id is not None:
            actor_dict = {
                "id": self.actor_id,
                "name": self.actor_name,
                "type": self.actor_type,
            }
        
        target_dict = None
        if self.target_id is not None:
            target_dict = {
                "id": self.target_id,
                "name": self.target_name,
                "type": self.target_type,
            }
        
        action_dict = None
        if self.action_url is not None:
            action_dict = {
                "url": self.action_url,
                "label": self.action_label,
            }
        
        created_at_str = None
        if self.created_at is not None:
            created_at_str = self.created_at.isoformat()
        
        return {
            "id": str(self.id),
            "activity_type": self.activity_type,
            "actor": actor_dict,
            "target": target_dict,
            "title": self.title,
            "description": self.description,
            "summary": self.summary,
            "extra_data": self.extra_data,
            "priority": self.priority,
            "category": self.category,
            "action": action_dict,
            "is_visible": self.is_visible,
            "created_at": created_at_str,
            "created_by": self.created_by,
            "retention_expires_at": self.retention_expires_at.isoformat() if self.retention_expires_at else None,
            "legal_basis": self.legal_basis,
            "decision_type": self.decision_type,
        }
