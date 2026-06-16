"""
Company Skills Catalog models for integrated skill management.

Provides persistent storage for:
- Company-specific skill catalogs (from Settings)
- Skill usage analytics and feedback
- Learning patterns for skill suggestions
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, Index, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

from lia_config.database import Base


class CompanySkillsCatalog(Base):
    """
    Catalog of skills configured by company in Settings.
    
    Integrates with:
    - TechStack from CompanyConfig
    - Behavioral competencies from company policies
    - Learning patterns from wizard usage
    """
    __tablename__ = "company_skills_catalog"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    skill_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(100), nullable=True)
    
    default_weight = Column(Integer, default=3)
    default_level = Column(String(50), default="Intermediário")
    is_required_default = Column(Boolean, default=False)
    
    description = Column(Text, nullable=True)
    aliases = Column(ARRAY(String), default=[])
    
    usage_count = Column(Integer, default=0)
    acceptance_rate = Column(Float, default=0.0)
    last_used_at = Column(DateTime, nullable=True)
    
    source = Column(String(50), default="manual")
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_skills_catalog_company_name', 'company_id', 'skill_name', unique=True),
        Index('idx_skills_catalog_category', 'company_id', 'category'),
        Index('idx_skills_catalog_active', 'company_id', 'is_active'),
        Index('idx_skills_catalog_usage', 'company_id', 'usage_count'),
    {"extend_existing": True}, )


class BehavioralCompetencyCatalog(Base):
    """
    Catalog of behavioral competencies configured by company.
    
    These are soft skills and cultural fit indicators that
    can be reused across job vacancies.
    """
    __tablename__ = "behavioral_competencies_catalog"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    justification = Column(Text, nullable=True)
    
    default_weight = Column(Integer, default=3)
    category = Column(String(100), nullable=True)
    
    usage_count = Column(Integer, default=0)
    acceptance_rate = Column(Float, default=0.0)
    last_used_at = Column(DateTime, nullable=True)
    
    wsi_questions = Column(JSON, default=[])
    evaluation_criteria = Column(JSON, default={})
    
    source = Column(String(50), default="manual")
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_behavioral_catalog_company_name', 'company_id', 'name', unique=True),
        Index('idx_behavioral_catalog_active', 'company_id', 'is_active'),
    {"extend_existing": True}, )


class SkillUsageAnalytics(Base):
    """
    Tracks how skills are used in job vacancies.
    
    Used for:
    - Silent feedback capture (learning loop)
    - Trend analysis
    - Suggestion improvement
    """
    __tablename__ = "skill_usage_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    skill_name = Column(String(255), nullable=False)
    skill_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=True)
    
    job_vacancy_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    job_draft_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    job_title = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    seniority = Column(String(50), nullable=True)
    
    source = Column(String(50), nullable=False)
    outcome = Column(String(20), nullable=False)
    
    original_weight = Column(Integer, nullable=True)
    final_weight = Column(Integer, nullable=True)
    original_level = Column(String(50), nullable=True)
    final_level = Column(String(50), nullable=True)
    was_required = Column(Boolean, nullable=True)
    
    suggestion_confidence = Column(Float, nullable=True)
    suggestion_reasoning = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_skill_usage_company', 'company_id'),
        Index('idx_skill_usage_skill', 'company_id', 'skill_name'),
        Index('idx_skill_usage_outcome', 'company_id', 'outcome'),
        Index('idx_skill_usage_job', 'job_vacancy_id'),
        Index('idx_skill_usage_date', 'created_at'),
    {"extend_existing": True}, )


class SkillSuggestionPattern(Base):
    """
    Learned patterns for skill suggestions.
    
    Generated from SkillUsageAnalytics to improve
    future suggestions based on company preferences.
    """
    __tablename__ = "skill_suggestion_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    pattern_type = Column(String(50), nullable=False)
    context_key = Column(String(255), nullable=False)
    
    skill_name = Column(String(255), nullable=False)
    skill_category = Column(String(50), nullable=True)
    
    suggested_weight = Column(Integer, nullable=True)
    suggested_level = Column(String(50), nullable=True)
    is_typically_required = Column(Boolean, default=False)
    
    sample_size = Column(Integer, default=0)
    acceptance_rate = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    
    context_data = Column(JSON, default={})
    
    is_promoted = Column(Boolean, default=False)
    last_computed_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_skill_pattern_company', 'company_id'),
        Index('idx_skill_pattern_type', 'company_id', 'pattern_type'),
        Index('idx_skill_pattern_context', 'company_id', 'context_key'),
        Index('idx_skill_pattern_confidence', 'company_id', 'confidence_score'),
        Index('idx_skill_pattern_promoted', 'company_id', 'is_promoted'),
    {"extend_existing": True}, )


SKILL_CATEGORIES = {
    "technical": {
        "language": "Linguagens de Programação",
        "framework": "Frameworks e Bibliotecas",
        "database": "Bancos de Dados",
        "tool": "Ferramentas e Plataformas",
        "infrastructure": "Infraestrutura e Cloud",
        "general": "Competências Técnicas Gerais"
    },
    "behavioral": {
        "leadership": "Liderança",
        "communication": "Comunicação",
        "problem_solving": "Resolução de Problemas",
        "teamwork": "Trabalho em Equipe",
        "adaptability": "Adaptabilidade",
        "analytical": "Pensamento Analítico"
    }
}

SKILL_SOURCES = {
    "company_catalog": "Catálogo da Empresa",
    "company_config": "Configurações",
    "market_benchmark": "Benchmark de Mercado",
    "learning_pattern": "Padrão Aprendido",
    "ats_history": "Histórico ATS",
    "llm_suggestion": "Sugestão IA",
    "manual": "Adicionado Manualmente"
}

SKILL_OUTCOMES = {
    "accepted": "Aceito sem modificação",
    "modified": "Aceito com modificação",
    "rejected": "Rejeitado"
}
