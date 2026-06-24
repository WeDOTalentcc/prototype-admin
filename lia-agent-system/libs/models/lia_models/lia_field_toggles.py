"""
LIA Field Toggles model for company-specific field configuration.
Allows companies to enable/disable specific fields for AI/LLM consumption in the wizard.

IMPORTANT: Toggle controls AI DATA CONSUMPTION only, not UI visibility.
- is_active=True: AI agents will consume this field's data from company config
- is_active=False: AI agents will NOT consume this data, but use fallback strategies
  (job history, market benchmarks) instead. Field still appears in wizard UI.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class LiaFieldToggle(Base):
    """
    Represents a field toggle configuration for a company.
    Controls whether a specific field's data is consumed by AI/LLM agents.
    
    When is_active=False:
    - Field still appears in wizard UI
    - AI agents use fallback strategies (job history, market benchmarks)
    - comment field provides additional context/instructions for agents
    """
    __tablename__ = "lia_field_toggles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False, index=True)
    
    field_key = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    comment = Column(Text, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'field_key', name='uq_company_field_toggle'),
    {"extend_existing": True}, )


FALLBACK_STRATEGIES = {
    "job_history": "Buscar padrões do histórico de vagas da empresa",
    "market_benchmark": "Usar benchmarks de mercado para a posição/setor",
    "role_inference": "Inferir baseado no título e senioridade da vaga",
    "skip": "Não incluir este dado nas sugestões"
}


FIELD_FALLBACK_CONFIG = {
    "seniority_levels": ["job_history", "market_benchmark"],
    "work_model": ["job_history", "market_benchmark"],
    "hybrid_days_onsite": ["job_history", "market_benchmark"],
    "employment_types": ["job_history", "market_benchmark"],
    "salary_ranges": ["job_history", "market_benchmark"],
    "trade_name": ["skip"],
    "industry": ["skip"],
    "website": ["skip"],
    "linkedin_url": ["skip"],
    "company_size": ["skip"],
    "employee_count": ["skip"],
    "founded_year": ["skip"],
    "mission": ["skip"],
    "vision": ["skip"],
    "values": ["skip"],
    "core_competencies": ["job_history", "role_inference"],
    "engineering_culture": ["skip"],
    "default_languages": ["job_history", "market_benchmark"],
    "company_big_five": ["skip"],
    "departments": ["job_history"],
    "behavioral_competencies": ["job_history", "role_inference", "market_benchmark"],
    "growth_opportunities": ["skip"],
    "dei_initiatives": ["skip"],
    "sustainability": ["skip"],
    "social_impact": ["skip"],
    "evp_bullets": ["skip"],
    "tech_stack": ["job_history", "role_inference", "market_benchmark"],
    "benefits": ["job_history", "market_benchmark"],
    "locations": ["job_history"],
    "pipeline": ["job_history"],
    "eligibility_questions": ["job_history", "role_inference"],
    "headcount_planning": ["skip"],
    "leadership_style": ["skip"],
    "team_dynamics": ["skip"],
    "variable_compensation": ["job_history", "market_benchmark"],
    "compensation_policies": ["job_history", "skip"],
    "company_description": ["skip"],
    "headquarters": ["skip"],
    "policy_instructions": ["skip"],
    # Per-channel screening AI toggles — "skip" = channel disabled, IA not active for it
    "screening_channel_chat_web": ["skip"],
    "screening_channel_whatsapp": ["skip"],
    "screening_channel_phone_pstn": ["skip"],
    "screening_channel_voice_web": ["skip"],
}


DEFAULT_FIELD_TOGGLES = [
    {"field_key": "seniority_levels", "is_active": True},
    {"field_key": "work_model", "is_active": True},
    {"field_key": "hybrid_days_onsite", "is_active": True},
    {"field_key": "employment_types", "is_active": True},
    {"field_key": "salary_ranges", "is_active": True},
    {"field_key": "trade_name", "is_active": True},
    {"field_key": "industry", "is_active": True},
    {"field_key": "website", "is_active": True},
    {"field_key": "linkedin_url", "is_active": True},
    {"field_key": "company_size", "is_active": True},
    {"field_key": "employee_count", "is_active": True},
    {"field_key": "founded_year", "is_active": True},
    {"field_key": "mission", "is_active": True},
    {"field_key": "vision", "is_active": True},
    {"field_key": "values", "is_active": True},
    {"field_key": "core_competencies", "is_active": True},
    {"field_key": "engineering_culture", "is_active": True},
    {"field_key": "default_languages", "is_active": True},
    {"field_key": "company_big_five", "is_active": True},
    {"field_key": "departments", "is_active": True},
    {"field_key": "behavioral_competencies", "is_active": True},
    {"field_key": "growth_opportunities", "is_active": True},
    {"field_key": "dei_initiatives", "is_active": True},
    {"field_key": "sustainability", "is_active": True},
    {"field_key": "social_impact", "is_active": True},
    {"field_key": "evp_bullets", "is_active": True},
    {"field_key": "tech_stack", "is_active": True},
    {"field_key": "benefits", "is_active": True},
    {"field_key": "locations", "is_active": True},
    {"field_key": "pipeline", "is_active": True},
    {"field_key": "eligibility_questions", "is_active": True},
    {"field_key": "headcount_planning", "is_active": True},
    {"field_key": "leadership_style", "is_active": True},
    {"field_key": "team_dynamics", "is_active": True},
    {"field_key": "variable_compensation", "is_active": True},
    {"field_key": "compensation_policies", "is_active": True},
    {"field_key": "company_description", "is_active": True},
    {"field_key": "headquarters", "is_active": True},
    {"field_key": "policy_instructions", "is_active": True},
    # Per-channel screening AI toggles (company-level defaults)
    {"field_key": "screening_channel_chat_web", "is_active": True},
    {"field_key": "screening_channel_whatsapp", "is_active": True},
    {"field_key": "screening_channel_phone_pstn", "is_active": False},
    {"field_key": "screening_channel_voice_web", "is_active": False},
]
