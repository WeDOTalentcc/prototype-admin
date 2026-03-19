"""
Compensation Policy model for salary and bonus management.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class CompensationPolicy(Base):
    """
    Compensation policies defining salary ranges, bonus structures,
    and variable compensation by role/department/seniority.
    """
    __tablename__ = "compensation_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    role_pattern = Column(String(255), nullable=True)
    seniority_level = Column(String(100), nullable=True)
    
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_target = Column(Float, nullable=True)
    
    bonus_enabled = Column(Boolean, default=False)
    bonus_type = Column(String(100), nullable=True)
    bonus_min_pct = Column(Float, nullable=True)
    bonus_target_pct = Column(Float, nullable=True)
    bonus_max_pct = Column(Float, nullable=True)
    bonus_criteria = Column(JSON, default={})
    
    variable_compensation = Column(JSON, default={})
    
    total_comp_annual_min = Column(Float, nullable=True)
    total_comp_annual_max = Column(Float, nullable=True)
    
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime, nullable=True)
    effective_until = Column(DateTime, nullable=True)
    source = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    company = relationship("CompanyProfile", back_populates="compensation_policies")
