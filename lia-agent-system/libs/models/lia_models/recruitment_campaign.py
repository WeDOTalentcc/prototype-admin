import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


DEFAULT_CAMPAIGN_STAGES = [
    {"name": "sourcing", "order": 1, "auto_actions": ["search_candidates"]},
    {"name": "screening", "order": 2, "auto_actions": ["apply_screening"]},
    {"name": "outreach", "order": 3, "auto_actions": ["send_outreach_email"]},
    {"name": "interview", "order": 4, "auto_actions": ["schedule_interview"]},
    {"name": "evaluation", "order": 5, "auto_actions": ["generate_evaluation"]},
    {"name": "offer", "order": 6, "auto_actions": ["prepare_offer"]},
]


class RecruitmentCampaign(Base):
    __tablename__ = "recruitment_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(64), nullable=False, index=True)
    created_by = Column(String(64), nullable=False)

    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)

    job_id = Column(String(64), nullable=True, index=True)
    talent_pool_id = Column(String(64), nullable=True)

    status = Column(String(20), nullable=False, default=CampaignStatus.ACTIVE.value)

    stages = Column(JSONB, nullable=False, default=list)
    current_stage_index = Column(Integer, nullable=False, default=0)
    automation_level = Column(String(20), nullable=False, default="semi")

    total_candidates = Column(Integer, default=0)
    candidates_screened = Column(Integer, default=0)
    candidates_contacted = Column(Integer, default=0)
    candidates_interviewed = Column(Integer, default=0)
    candidates_offered = Column(Integer, default=0)
    candidates_hired = Column(Integer, default=0)

    stage_history = Column(JSONB, nullable=False, default=list)

    # multi-vacancy + Agent Studio wiring (migration 289)
    job_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True, default=list)
    agent_ids = Column(ARRAY(String()), nullable=True, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_campaign_company", "company_id"),
        Index("idx_campaign_status", "status"),
        Index("idx_campaign_job", "job_id"),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<RecruitmentCampaign id={self.id} name='{self.name}' status={self.status}>"

    @property
    def current_stage(self) -> dict | None:
        if self.stages and 0 <= self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None

    @property
    def progress_pct(self) -> float:
        if not self.stages:
            return 0.0
        if self.status == "completed":
            return 100.0
        return round((self.current_stage_index / len(self.stages)) * 100, 1)

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "created_by": self.created_by,
            "name": self.name,
            "description": self.description,
            "job_id": self.job_id,
            "talent_pool_id": self.talent_pool_id,
            "status": self.status,
            "stages": self.stages or [],
            "current_stage_index": self.current_stage_index,
            "current_stage": self.current_stage,
            "automation_level": self.automation_level,
            "progress_pct": self.progress_pct,
            "total_candidates": self.total_candidates,
            "candidates_screened": self.candidates_screened,
            "candidates_contacted": self.candidates_contacted,
            "candidates_interviewed": self.candidates_interviewed,
            "candidates_offered": self.candidates_offered,
            "candidates_hired": self.candidates_hired,
            "stage_history": self.stage_history or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
