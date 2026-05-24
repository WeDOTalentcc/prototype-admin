"""
Integration Hub models for centralized integration management.
Extends ATS integration to support HRIS, Job Boards, Communication platforms.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from lia_config.database import Base


class IntegrationCategory(str, enum.Enum):
    ATS = "ats"
    HRIS = "hris"
    WORKFORCE_PLANNING = "workforce_planning"
    JOB_BOARD = "job_board"
    COMMUNICATION = "communication"
    ASSESSMENT = "assessment"
    BACKGROUND_CHECK = "background_check"


class IntegrationStatus(str, enum.Enum):
    NOT_CONNECTED = "not_connected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    NEEDS_REAUTH = "needs_reauth"


class IntegrationProvider(Base):
    """Available integration providers catalog."""
    __tablename__ = "integration_providers"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    supports_oauth = Column(Boolean, default=False)
    supports_api_key = Column(Boolean, default=False)
    supports_webhook = Column(Boolean, default=False)
    
    features = Column(ARRAY(String), default=[])
    
    setup_instructions = Column(Text, nullable=True)
    documentation_url = Column(String(500), nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class IntegrationConnection(Base):
    """Active integration connections for a company."""
    __tablename__ = "integration_connections"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("integration_providers.id"), nullable=False)
    
    status = Column(String(50), default="not_connected")
    
    auth_type = Column(String(50))
    # ── credentials at-rest encryption (P0.D — Wave 3 audit 2026-05-21, LGPD Art. 46) ──
    # canonical: credentials_encrypted (Fernet ciphertext of JSON-serialized dict).
    # legacy: credentials_legacy (was credentials JSON; kept nullable during dual-write
    #         backfill window; SET NULL post-migration 168 backfill, drop column once
    #         every row has credentials_encrypted populated).
    # NEVER access self.credentials_legacy directly — always go via repository
    # get_decrypted_credentials() to centralize fail-loud behavior.
    credentials_encrypted = Column("credentials_encrypted", Text, nullable=True)
    credentials_legacy = Column("credentials", JSON, nullable=True)
    
    sync_enabled = Column(Boolean, default=True)
    sync_direction = Column(String(50), default="bidirectional")
    sync_frequency = Column(String(50), default="realtime")
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    last_sync_error = Column(Text, nullable=True)
    
    field_mappings = Column(JSON, default={})
    
    health_score = Column(Float, default=100.0)
    error_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    provider = relationship("IntegrationProvider")


class IntegrationSyncLog(Base):
    """Log of integration sync operations."""
    __tablename__ = "integration_sync_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("integration_connections.id"), nullable=False)
    
    sync_type = Column(String(50), nullable=False)
    direction = Column(String(50))
    
    status = Column(String(50), nullable=False)
    
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default={})
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    sync_metadata = Column(JSON, default={})


class IntegrationWebhook(Base):
    """Webhook configurations for integrations."""
    __tablename__ = "integration_webhooks"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("integration_connections.id"), nullable=False)
    
    webhook_url = Column(String(500), nullable=False)
    webhook_secret = Column(String(255), nullable=True)
    
    events = Column(ARRAY(String), default=[])
    
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


DEFAULT_INTEGRATION_PROVIDERS = [
    {
        "name": "Gupy",
        "category": "ats",
        "slug": "gupy",
        "description": "Leading ATS platform in Brazil for recruitment and selection",
        "logo_url": "/logos/gupy.png",
        "supports_oauth": False,
        "supports_api_key": True,
        "supports_webhook": True,
        "features": ["sync_candidates", "sync_jobs", "sync_applications", "webhooks"],
        "is_premium": False
    },
    {
        "name": "Pandapé",
        "category": "ats",
        "slug": "pandape",
        "description": "ATS and recruitment management platform",
        "logo_url": "/logos/pandape.png",
        "supports_oauth": False,
        "supports_api_key": True,
        "supports_webhook": True,
        "features": ["sync_candidates", "sync_jobs", "sync_applications"],
        "is_premium": False
    },
    {
        "name": "Merge.dev",
        "category": "ats",
        "slug": "merge",
        "description": "Universal ATS API connector for 40+ HR systems",
        "logo_url": "/logos/merge.png",
        "supports_oauth": True,
        "supports_api_key": True,
        "supports_webhook": True,
        "features": ["sync_candidates", "sync_jobs", "unified_api", "multi_ats"],
        "is_premium": True
    },
    {
        "name": "LinkedIn Jobs",
        "category": "job_board",
        "slug": "linkedin_jobs",
        "description": "Post and manage jobs on LinkedIn",
        "logo_url": "/logos/linkedin.png",
        "supports_oauth": True,
        "supports_api_key": False,
        "supports_webhook": True,
        "features": ["post_jobs", "receive_applications", "job_analytics"],
        "is_premium": False
    },
    {
        "name": "Indeed",
        "category": "job_board",
        "slug": "indeed",
        "description": "World's largest job site integration",
        "logo_url": "/logos/indeed.png",
        "supports_oauth": False,
        "supports_api_key": True,
        "supports_webhook": True,
        "features": ["post_jobs", "sponsored_jobs", "receive_applications"],
        "is_premium": False
    },
    {
        "name": "Workday",
        "category": "hris",
        "slug": "workday",
        "description": "Enterprise HR and finance management",
        "logo_url": "/logos/workday.png",
        "supports_oauth": True,
        "supports_api_key": True,
        "supports_webhook": True,
        "features": ["sync_employees", "sync_org_structure", "sync_positions"],
        "is_premium": True
    },
    {
        "name": "Slack",
        "category": "communication",
        "slug": "slack",
        "description": "Team communication and notifications",
        "logo_url": "/logos/slack.png",
        "supports_oauth": True,
        "supports_api_key": False,
        "supports_webhook": True,
        "features": ["notifications", "alerts", "candidate_updates", "team_collaboration"],
        "is_premium": False
    },
    {
        "name": "Microsoft Teams",
        "category": "communication",
        "slug": "microsoft_teams",
        "description": "Microsoft Teams integration for notifications and collaboration",
        "logo_url": "/logos/teams.png",
        "supports_oauth": True,
        "supports_api_key": False,
        "supports_webhook": True,
        "features": ["notifications", "alerts", "candidate_updates", "scheduling"],
        "is_premium": False
    }
]
