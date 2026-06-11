from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, JSON, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


# ── TriagemSession canonical status constants (VARCHAR — no PG ENUM, add freely) ──
# Ordered by lifecycle: invited → awaiting_consent → started → in_progress → completed
TRIAGEM_STATUS_INVITED = "invited"
TRIAGEM_STATUS_AWAITING_CONSENT = "awaiting_consent"  # Phase 1b: waiting for LGPD SIM/NÃO
TRIAGEM_STATUS_CONSENT_DECLINED = "consent_declined"  # candidate replied NÃO
TRIAGEM_STATUS_STARTED = "started"
TRIAGEM_STATUS_IN_PROGRESS = "in_progress"
TRIAGEM_STATUS_COMPLETED = "completed"
TRIAGEM_STATUS_EXPIRED = "expired"


class TriagemSession(Base):
    __tablename__ = "triagem_sessions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(255), unique=True, nullable=False, index=True)
    candidate_id = Column(String(255), nullable=False, index=True)
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    job_id = Column(String(255), nullable=False, index=True)
    job_title = Column(String(500), nullable=True)
    company_id = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    company_logo_url = Column(String(1024), nullable=True)
    status = Column(String(50), nullable=False, default="invited", index=True)
    current_block = Column(Integer, nullable=False, default=0)
    total_blocks = Column(Integer, nullable=False, default=7)
    wsi_final_score = Column(Float, nullable=True)
    recommendation = Column(String(50), nullable=True)
    feedback_draft = Column(Text, nullable=True)
    invite_channel = Column(String(50), nullable=True, default="email")
    voice_mode = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "token": self.token,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "company_logo_url": self.company_logo_url,
            "status": self.status,
            "current_block": self.current_block,
            "total_blocks": self.total_blocks,
            "wsi_final_score": self.wsi_final_score,
            "recommendation": self.recommendation,
            "invite_channel": self.invite_channel,
            "voice_mode": self.voice_mode,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TriagemMessage(Base):
    __tablename__ = "triagem_messages"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sender = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, default="text")
    wsi_block = Column(Integer, nullable=True)
    wsi_question_id = Column(String(255), nullable=True)
    score = Column(Float, nullable=True)
    audio_base64 = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        result = {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "sender": self.sender,
            "content": self.content,
            "message_type": self.message_type,
            "wsi_block": self.wsi_block,
            "wsi_question_id": self.wsi_question_id,
            "score": self.score,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.audio_base64:
            result["audio_base64"] = self.audio_base64
        return result
