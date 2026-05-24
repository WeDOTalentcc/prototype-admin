"""
Imported Job Description models for ATS/HRIS data import.

Phase 1B of Learning Loop: Import JDs from external sources to enable
company-specific suggestions in the wizard.

Data Priority Order (highest to lowest):
1. Company Settings (Menu Configurações) - 100% precision
2. LIA Platform History - 95% precision
3. Imported JDs from ATS (this module) - 85% precision
4. Workforce Planning / HRIS - 80% precision
5. Full ETL + Datalakes - 75% precision
6. Curated Templates (662) - 70% precision (fallback)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import enum

from lia_config.database import Base


class ImportSource(str, enum.Enum):
    """Source of imported job description."""
    ATS_GUPY = "ats_gupy"
    ATS_PANDAPE = "ats_pandape"
    ATS_GREENHOUSE = "ats_greenhouse"
    ATS_LEVER = "ats_lever"
    ATS_OTHER = "ats_other"
    HRIS_SAP = "hris_sap"
    HRIS_WORKDAY = "hris_workday"
    HRIS_OTHER = "hris_other"
    SPREADSHEET = "spreadsheet"
    MANUAL_UPLOAD = "manual_upload"
    API_IMPORT = "api_import"


class ImportStatus(str, enum.Enum):
    """Status of import processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


class ProcessingStatus(str, enum.Enum):
    """Status of JD processing/parsing."""
    RAW = "raw"
    PARSED = "parsed"
    NORMALIZED = "normalized"
    ENRICHED = "enriched"
    FAILED = "failed"


