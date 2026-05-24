"""
ATS Integration models for Gupy and Pandapé synchronization.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from lia_config.database import Base


class ATSProvider(enum.Enum):
    """Supported ATS platforms"""
    GUPY = "gupy"
    PANDAPE = "pandape"
    MERGE = "merge"
    OTHER = "other"


class SyncStatus(enum.Enum):
    """Synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ATSConnection(Base):
    """
    ATS platform connections and credentials.
    Each company can have multiple ATS connections.
    """
    __tablename__ = "ats_connections"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ATS Platform
    provider = Column(SQLEnum(ATSProvider), nullable=False, index=True)
    provider_name = Column(String(100), nullable=False)  # "Gupy", "Pandapé"
    
    # Connection details
    api_key = Column(String(500), nullable=True)  # Encrypted API key
    api_secret = Column(String(500), nullable=True)  # Encrypted secret
    api_endpoint = Column(String(500), nullable=True)  # Custom endpoint if needed
    webhook_secret = Column(String(500), nullable=True)  # Webhook signature verification
    
    # Organization mapping
    # TENANT-EXEMPT: ATSConnection legacy pre-multi-tenancy; novas linhas sempre setam (RLS via app layer)
    company_id = Column(String(255), nullable=True)  # Internal company ID
    ats_company_id = Column(String(255), nullable=True)  # Company ID in ATS platform
    ats_company_name = Column(String(255), nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    auto_sync_enabled = Column(Boolean, default=True)
    sync_frequency_hours = Column(Integer, default=24)  # How often to sync
    sync_candidates = Column(Boolean, default=True)
    sync_jobs = Column(Boolean, default=True)
    sync_applications = Column(Boolean, default=True)
    
    # Field mappings
    field_mappings = Column(JSON, default=[])  # [{sourceField, targetField, confidence}]
    
    # Webhook configuration
    webhook_url = Column(String(1000), nullable=True)  # Our webhook endpoint
    webhook_events = Column(JSON, default=[])  # ["candidate.hired", "application.created"]
    webhook_id = Column(String(255), nullable=True)  # Webhook ID in ATS platform
    
    # Status
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(SQLEnum(SyncStatus), nullable=True)
    last_sync_error = Column(Text, nullable=True)
    total_syncs = Column(Integer, default=0)
    total_sync_errors = Column(Integer, default=0)
    
    # Statistics
    total_candidates_synced = Column(Integer, default=0)
    total_jobs_synced = Column(Integer, default=0)
    total_applications_synced = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(String(255), nullable=False, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ATSConnection {self.provider.value} - {self.provider_name}>"


class ATSSyncJob(Base):
    """
    Track synchronization jobs between LIA and ATS platforms.
    """
    __tablename__ = "ats_sync_jobs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Connection reference
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(SQLEnum(ATSProvider), nullable=False, index=True)
    
    # Job details
    sync_type = Column(String(50), nullable=False)  # candidates, jobs, applications, full
    sync_direction = Column(String(50), default="import")  # import, export, bidirectional
    
    # Status
    status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results
    total_records = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default={})
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Sync details
    filters_applied = Column(JSON, default={})  # {"date_from": "2025-01-01", "status": "active"}
    sync_metadata = Column(JSON, default={})  # Platform-specific metadata
    
    # Audit
    triggered_by = Column(String(255), default="system")  # user_id or "system" or "webhook"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ATSSyncJob {self.id} - {self.provider.value} ({self.status.value})>"


class ATSCandidate(Base):
    """
    Candidates imported from ATS platforms.
    Maps ATS candidate data to LIA internal candidate records.
    """
    __tablename__ = "ats_candidates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ATS reference
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(SQLEnum(ATSProvider), nullable=False, index=True)
    ats_candidate_id = Column(String(255), nullable=False, index=True)  # ID in ATS platform
    
    # Internal mapping
    lia_candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Link to candidates table
    
    # Candidate data (from ATS)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    
    # Professional info
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Application context
    applied_job_id = Column(String(255), nullable=True)  # ATS job ID
    applied_job_title = Column(String(255), nullable=True)
    application_date = Column(DateTime, nullable=True)
    application_status = Column(String(100), nullable=True)  # hired, rejected, in_process
    current_stage = Column(String(100), nullable=True)  # triagem, entrevista, final
    
    # ATS-specific data
    ats_score = Column(Float, nullable=True)  # Candidate score in ATS platform
    ats_tags = Column(JSON, default=[])  # Tags from ATS
    ats_raw_data = Column(JSON, default={})  # Full ATS payload for reference
    
    # Sync metadata
    first_synced_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    sync_version = Column(Integer, default=1)  # Increments with each update
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ATSCandidate {self.name} from {self.provider.value}>"


class ATSWebhookLog(Base):
    """
    Log all webhook events received from ATS platforms.
    """
    __tablename__ = "ats_webhook_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source
    connection_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    provider = Column(SQLEnum(ATSProvider), nullable=False, index=True)
    
    # Webhook details
    event_type = Column(String(100), nullable=False, index=True)  # "candidate.hired", "application.created"
    event_id = Column(String(255), nullable=True)  # Event ID from ATS
    
    # Payload
    payload = Column(JSON, nullable=False)  # Full webhook payload
    headers = Column(JSON, default={})  # HTTP headers
    
    # Processing
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Verification
    signature_valid = Column(Boolean, nullable=True)
    signature = Column(String(500), nullable=True)
    
    # Metadata
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<ATSWebhookLog {self.event_type} from {self.provider.value}>"


class ATSJobMapping(Base):
    """
    Map ATS job postings to LIA internal job vacancies.
    """
    __tablename__ = "ats_job_mappings"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ATS reference
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(SQLEnum(ATSProvider), nullable=False)
    ats_job_id = Column(String(255), nullable=False, index=True)
    
    # Internal mapping
    lia_job_vacancy_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Job data
    job_title = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    employment_type = Column(String(100), nullable=True)  # full_time, part_time, contract
    
    # Status
    ats_status = Column(String(50), nullable=True)  # open, closed, draft
    is_active = Column(Boolean, default=True)
    
    # Sync
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    ats_raw_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ATSJobMapping {self.job_title} from {self.provider.value}>"
