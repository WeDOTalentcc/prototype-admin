"""
Job Pattern models for learning from historical job creation data.

Enables LIA to:
- Recognize patterns from similar job titles/departments
- Learn optimal salary ranges per role/location
- Suggest skills based on successful hires
- Predict time-to-fill based on job characteristics
- Semantic search for similar jobs using pgvector
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector

from lia_config.database import Base

EMBEDDING_DIMENSION = 768


class JobPattern(Base):
    """
    Patterns learned from historical job creation and outcomes.
    
    Captures successful patterns for:
    - Job titles and their typical requirements
    - Salary ranges by role/location/seniority
    - Skills commonly required together
    - Time-to-fill predictions
    """
    __tablename__ = "job_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    pattern_type = Column(String(50), nullable=False, index=True)
    pattern_key = Column(String(255), nullable=False, index=True)
    
    job_title_normalized = Column(String(255), nullable=True, index=True)
    department = Column(String(100), nullable=True, index=True)
    seniority = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    work_model = Column(String(50), nullable=True)
    
    sample_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    avg_salary_min = Column(Float, nullable=True)
    avg_salary_max = Column(Float, nullable=True)
    salary_percentile_25 = Column(Float, nullable=True)
    salary_percentile_75 = Column(Float, nullable=True)
    
    common_skills = Column(ARRAY(String), default=list)
    skill_frequency = Column(JSON, default=dict)
    common_behavioral = Column(ARRAY(String), default=list)
    behavioral_frequency = Column(JSON, default=dict)
    
    avg_time_to_fill = Column(Integer, nullable=True)
    median_time_to_fill = Column(Integer, nullable=True)
    time_to_fill_samples = Column(JSON, default=list)
    
    common_benefits = Column(ARRAY(String), default=list)
    common_languages = Column(ARRAY(String), default=list)
    
    success_profiles = Column(JSON, default=list)
    
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)
    
    is_active = Column(Boolean, default=True)
    confidence = Column(Float, default=0.3)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sample_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_job_pattern_lookup', 'company_id', 'pattern_type', 'pattern_key'),
        Index('idx_job_pattern_title', 'company_id', 'job_title_normalized'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "pattern_type": self.pattern_type,
            "pattern_key": self.pattern_key,
            "job_title_normalized": self.job_title_normalized,
            "department": self.department,
            "seniority": self.seniority,
            "location": self.location,
            "work_model": self.work_model,
            "sample_count": self.sample_count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
            "avg_salary_min": self.avg_salary_min,
            "avg_salary_max": self.avg_salary_max,
            "salary_percentile_25": self.salary_percentile_25,
            "salary_percentile_75": self.salary_percentile_75,
            "common_skills": self.common_skills or [],
            "skill_frequency": self.skill_frequency or {},
            "common_behavioral": self.common_behavioral or [],
            "behavioral_frequency": self.behavioral_frequency or {},
            "avg_time_to_fill": self.avg_time_to_fill,
            "median_time_to_fill": self.median_time_to_fill,
            "common_benefits": self.common_benefits or [],
            "common_languages": self.common_languages or [],
            "success_profiles": self.success_profiles or [],
            "is_active": self.is_active,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def update_confidence(self) -> float:
        """Update confidence based on sample size."""
        if self.sample_count < 3:
            self.confidence = 0.2
        elif self.sample_count < 5:
            self.confidence = 0.4
        elif self.sample_count < 10:
            self.confidence = 0.6
        elif self.sample_count < 20:
            self.confidence = 0.8
        else:
            self.confidence = min(0.95, 0.8 + (self.sample_count - 20) * 0.005)
        return self.confidence
    
    def calculate_success_rate(self) -> float:
        """Calculate and update success rate."""
        if self.sample_count == 0:
            return 0.0
        self.success_rate = self.success_count / self.sample_count
        return self.success_rate


class SalaryBenchmark(Base):
    """
    Salary benchmarks learned from company hiring data.
    
    Provides:
    - Market-competitive salary ranges
    - Location-based adjustments
    - Seniority progressions
    """
    __tablename__ = "salary_benchmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    job_title_normalized = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    seniority = Column(String(50), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    work_model = Column(String(50), nullable=True)
    
    sample_count = Column(Integer, default=0)
    
    min_salary = Column(Float, nullable=True)
    max_salary = Column(Float, nullable=True)
    avg_salary = Column(Float, nullable=True)
    median_salary = Column(Float, nullable=True)
    
    percentile_10 = Column(Float, nullable=True)
    percentile_25 = Column(Float, nullable=True)
    percentile_50 = Column(Float, nullable=True)
    percentile_75 = Column(Float, nullable=True)
    percentile_90 = Column(Float, nullable=True)
    
    salary_samples = Column(JSON, default=list)
    
    currency = Column(String(10), default="BRL")
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_salary_benchmark_lookup', 'company_id', 'job_title_normalized', 'seniority'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "job_title_normalized": self.job_title_normalized,
            "department": self.department,
            "seniority": self.seniority,
            "location": self.location,
            "work_model": self.work_model,
            "sample_count": self.sample_count,
            "salary_range": {
                "min": self.min_salary,
                "max": self.max_salary,
                "avg": self.avg_salary,
                "median": self.median_salary,
            },
            "percentiles": {
                "p10": self.percentile_10,
                "p25": self.percentile_25,
                "p50": self.percentile_50,
                "p75": self.percentile_75,
                "p90": self.percentile_90,
            },
            "currency": self.currency,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class SkillCluster(Base):
    """
    Clusters of skills that commonly appear together.
    
    Enables:
    - Skill recommendations based on existing skills
    - Identification of missing skills
    - Skill synergy detection
    """
    __tablename__ = "skill_clusters"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    cluster_name = Column(String(255), nullable=False)
    cluster_type = Column(String(50), nullable=False)
    
    core_skills = Column(ARRAY(String), default=list)
    related_skills = Column(ARRAY(String), default=list)
    
    skill_cooccurrence = Column(JSON, default=dict)
    
    job_titles = Column(ARRAY(String), default=list)
    departments = Column(ARRAY(String), default=list)
    
    sample_count = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "cluster_name": self.cluster_name,
            "cluster_type": self.cluster_type,
            "core_skills": self.core_skills or [],
            "related_skills": self.related_skills or [],
            "skill_cooccurrence": self.skill_cooccurrence or {},
            "job_titles": self.job_titles or [],
            "departments": self.departments or [],
            "sample_count": self.sample_count,
            "is_active": self.is_active,
        }


class JobEmbedding(Base):
    """
    Vector embeddings for job vacancies enabling semantic search.
    
    Enables:
    - Finding similar jobs by meaning (not just keywords)
    - Fast Track suggestions based on semantically similar past jobs
    - Cross-department pattern recognition
    """
    __tablename__ = "job_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    draft_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    job_title = Column(String(255), nullable=False)
    job_title_normalized = Column(String(255), nullable=True, index=True)
    department = Column(String(100), nullable=True)
    seniority = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    work_model = Column(String(50), nullable=True)
    
    description_summary = Column(Text, nullable=True)
    skills = Column(ARRAY(String), default=list)
    behavioral_competencies = Column(ARRAY(String), default=list)
    
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)
    embedding_text = Column(Text, nullable=True)
    embedding_provider = Column(String(50), nullable=True, comment="Provider that generated this vector (gemini, openai, etc.)")
    embedding_model = Column(String(100), nullable=True, comment="Model used (e.g. text-embedding-004, text-embedding-3-small)")

    outcome_status = Column(String(50), nullable=True)
    time_to_fill_days = Column(Integer, nullable=True)
    hire_quality_score = Column(Float, nullable=True)
    
    metadata_json = Column(JSON, nullable=True, default=dict)
    
    is_template = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_job_embedding_company', 'company_id', 'is_active'),
        Index('idx_job_embedding_title', 'company_id', 'job_title_normalized'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "job_id": str(self.job_id) if self.job_id else None,
            "job_title": self.job_title,
            "department": self.department,
            "seniority": self.seniority,
            "location": self.location,
            "work_model": self.work_model,
            "skills": self.skills or [],
            "behavioral_competencies": self.behavioral_competencies or [],
            "outcome_status": self.outcome_status,
            "time_to_fill_days": self.time_to_fill_days,
            "is_template": self.is_template,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @staticmethod
    def create_embedding_text(
        job_title: str,
        department: str = None,
        seniority: str = None,
        location: str = None,
        skills: list = None,
        behavioral: list = None,
        description: str = None
    ) -> str:
        """Create text representation for embedding generation."""
        parts = [f"Job Title: {job_title}"]
        
        if department:
            parts.append(f"Department: {department}")
        if seniority:
            parts.append(f"Seniority: {seniority}")
        if location:
            parts.append(f"Location: {location}")
        if skills:
            parts.append(f"Technical Skills: {', '.join(skills[:15])}")
        if behavioral:
            parts.append(f"Behavioral Competencies: {', '.join(behavioral[:10])}")
        if description:
            parts.append(f"Description: {description[:500]}")
        
        return " | ".join(parts)
