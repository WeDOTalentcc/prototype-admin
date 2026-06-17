"""
Job Template models for the Fast Track system.

Provides pre-configured job templates that enable:
- Fast Track job creation (15 min → 3 min)
- System templates (480+ templates across 13 areas)
- Company-specific templates (learned from usage)
- AI enrichment for missing fields
- Learning from historical job creation
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from lia_config.database import Base


class JobTemplate(Base):
    """
    Pre-configured job templates for Fast Track creation.
    
    Templates can be:
    - System templates (is_system=True, company_id=NULL): Global templates available to all
    - Company templates (is_system=False, company_id=X): Learned from company's job creation
    
    Each template contains:
    - Basic info (title, category, seniority)
    - Default skills and competencies
    - Responsibilities and requirements
    - Salary benchmarks
    - Alternative titles for matching
    """
    __tablename__ = "job_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    # WT-2022 P0.TENANT: TENANT-EXEMPT - is_system templates globais (company_id NULL quando is_system=True; documentado linhas 24-25)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    parent_template_id = Column(UUID(as_uuid=True), ForeignKey('job_templates.id'), nullable=True)
    
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    title_normalized = Column(String(200), nullable=False, index=True)
    title_alternatives = Column(ARRAY(String), default=list)
    
    seniority = Column(String(20), nullable=False, index=True)
    
    default_description = Column(Text, nullable=True)
    default_responsibilities = Column(ARRAY(String), default=list)
    default_requirements = Column(Text, nullable=True)
    default_nice_to_have = Column(Text, nullable=True)
    default_education = Column(ARRAY(String), default=list)
    default_certifications = Column(ARRAY(String), default=list)
    default_languages = Column(ARRAY(String), default=list)
    
    default_skills = Column(JSON, default=list)
    default_behavioral = Column(JSON, default=list)
    
    salary_range_min = Column(Integer, nullable=True)
    salary_range_max = Column(Integer, nullable=True)
    salary_currency = Column(String(3), default="BRL")
    
    work_model = Column(String(20), default="hybrid")
    employment_type = Column(String(20), default="clt")
    experience_years_min = Column(Integer, nullable=True)
    experience_years_max = Column(Integer, nullable=True)
    
    is_system = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    popularity_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    
    template_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    __table_args__ = (
        Index('idx_template_category', 'category', 'subcategory'),
        Index('idx_template_company', 'company_id', 'is_active'),
        Index('idx_template_system', 'is_system', 'is_active', 'category'),
        Index('idx_template_popularity', 'popularity_score'),
        Index('idx_template_title_search', 'title_normalized', 'is_active'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "parent_template_id": str(self.parent_template_id) if self.parent_template_id else None,
            "category": self.category,
            "subcategory": self.subcategory,
            "title": self.title,
            "title_normalized": self.title_normalized,
            "title_alternatives": self.title_alternatives or [],
            "seniority": self.seniority,
            "default_description": self.default_description,
            "default_responsibilities": self.default_responsibilities or [],
            "default_requirements": self.default_requirements,
            "default_nice_to_have": self.default_nice_to_have,
            "default_education": self.default_education or [],
            "default_certifications": self.default_certifications or [],
            "default_languages": self.default_languages or [],
            "default_skills": self.default_skills or [],
            "default_behavioral": self.default_behavioral or [],
            "salary_range": {
                "min": self.salary_range_min,
                "max": self.salary_range_max,
                "currency": self.salary_currency,
            },
            "work_model": self.work_model,
            "employment_type": self.employment_type,
            "experience_years": {
                "min": self.experience_years_min,
                "max": self.experience_years_max,
            },
            "is_system": self.is_system,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "popularity_score": self.popularity_score,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_wizard_data(self) -> dict:
        """Convert to wizard-compatible format for Fast Track."""
        return {
            "title": self.title,
            "department": self.subcategory,
            "seniority": self.seniority,
            "description": self.default_description,
            "responsibilities": self.default_responsibilities or [],
            "requirements": self.default_requirements,
            "niceToHave": self.default_nice_to_have,
            "education": self.default_education or [],
            "certifications": self.default_certifications or [],
            "languages": self.default_languages or [],
            "technicalSkills": [
                {
                    "id": f"skill-{i}",
                    "name": skill.get("name", ""),
                    "category": skill.get("category", "technical"),
                    "level": skill.get("level", "intermediate"),
                    "weight": skill.get("weight", 1.0),
                    "required": skill.get("required", True),
                }
                for i, skill in enumerate(self.default_skills or [])
            ],
            "behavioralCompetencies": [
                {
                    "id": f"comp-{i}",
                    "name": comp.get("name", ""),
                    "weight": comp.get("weight", 1.0),
                    "justification": comp.get("justification", ""),
                    "enabled": True,
                }
                for i, comp in enumerate(self.default_behavioral or [])
            ],
            "salaryInfo": {
                "min": self.salary_range_min,
                "max": self.salary_range_max,
                "currency": self.salary_currency,
                "showOnPosting": False,
            },
            "workModel": self.work_model,
            "employmentType": self.employment_type,
            "experienceYears": {
                "min": self.experience_years_min,
                "max": self.experience_years_max,
            },
        }
    
    def increment_usage(self):
        """Increment usage count and update popularity."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self._update_popularity()
    
    def _update_popularity(self):
        """Update popularity score based on usage and recency."""
        if not self.last_used_at:
            self.popularity_score = 0.0
            return
        
        days_since_used = (datetime.utcnow() - self.last_used_at).days
        recency_factor = max(0.1, 1.0 - (days_since_used / 365))
        
        usage_factor = min(1.0, self.usage_count / 100)
        
        self.popularity_score = (recency_factor * 0.4) + (usage_factor * 0.6)
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """Normalize job title for search and matching."""
        import re
        normalized = title.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        replacements = {
            'sr': 'senior',
            'jr': 'junior',
            'pl': 'pleno',
            'dev': 'desenvolvedor',
            'eng': 'engenheiro',
            'analista de': 'analista',
        }
        for short, full in replacements.items():
            normalized = normalized.replace(f' {short} ', f' {full} ')
            normalized = normalized.replace(f'{short} ', f'{full} ')
        
        return normalized.strip()


