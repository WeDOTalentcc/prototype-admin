"""
Company Culture Profile models for automatic organizational profile analysis.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from lia_config.database import Base


class CompanyCultureProfile(Base):
    """
    Company culture profile extracted from website analysis.
    Contains mission, vision, values, EVP, and organizational Big Five scores.
    """
    __tablename__ = "company_culture_profiles"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    mission = Column(Text, nullable=True)
    vision = Column(Text, nullable=True)
    # NOT NULL + server_default enforced by alembic 130_culture_profile_defaults_not_null
    values = Column(ARRAY(String), nullable=False, server_default="{}", default=list)
    evp_bullets = Column(ARRAY(String), nullable=False, server_default="{}", default=list)
    core_competencies = Column(ARRAY(String), nullable=False, server_default="{}", default=list)  # Behavioral competencies extracted from website
    culture_description = Column(Text, nullable=True)
    
    website_url = Column(String(500), nullable=False)
    linkedin_url = Column(String(500), nullable=True)
    analyzed_pages = Column(ARRAY(String), nullable=False, server_default="{}", default=list)
    
    # Company info from LinkedIn/website
    industry = Column(String(200), nullable=True)
    employee_count = Column(String(50), nullable=True)  # e.g., "501-1000"
    company_size = Column(String(50), nullable=True)  # e.g., "Medium", "Large"
    headquarters = Column(String(300), nullable=True)
    locations = Column(ARRAY(String), nullable=False, server_default="{}", default=list)
    founded_year = Column(Integer, nullable=True)
    
    # Work culture details
    work_model = Column(String(100), nullable=True)  # e.g., "Hybrid", "Remote", "On-site"
    growth_opportunities = Column(Text, nullable=True)
    team_dynamics = Column(Text, nullable=True)
    leadership_style = Column(Text, nullable=True)
    
    # DEI & Sustainability
    dei_initiatives = Column(Text, nullable=True)
    sustainability = Column(Text, nullable=True)
    social_impact = Column(Text, nullable=True)
    
    # Tech culture (for tech companies)
    tech_stack = Column(ARRAY(String), nullable=False, server_default="{}", default=list)
    engineering_culture = Column(Text, nullable=True)
    
    # Default languages for job vacancies
    default_languages = Column(ARRAY(String), nullable=False, server_default="{}", default=list)
    
    openness_score = Column(Integer, nullable=False, server_default="50", default=50)
    conscientiousness_score = Column(Integer, nullable=False, server_default="50", default=50)
    extraversion_score = Column(Integer, nullable=False, server_default="50", default=50)
    agreeableness_score = Column(Integer, nullable=False, server_default="50", default=50)
    stability_score = Column(Integer, nullable=False, server_default="50", default=50)
    
    source = Column(String(20), default="auto")
    confidence_score = Column(Float, default=0.0)
    raw_llm_response = Column(Text, nullable=True)

    # Fase 5.1 (2026-06-04) — Context Center HITL approval gate. Auto profiles
    # (source='auto', scrape+LLM) must be human-approved before feeding agent
    # prompts (LGPD/bias). Human-authored profiles bypass via source != 'auto'.
    is_approved = Column(Boolean, nullable=False, server_default="false", default=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    last_analysis_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CultureAnalysisJob(Base):
    """
    Track async culture analysis jobs.
    """
    __tablename__ = "culture_analysis_jobs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    website_url = Column(String(500), nullable=False)
    status = Column(String(50), default="pending")
    progress = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)
    
    error_message = Column(Text, nullable=True)
    result_profile_id = Column(UUID(as_uuid=True), nullable=True)
    
    pages_discovered = Column(Integer, default=0)
    pages_scraped = Column(Integer, default=0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
