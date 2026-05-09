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


# ---------------------------------------------------------------------------
# Default Brazilian compensation policy templates
# ---------------------------------------------------------------------------

DEFAULT_BR_COMPENSATION_TEMPLATES: list[dict] = [
    {
        "name": "Política Padrão — Engenharia",
        "policy_type": "hierarchical_bands",
        "currency": "BRL",
        "applicable_departments": ["Engenharia", "Tecnologia"],
        "applicable_seniority": ["junior", "pleno", "senior"],
        "salary_bands": [
            {"level": "junior", "min": 4000, "max": 7000},
            {"level": "pleno", "min": 7000, "max": 12000},
            {"level": "senior", "min": 12000, "max": 20000},
        ],
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Política Padrão — Comercial",
        "policy_type": "mixed",
        "currency": "BRL",
        "applicable_departments": ["Vendas", "Comercial"],
        "applicable_seniority": ["junior", "pleno", "senior"],
        "salary_bands": [
            {"level": "junior", "min": 2500, "max": 4000},
            {"level": "pleno", "min": 4000, "max": 8000},
            {"level": "senior", "min": 8000, "max": 15000},
        ],
        "variable_compensation": {
            "items": [{"kind": "commission", "percentage": 5.0, "frequency": "monthly"}]
        },
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Política Padrão — Produto",
        "policy_type": "hierarchical_bands",
        "currency": "BRL",
        "applicable_departments": ["Produto"],
        "applicable_seniority": ["pleno", "senior"],
        "salary_bands": [
            {"level": "pleno", "min": 8000, "max": 14000},
            {"level": "senior", "min": 14000, "max": 22000},
        ],
        "is_active": True,
        "is_default": True,
    },
]
