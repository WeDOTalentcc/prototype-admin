"""
Company Setup models for platform configuration.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class CompanyProfile(Base):
    """
    Main company profile and general information.
    Core of the Phase 0 Setup & Calibration.
    """
    __tablename__ = "company_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=True, unique=True, index=True)
    
    name = Column(String(255), nullable=False)
    trading_name = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    cnpj = Column(String(18), nullable=True)
    industry = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)
    founded_year = Column(Integer, nullable=True)
    
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    
    headquarters_city = Column(String(100), nullable=True)
    headquarters_state = Column(String(100), nullable=True)
    headquarters_country = Column(String(100), default="Brasil")
    address = Column(Text, nullable=True)
    
    main_phone = Column(String(50), nullable=True)
    hr_phone = Column(String(50), nullable=True)
    main_email = Column(String(255), nullable=True)
    hr_email = Column(String(255), nullable=True)
    
    linkedin_url = Column(String(500), nullable=True)
    glassdoor_url = Column(String(500), nullable=True)
    
    employee_count = Column(Integer, nullable=True)
    revenue_range = Column(String(100), nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    culture_analyzed = Column(Boolean, default=False)
    culture_analysis_date = Column(DateTime, nullable=True)
    culture_insights = Column(JSON, default={})
    
    ats_history_analyzed = Column(Boolean, default=False)
    ats_analysis_date = Column(DateTime, nullable=True)
    ats_insights = Column(JSON, default={})
    
    additional_data = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    benefits = relationship("Benefit", back_populates="company", cascade="all, delete-orphan")
    culture_values = relationship("CultureValue", back_populates="company", cascade="all, delete-orphan")
    compensation_policies = relationship("CompensationPolicy", back_populates="company", cascade="all, delete-orphan")


class Department(Base):
    """
    Company departments/areas with hierarchical structure.
    """
    __tablename__ = "departments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    manager_name = Column(String(255), nullable=True)
    manager_email = Column(String(255), nullable=True)
    manager_title = Column(String(255), nullable=True)
    manager_phone = Column(String(50), nullable=True)
    manager_id = Column(UUID(as_uuid=True), nullable=True)
    
    headcount = Column(Integer, default=0)
    budget_annual = Column(Float, nullable=True)
    
    cost_center = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    hiring_priority = Column(String(50), default="normal")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("CompanyProfile", back_populates="departments")
    children = relationship("Department", backref="parent", remote_side=[id])
    members = relationship("DepartmentMember", back_populates="department", cascade="all, delete-orphan")


class DepartmentMember(Base):
    """
    Members/employees within a department for org chart building.
    """
    __tablename__ = "department_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    linkedin_url = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    level = Column(String(50), default="outros")
    
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    department = relationship("Department", back_populates="members")


class Benefit(Base):
    """
    Company benefits offered to employees.
    Supports: monetary (R$), percentage (%), or informative (description only)
    """
    __tablename__ = "benefits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    
    icon = Column(String(50), nullable=True)
    value = Column(Float, nullable=True)
    value_type = Column(String(50), default="monetary")
    value_details = Column(Text, nullable=True)
    percentage_value = Column(Float, nullable=True)
    
    applicable_to = Column(ARRAY(String), default=[])
    seniority_levels = Column(ARRAY(String), default=[])
    contract_types = Column(ARRAY(String), default=[])
    departments = Column(JSONB, default=[])
    
    waiting_period_days = Column(Integer, default=0)
    
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_highlighted = Column(Boolean, default=False)
    is_discount = Column(Boolean, default=False)
    
    order = Column(Integer, default=0)
    
    provider = Column(String(255), nullable=True)
    provider_contact = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("CompanyProfile", back_populates="benefits")


class CultureValue(Base):
    """
    Company culture values and principles.
    """
    __tablename__ = "culture_values"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="value")
    
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    
    behavioral_indicators = Column(ARRAY(String), default=[])
    interview_questions = Column(ARRAY(String), default=[])
    
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    ai_generated = Column(Boolean, default=False)
    source = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("CompanyProfile", back_populates="culture_values")


class IdealProfile(Base):
    """
    Ideal candidate profiles by role/department.
    Generated by AI analysis of company culture, historical hiring, and job requirements.
    """
    __tablename__ = "ideal_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    role_type = Column(String(100), nullable=True)
    seniority_level = Column(String(50), nullable=True)
    
    technical_requirements = Column(JSON, default={})
    behavioral_requirements = Column(JSON, default={})
    experience_requirements = Column(JSON, default={})
    education_requirements = Column(JSON, default={})
    
    big_five_ideal = Column(JSON, default={})
    
    evaluation_weights = Column(JSON, default={})
    
    mandatory_skills = Column(ARRAY(String), default=[])
    preferred_skills = Column(ARRAY(String), default=[])
    languages = Column(JSON, default={})
    
    salary_range_min = Column(Float, nullable=True)
    salary_range_max = Column(Float, nullable=True)
    
    culture_fit_criteria = Column(JSON, default={})
    
    ai_generated = Column(Boolean, default=False)
    ai_analysis_date = Column(DateTime, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    
    validated = Column(Boolean, default=False)
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class BenefitTemplate(Base):
    """
    Pre-registered benefit templates for recruiters.
    Global templates not linked to any specific company.
    """
    __tablename__ = "benefit_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlobalSearchSettings(Base):
    """
    Global search configuration settings per company.
    """
    __tablename__ = "global_search_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=True, index=True)
    
    default_limit = Column(Integer, default=50)
    search_type = Column(String(20), default='fast')
    show_emails = Column(Boolean, default=False)
    show_phone_numbers = Column(Boolean, default=False)
    high_freshness = Column(Boolean, default=False)
    auto_expand_global = Column(Boolean, default=False)
    confirm_before_search = Column(Boolean, default=True)
    global_search_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Approver(Base):
    """
    Approval workflow levels for job vacancies and hiring decisions.
    """
    __tablename__ = "approvers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    
    level = Column(Integer, nullable=False, default=1)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