class TemplateCategory(Base):
    """
    Categories and subcategories for organizing templates.
    
    Provides hierarchical organization:
    - Category: 'tecnologia', 'financas', 'rh'
    - Subcategory: 'desenvolvimento', 'dados', 'infra'
    """
    __tablename__ = "template_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    name = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey('template_categories.id'), nullable=True)
    
    sort_order = Column(Integer, default=0)
    template_count = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_category_parent', 'parent_id'),
        Index('idx_category_sort', 'sort_order'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "sort_order": self.sort_order,
            "template_count": self.template_count,
            "is_active": self.is_active,
        }


class TemplateUsageLog(Base):
    """
    Logs template usage for learning and analytics.
    
    Tracks:
    - Which templates are used
    - How they are modified
    - Success metrics for templates
    """
    __tablename__ = "template_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    template_id = Column(UUID(as_uuid=True), ForeignKey('job_templates.id'), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    action = Column(String(50), nullable=False)
    
    fields_modified = Column(ARRAY(String), default=list)
    modifications_count = Column(Integer, default=0)
    
    time_to_complete_seconds = Column(Integer, nullable=True)
    completion_rate = Column(Float, nullable=True)
    
    feedback_rating = Column(Integer, nullable=True)
    feedback_text = Column(Text, nullable=True)
    
    session_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_usage_template_company', 'template_id', 'company_id'),
        Index('idx_usage_created', 'created_at'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "template_id": str(self.template_id),
            "company_id": str(self.company_id) if self.company_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "job_id": str(self.job_id) if self.job_id else None,
            "action": self.action,
            "fields_modified": self.fields_modified or [],
            "modifications_count": self.modifications_count,
            "time_to_complete_seconds": self.time_to_complete_seconds,
            "completion_rate": self.completion_rate,
            "feedback_rating": self.feedback_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
