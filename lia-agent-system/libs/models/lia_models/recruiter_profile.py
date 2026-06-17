"""
Recruiter Profile models for personalization.

These models enable personalized wizard experience based on:
- Individual recruiter preferences and patterns
- Field-specific correction history
- Communication style preferences
- Privacy and transparency settings
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from lia_config.database import Base


REMINDER_ACTIONS = {
    "fill_now": "Recrutador escolheu preencher o campo com ajuda da LIA",
    "remind_later": "Recrutador escolheu ser lembrado depois",
    "dont_remind": "Recrutador escolheu não ser lembrado mais",
    "dismissed": "Recrutador descartou a notificação sem ação"
}


FIELD_IMPACT_DESCRIPTIONS = {
    "benefits": "A falta de benefícios cadastrados reduz a qualidade da descrição da vaga e pode impactar a atração de candidatos.",
    "tech_stack": "Sem o stack tecnológico definido, LIA não consegue sugerir habilidades técnicas relevantes.",
    "behavioral_competencies": "Competências comportamentais vazias limitam a geração de perguntas WSI e avaliação cultural.",
    "core_competencies": "Competências core não definidas afetam a avaliação de fit com a empresa.",
    "salary_ranges": "Faixas salariais não cadastradas impedem sugestões de remuneração competitiva.",
    "locations": "Localizações não definidas dificultam o matching geográfico de candidatos.",
    "work_model": "Modelo de trabalho não definido impacta filtros de candidatos (remoto/híbrido/presencial).",
    "departments": "Departamentos não cadastrados limitam a atribuição correta da vaga.",
    "eligibility_questions": "Perguntas de elegibilidade vazias podem resultar em triagem menos eficiente.",
    "seniority_levels": "Níveis de senioridade não definidos afetam benchmarks salariais e requisitos.",
    "employment_types": "Tipos de contratação não definidos (CLT, PJ) impactam expectativas de candidatos.",
}

DEFAULT_IMPACT_DESCRIPTION = "Este campo vazio pode reduzir a qualidade das sugestões da LIA."


class RecruiterProfile(Base):
    """
    Personalization profile for each recruiter.
    
    Tracks:
    - Usage statistics (jobs created, avg completion time)
    - Detected preferences (seniorities, departments)
    - Correction patterns (which fields are often corrected)
    - Interaction preferences (quick flow, detailed explanations)
    
    This data is used to personalize the wizard experience,
    adjusting defaults, confidence thresholds, and messaging.
    """
    __tablename__ = "recruiter_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_id = Column(String(255), nullable=False, unique=True, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    total_jobs_created = Column(Integer, default=0)
    total_corrections_made = Column(Integer, default=0)
    avg_completion_time_seconds = Column(Float, nullable=True)
    
    preferred_seniorities = Column(JSON, default=list)
    preferred_departments = Column(JSON, default=list)
    correction_patterns = Column(JSON, default=dict)
    
    confidence_threshold_adjustment = Column(Float, default=0.0)
    wizard_mode = Column(String(50), nullable=True)
    experience_level = Column(String(50), nullable=True)
    profile_version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_recruiter_profile_company', 'company_id'),
    {"extend_existing": True}, )
    
    @property
    def prefers_quick_flow(self) -> bool:
        """Derived from wizard_mode."""
        return self.wizard_mode == "quick"
    
    @property
    def prefers_detailed_explanations(self) -> bool:
        """Derived from wizard_mode."""
        return self.wizard_mode == "detailed"
    
    @property
    def fields_often_corrected(self) -> dict:
        """Derived from correction_patterns."""
        return self.correction_patterns or {}
    
    @property
    def uses_jd_import(self) -> bool:
        """Default value - to be implemented."""
        return False


class RecruiterFieldPreference(Base):
    """
    Field-specific preferences for each recruiter.
    
    Tracks how a recruiter interacts with each field:
    - Correction frequency and patterns
    - Preferred values and ranges
    - Custom confidence thresholds
    - Empty field reminder preferences (for "active toggle + empty field" scenario)
    
    This enables highly granular personalization at the field level.
    """
    __tablename__ = "recruiter_field_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_id = Column(String(255), nullable=False, index=True)
    recruiter_profile_id = Column(UUID(as_uuid=True), nullable=True)
    # TENANT-EXEMPT: RecruiterFieldPreference legacy; recruiter_id ja scope canonical
    company_id = Column(String(255), nullable=True, index=True)
    field_name = Column(String(100), nullable=False)
    
    correction_count = Column(Integer, default=0)
    total_encounters = Column(Integer, default=0)
    correction_rate = Column(Float, default=0.0)
    
    typical_corrections = Column(JSON, default=list)
    preferred_values = Column(JSON, default=list)
    value_range = Column(JSON, nullable=True)
    
    custom_threshold = Column(Float, nullable=True)
    always_ask = Column(Boolean, default=False)
    
    remind_me_empty_field = Column(Boolean, default=True)
    last_reminded_at = Column(DateTime, nullable=True)
    snooze_until = Column(DateTime, nullable=True)
    times_reminded = Column(Integer, default=0)
    times_filled_with_lia = Column(Integer, default=0)
    last_reminder_action = Column(String(50), nullable=True)
    
    last_correction_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_field_pref_recruiter_field', 'recruiter_id', 'field_name', unique=True),
        Index('ix_field_pref_company', 'company_id'),
    {"extend_existing": True}, )


class PersonalizationSettings(Base):
    """
    User-controllable personalization settings.
    
    Gives recruiters control over:
    - Whether personalization is enabled
    - Which data is used for personalization
    - Privacy preferences
    - Transparency preferences
    """
    __tablename__ = "personalization_settings"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_id = Column(String(255), nullable=False, unique=True, index=True)
    
    enable_personalization = Column(Boolean, default=True)
    use_correction_history = Column(Boolean, default=True)
    use_preference_detection = Column(Boolean, default=True)
    use_outcome_data = Column(Boolean, default=True)
    
    show_confidence_indicators = Column(Boolean, default=True)
    explain_suggestions = Column(Boolean, default=True)
    
    auto_approve_high_confidence = Column(Boolean, default=True)
    high_confidence_threshold = Column(Float, default=0.90)
    
    data_retention_months = Column(Integer, default=24)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProfileCalculationLog(Base):
    """
    Log of profile recalculations.
    
    Tracks when and why profiles are recalculated,
    what changed, and what triggered the recalculation.
    This provides transparency and debugging information.
    """
    __tablename__ = "profile_calculation_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    recruiter_profile_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    trigger = Column(String(50), nullable=False)
    jobs_analyzed = Column(Integer, default=0)
    corrections_analyzed = Column(Integer, default=0)
    outcomes_analyzed = Column(Integer, default=0)
    
    changes_detected = Column(JSON, default=list)
    
    previous_profile_snapshot = Column(JSON, nullable=True)
    new_profile_snapshot = Column(JSON, nullable=True)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_time_ms = Column(Integer, nullable=True)
