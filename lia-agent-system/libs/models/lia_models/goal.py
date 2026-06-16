"""
Goal model for user goals and targets.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from lia_config.database import Base


class GoalCategory(str, enum.Enum):
    RECRUITMENT = "recruitment"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    SATISFACTION = "satisfaction"


class GoalPeriod(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class GoalStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    OVERDUE = "overdue"


class Goal(Base):
    """
    Represents a goal or target for a user.
    """
    __tablename__ = "goals"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    # TENANT-EXEMPT: Goal com company_id NULL = personal goal sem dimensao tenant (user-scoped only)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=True)
    
    template_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    target = Column(Float, nullable=False, default=0)
    current = Column(Float, nullable=False, default=0)
    unit = Column(String(100), nullable=True)
    
    period = Column(String(50), nullable=False, default="monthly")
    category = Column(String(50), nullable=False, default="recruitment")
    status = Column(String(50), nullable=False, default="pending")
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    progress = Column(Float, nullable=False, default=0)
    is_custom = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    goal_metadata = Column(JSONB, nullable=True, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_progress(self):
        """Calculate progress percentage based on current vs target."""
        if self.target and self.target > 0:
            self.progress = min((self.current / self.target) * 100, 100)
        else:
            self.progress = 0
        return self.progress

    def update_status(self):
        """Update status based on progress and dates."""
        now = datetime.utcnow()
        
        if self.progress >= 100:
            self.status = GoalStatus.ACHIEVED.value
        elif self.end_date:
            end_date = self.end_date.replace(tzinfo=None) if self.end_date.tzinfo else self.end_date
            if now > end_date:
                self.status = GoalStatus.OVERDUE.value
            elif self.current > 0:
                self.status = GoalStatus.IN_PROGRESS.value
            else:
                self.status = GoalStatus.PENDING.value
        elif self.current > 0:
            self.status = GoalStatus.IN_PROGRESS.value
        else:
            self.status = GoalStatus.PENDING.value
        
        return self.status


class GoalTemplate(Base):
    """
    Predefined goal templates that can be applied to users.
    """
    __tablename__ = "goal_templates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: GoalTemplate com company_id NULL = template global compartilhado entre tenants
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default="recruitment")
    
    default_target = Column(Float, nullable=False, default=0)
    unit = Column(String(100), nullable=True)
    period = Column(String(50), nullable=False, default="monthly")
    
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    
    template_metadata = Column(JSONB, nullable=True, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
