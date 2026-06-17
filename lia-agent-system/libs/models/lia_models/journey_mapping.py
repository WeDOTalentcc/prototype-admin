"""
Journey Mapping models for recruitment process discovery and configuration.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from lia_config.database import Base


class JourneyStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ACTIVE = "active"


class IntegrationType(str, enum.Enum):
    ATS = "ats"
    WORKFORCE_PLANNING = "workforce_planning"
    HRIS = "hris"
    JOB_BOARD = "job_board"
    COMMUNICATION = "communication"
    ASSESSMENT = "assessment"
    BACKGROUND_CHECK = "background_check"


class JourneyBlueprint(Base):
    """Main recruitment journey blueprint for a company."""
    __tablename__ = "journey_blueprints"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), default="Jornada Principal")
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    
    wizard_step = Column(Integer, default=1)
    wizard_completed = Column(Boolean, default=False)
    wizard_data = Column(JSON, default={})
    
    ai_summary = Column(Text, nullable=True)
    ai_recommendations = Column(JSON, default=[])
    
    vacancy_origin = Column(String(100), nullable=True)
    has_external_wfp = Column(Boolean, default=False)
    has_internal_wfp = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    steps = relationship("JourneyStep", back_populates="blueprint", cascade="all, delete-orphan")
    integrations = relationship("JourneyIntegration", back_populates="blueprint", cascade="all, delete-orphan")


class JourneyStep(Base):
    """Individual step in the recruitment journey."""
    __tablename__ = "journey_steps"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("journey_blueprints.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    step_type = Column(String(100), nullable=False)
    
    order = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    is_required = Column(Boolean, default=True)
    
    config = Column(JSON, default={})
    sla_days = Column(Integer, nullable=True)
    responsible_role = Column(String(100), nullable=True)
    
    automation_enabled = Column(Boolean, default=False)
    automation_config = Column(JSON, default={})
    
    ai_enabled = Column(Boolean, default=False)
    ai_config = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    blueprint = relationship("JourneyBlueprint", back_populates="steps")


class JourneyIntegration(Base):
    """Integration point in the journey."""
    __tablename__ = "journey_integrations"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey("journey_blueprints.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    integration_type = Column(String(100), nullable=False)
    provider = Column(String(100), nullable=True)
    
    is_enabled = Column(Boolean, default=False)
    is_connected = Column(Boolean, default=False)
    
    connection_config = Column(JSON, default={})
    field_mappings = Column(JSON, default={})
    
    sync_direction = Column(String(50), default="bidirectional")
    sync_frequency = Column(String(50), default="realtime")
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="pending")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    blueprint = relationship("JourneyBlueprint", back_populates="integrations")
