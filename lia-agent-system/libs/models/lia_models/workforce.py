"""
Workforce Planning models for hiring plan management.
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Date, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class HiringPlan(Base):
    """
    Annual hiring plan for workforce planning.
    Contains the overall plan for hiring in a fiscal year.
    """
    __tablename__ = "hiring_plans"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    fiscal_year = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(String(50), default="draft")
    
    owner_name = Column(String(255), nullable=True)
    owner_email = Column(String(255), nullable=True)
    
    total_headcount = Column(Integer, default=0)
    total_budget = Column(Float, nullable=True)
    currency = Column(String(10), default="BRL")
    
    ai_source_metadata = Column(JSON, default={})
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    planned_headcounts = relationship("PlannedHeadcount", back_populates="hiring_plan", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="hiring_plan", cascade="all, delete-orphan")


class PlannedHeadcount(Base):
    """
    Planned position within a hiring plan.
    Represents individual positions to be filled.
    """
    __tablename__ = "planned_headcounts"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hiring_plan_id = Column(UUID(as_uuid=True), ForeignKey("hiring_plans.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    ideal_profile_id = Column(UUID(as_uuid=True), ForeignKey("ideal_profiles.id"), nullable=True)
    
    target_month = Column(Integer, nullable=False)
    target_year = Column(Integer, nullable=False)
    
    title = Column(String(255), nullable=False)
    level = Column(String(100), nullable=True)
    contract_type = Column(String(100), nullable=True)
    
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="BRL")
    
    headcount = Column(Integer, default=1)
    justification = Column(Text, nullable=True)
    
    hiring_manager_name = Column(String(255), nullable=True)
    hiring_manager_email = Column(String(255), nullable=True)
    
    technical_profile = Column(JSON, default={})
    behavioral_profile = Column(JSON, default={})
    job_description = Column(Text, nullable=True)
    
    priority = Column(String(50), default="medium")
    
    hiring_window_start = Column(Date, nullable=True)
    hiring_window_end = Column(Date, nullable=True)
    
    status = Column(String(50), default="planned")
    
    linked_vacancy_id = Column(UUID(as_uuid=True), nullable=True)
    
    notes = Column(Text, nullable=True)
    ai_generated = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    hiring_plan = relationship("HiringPlan", back_populates="planned_headcounts")


class ImportJob(Base):
    """
    Import job record for tracking file imports.
    Tracks the status and results of spreadsheet imports.
    """
    __tablename__ = "import_jobs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hiring_plan_id = Column(UUID(as_uuid=True), ForeignKey("hiring_plans.id"), nullable=False)
    
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    
    status = Column(String(50), default="pending")
    
    total_rows = Column(Integer, default=0)
    imported_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    
    errors = Column(JSON, default=[])
    column_mapping = Column(JSON, default={})
    ai_suggestions = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    hiring_plan = relationship("HiringPlan", back_populates="import_jobs")


class WorkforceEntry(Base):
    """
    Simple workforce entry for monthly planning by department.
    Used for the admin panel workforce planning UI.
    """
    __tablename__ = "workforce_entries"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # WT-2022 P0.WORK: nullable=True por ora (legacy rows pré-fix).
    # Repository (WorkforceRepository) enforça company_id em TODAS as queries
    # via WHERE/setter — defense em camada de service. TODO migration:
    # backfill legacy rows + alterar para nullable=False.
    # WT-2022 P0.WORK migration 162 (2026-05-21): NOT NULL aplicado no DB. Python model alinhado.
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    year = Column(Integer, nullable=False)
    month = Column(String(10), nullable=False)
    department = Column(String(100), nullable=False)
    
    planned = Column(Integer, default=0)
    actual = Column(Integer, default=0)
    ai_suggestion = Column(Integer, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert entry to dictionary."""
        return {
            "id": str(self.id),
            "year": self.year,
            "month": self.month,
            "department": self.department,
            "planned": self.planned,
            "actual": self.actual,
            "ai_suggestion": self.ai_suggestion,
            "notes": self.notes,
        }
