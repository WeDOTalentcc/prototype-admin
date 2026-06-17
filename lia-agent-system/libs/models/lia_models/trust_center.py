"""
Trust Center models for public-facing security and compliance portal.

This module provides models for:
- TrustCenterSettings: Configuration for company's public trust center
- Subprocessor: Data subprocessors (cloud providers, third parties)
- TrustCenterResource: Downloadable policies and documents
- TrustCenterUpdate: Compliance news and updates
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from lia_config.database import Base
import enum
import uuid


class SubprocessorCategory(str, enum.Enum):
    """Categories of data subprocessors."""
    CLOUD_HOSTING = "cloud_hosting"
    CRM = "crm"
    ANALYTICS = "analytics"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    SECURITY = "security"
    STORAGE = "storage"
    AI_ML = "ai_ml"
    OTHER = "other"


class ResourceCategory(str, enum.Enum):
    """Categories of trust center resources."""
    POLICY = "policy"
    REPORT = "report"
    CERTIFICATE = "certificate"
    WHITEPAPER = "whitepaper"
    OTHER = "other"


class UpdateCategory(str, enum.Enum):
    """Categories of trust center updates."""
    GENERAL = "general"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    CERTIFICATION = "certification"
    POLICY = "policy"


class TrustCenterSettings(Base):
    """
    Configuration for a company's public Trust Center portal.
    
    Controls appearance, visibility, and content settings for the 
    public-facing security and compliance portal.
    """
    __tablename__ = "trust_center_settings"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    company_slug = Column(String(100), nullable=False, unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    company_description = Column(Text, nullable=True)
    
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(20), nullable=True, default="#6366F1")
    
    is_public = Column(Boolean, default=False)
    custom_domain = Column(String(255), nullable=True)
    
    show_certifications = Column(Boolean, default=True)
    show_controls = Column(Boolean, default=True)
    show_bias_audits = Column(Boolean, default=True)
    show_subprocessors = Column(Boolean, default=True)
    
    contact_email = Column(String(255), nullable=True)
    privacy_policy_url = Column(String(500), nullable=True)
    terms_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TrustCenterSettings {self.company_slug}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "company_slug": self.company_slug,
            "company_name": self.company_name,
            "company_description": self.company_description,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "is_public": self.is_public,
            "custom_domain": self.custom_domain,
            "show_certifications": self.show_certifications,
            "show_controls": self.show_controls,
            "show_bias_audits": self.show_bias_audits,
            "show_subprocessors": self.show_subprocessors,
            "contact_email": self.contact_email,
            "privacy_policy_url": self.privacy_policy_url,
            "terms_url": self.terms_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Subprocessor(Base):
    """
    Data subprocessors for LGPD/GDPR transparency.
    
    Tracks third-party providers that process data on behalf of the company,
    including cloud providers, analytics tools, payment processors, etc.
    """
    __tablename__ = "trust_center_subprocessors"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, default="other")
    description = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    data_processed = Column(Text, nullable=True)
    
    is_public = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Subprocessor {self.name}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "country": self.country,
            "data_processed": self.data_processed,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TrustCenterResource(Base):
    """
    Downloadable resources for the Trust Center.
    
    Includes policies, compliance reports, certificates, and other
    documents that can be shared publicly or with NDA.
    """
    __tablename__ = "trust_center_resources"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default="other")
    
    file_url = Column(String(500), nullable=False)
    
    is_public = Column(Boolean, default=True)
    requires_nda = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<TrustCenterResource {self.title}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "file_url": self.file_url,
            "is_public": self.is_public,
            "requires_nda": self.requires_nda,
            "download_count": self.download_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TrustCenterUpdate(Base):
    """
    Compliance news and updates for the Trust Center.
    
    Used to communicate security updates, new certifications,
    policy changes, and other compliance-related news.
    """
    __tablename__ = "trust_center_updates"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general")
    
    published_at = Column(DateTime, nullable=True)
    is_published = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<TrustCenterUpdate {self.title}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "is_published": self.is_published,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