class ImportedJobDescription(Base):
    """
    Stores job descriptions imported from ATS/HRIS systems.
    
    This is the core data source for Phase 1B learning:
    - Title (autocomplete + naming patterns)
    - Responsibilities (contextual suggestions)
    - Technical skills (custom catalog)
    - Behavioral competencies (custom catalog)
    - Salary (internal benchmarks)
    - Benefits (default packages)
    """
    __tablename__ = "imported_job_descriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    external_id = Column(String(255), nullable=True, index=True)
    source = Column(String(50), nullable=False, default=ImportSource.MANUAL_UPLOAD.value)
    import_batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    job_title_original = Column(String(500), nullable=False)
    job_title_normalized = Column(String(255), nullable=True, index=True)
    
    department = Column(String(100), nullable=True, index=True)
    area = Column(String(100), nullable=True)
    team = Column(String(100), nullable=True)
    
    seniority = Column(String(50), nullable=True, index=True)
    seniority_confidence = Column(Float, default=0.0)
    
    employment_type = Column(String(50), nullable=True)
    work_model = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    
    description_raw = Column(Text, nullable=True)
    description_parsed = Column(Text, nullable=True)
    
    responsibilities = Column(ARRAY(String), default=list)
    responsibilities_raw = Column(Text, nullable=True)
    
    technical_skills = Column(JSON, default=list)
    behavioral_competencies = Column(JSON, default=list)
    
    requirements_mandatory = Column(ARRAY(String), default=list)
    requirements_desirable = Column(ARRAY(String), default=list)
    
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="BRL")
    salary_period = Column(String(20), default="monthly")
    salary_confidential = Column(Boolean, default=False)
    
    benefits = Column(ARRAY(String), default=list)
    benefits_details = Column(JSON, default=dict)
    
    hiring_manager = Column(String(255), nullable=True)
    hiring_manager_email = Column(String(255), nullable=True)
    recruiter = Column(String(255), nullable=True)
    
    headcount = Column(Integer, default=1)
    
    job_status = Column(String(50), nullable=True)
    was_filled = Column(Boolean, nullable=True)
    candidates_count = Column(Integer, nullable=True)
    time_to_fill_days = Column(Integer, nullable=True)
    hired_candidate_id = Column(String(255), nullable=True)
    
    created_date_original = Column(DateTime, nullable=True)
    closed_date_original = Column(DateTime, nullable=True)
    
    processing_status = Column(String(50), default=ProcessingStatus.RAW.value)
    parsing_confidence = Column(Float, default=0.0)
    parsing_errors = Column(JSON, default=list)
    
    metadata_raw = Column(JSON, default=dict)
    
    is_used_for_learning = Column(Boolean, default=True)
    times_used_as_template = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_imported_jd_company_title', 'company_id', 'job_title_normalized'),
        Index('idx_imported_jd_company_dept', 'company_id', 'department'),
        Index('idx_imported_jd_company_source', 'company_id', 'source'),
        Index('idx_imported_jd_batch', 'import_batch_id'),
        Index('idx_imported_jd_learning', 'company_id', 'is_used_for_learning'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "external_id": self.external_id,
            "source": self.source,
            "job_title_original": self.job_title_original,
            "job_title_normalized": self.job_title_normalized,
            "department": self.department,
            "seniority": self.seniority,
            "employment_type": self.employment_type,
            "work_model": self.work_model,
            "location": self.location,
            "responsibilities": self.responsibilities or [],
            "technical_skills": self.technical_skills or [],
            "behavioral_competencies": self.behavioral_competencies or [],
            "requirements_mandatory": self.requirements_mandatory or [],
            "requirements_desirable": self.requirements_desirable or [],
            "salary": {
                "min": self.salary_min,
                "max": self.salary_max,
                "currency": self.salary_currency,
                "period": self.salary_period,
            } if self.salary_min or self.salary_max else None,
            "benefits": self.benefits or [],
            "hiring_manager": self.hiring_manager,
            "headcount": self.headcount,
            "job_status": self.job_status,
            "was_filled": self.was_filled,
            "time_to_fill_days": self.time_to_fill_days,
            "processing_status": self.processing_status,
            "parsing_confidence": self.parsing_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_wizard_suggestion(self) -> dict:
        """Convert to wizard-friendly suggestion format."""
        return {
            "source": "imported_jd",
            "source_id": str(self.id),
            "title": self.job_title_normalized or self.job_title_original,
            "department": self.department,
            "seniority": self.seniority,
            "employment_type": self.employment_type,
            "work_model": self.work_model,
            "location": self.location,
            "responsibilities": self.responsibilities or [],
            "technical_skills": self.technical_skills or [],
            "behavioral_competencies": self.behavioral_competencies or [],
            "salary_range": {
                "min": self.salary_min,
                "max": self.salary_max,
            } if self.salary_min or self.salary_max else None,
            "benefits": self.benefits or [],
            "confidence": self.parsing_confidence,
            "was_successful": self.was_filled,
            "original_date": self.created_date_original.isoformat() if self.created_date_original else None,
        }


class ImportBatch(Base):
    """
    Tracks batch imports from ATS/HRIS systems.
    
    Enables:
    - Progress tracking for large imports
    - Rollback of failed imports
    - Import history and auditing
    """
    __tablename__ = "import_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    source = Column(String(50), nullable=False)
    source_connection_id = Column(UUID(as_uuid=True), nullable=True)
    
    status = Column(String(50), default=ImportStatus.PENDING.value)
    
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    skipped_records = Column(Integer, default=0)
    
    import_config = Column(JSON, default=dict)
    
    errors = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_import_batch_company', 'company_id', 'status'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "source": self.source,
            "status": self.status,
            "progress": {
                "total": self.total_records,
                "processed": self.processed_records,
                "successful": self.successful_records,
                "failed": self.failed_records,
                "skipped": self.skipped_records,
                "percentage": round((self.processed_records / self.total_records * 100) if self.total_records > 0 else 0, 1),
            },
            "errors_count": len(self.errors or []),
            "warnings_count": len(self.warnings or []),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClientSkillCatalog(Base):
    """
    Company-specific skill catalog built from imported JDs.
    
    Aggregates skills from all imported JDs to provide:
    - Custom autocomplete for skills
    - Frequency-based suggestions
    - Role-specific skill associations
    """
    __tablename__ = "client_skill_catalogs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    skill_name = Column(String(255), nullable=False)
    skill_name_normalized = Column(String(255), nullable=False, index=True)
    skill_type = Column(String(50), default="technical")
    
    frequency = Column(Integer, default=1)
    
    associated_titles = Column(ARRAY(String), default=list)
    associated_departments = Column(ARRAY(String), default=list)
    associated_seniorities = Column(ARRAY(String), default=list)
    
    typical_level = Column(String(50), nullable=True)
    
    source_jds = Column(ARRAY(String), default=list)
    
    success_rate = Column(Float, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_client_skill_lookup', 'company_id', 'skill_name_normalized'),
        Index('idx_client_skill_type', 'company_id', 'skill_type', 'is_active'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "skill_name": self.skill_name,
            "skill_type": self.skill_type,
            "frequency": self.frequency,
            "associated_titles": self.associated_titles or [],
            "associated_departments": self.associated_departments or [],
            "typical_level": self.typical_level,
            "success_rate": self.success_rate,
        }
