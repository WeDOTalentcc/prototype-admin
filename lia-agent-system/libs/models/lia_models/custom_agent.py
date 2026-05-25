import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from lia_config.database import Base


class CustomAgentStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class MarketplaceListingStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNPUBLISHED = "unpublished"


class CustomAgent(Base):
    __tablename__ = "custom_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(64), nullable=False, index=True)
    created_by = Column(String(64), nullable=False)

    name = Column(String(256), nullable=False)
    role = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=False)
    allowed_tools = Column(ARRAY(String), nullable=False, default=list)
    domain = Column(String(64), nullable=False, default="general")
    icon = Column(String(10), nullable=True, default="🤖")

    status = Column(String(20), nullable=False, default=CustomAgentStatus.DRAFT.value)
    version = Column(Integer, nullable=False, default=1)

    config = Column(JSONB, nullable=False, default=dict)
    max_steps = Column(Integer, nullable=False, default=8)
    temperature = Column(Float, nullable=False, default=0.7)
    model_override = Column(String(64), nullable=True)

    # GAP 8: New fields for Agent Studio parity
    enable_memory = Column(Boolean, nullable=False, default=True, server_default="true")
    context_level = Column(String(20), nullable=False, default="full", server_default="full")
    excluded_tools = Column(ARRAY(String), nullable=False, default=list, server_default="{}")

    # Sprint 3.7 W4-1: per-agent voice flag — semântica PSTN only desde W-Channels-A (2026-05-23).
    # Voice (PSTN) = ligação telefônica Twilio outbound. Default OFF; cliente controla via UI.
    voice_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    # W-Channels-A (2026-05-23): per-agent VoIP flag — voz no navegador (Twilio VoIP SDK + Gemini Live).
    # Independente de voice_enabled. Default OFF; cliente controla via UI.
    voip_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    # T5a UX Transformação 5: per-agent WhatsApp flag (default OFF; client controls via Settings UI)
    whatsapp_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    # Workstream A 2026-05-23: per-agent triagem_invite CAPABILITY (default OFF).
    # Diferente dos canais diretos (voice/voip/whatsapp), triagem_invite habilita
    # o agente a CRIAR convites de triagem (token único + URL pública /triagem/{token})
    # entregues ao candidato via email/WhatsApp. Cliente controla via UI.
    triagem_invite_enabled = Column(Boolean, nullable=False, default=False, server_default="false")

    # Sub-sprint 7A (2026-05-25): canonical categorization + sourcing-only payloads.
    # category virou source-of-truth pra screening|sourcing|communication|analytics|automation|job_management.
    # Sprint 8 (migration 204) tornara category NOT NULL.
    category = Column(String(32), nullable=True)
    runtime_metrics = Column(JSONB, nullable=False, default=dict, server_default="{}")
    search_strategy = Column(JSONB, nullable=True)   # sourcing-only payload
    preferences = Column(JSONB, nullable=True)       # sourcing-only payload
    outreach_config = Column(JSONB, nullable=True)   # sourcing-only payload
    legacy_sourcing_agent_id = Column(UUID(as_uuid=True), nullable=True)  # back-reference (drop Sprint 8)


    total_executions = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    last_executed_at = Column(DateTime, nullable=True)

    is_marketplace_published = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    marketplace_listing = relationship(
        "AgentMarketplaceListing",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan",
    )
    installations = relationship(
        "AgentInstallation",
        back_populates="source_agent",
        foreign_keys="AgentInstallation.source_agent_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_custom_agents_company", "company_id"),
        Index("idx_custom_agents_status", "status"),
        Index("idx_custom_agents_domain", "domain"),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<CustomAgent id={self.id} name='{self.name}' company={self.company_id} status={self.status}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "created_by": self.created_by,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "allowed_tools": self.allowed_tools or [],
            "domain": self.domain,
            "icon": self.icon,
            "status": self.status,
            "version": self.version,
            "config": self.config or {},
            "max_steps": self.max_steps,
            "temperature": self.temperature,
            "model_override": self.model_override,
            "enable_memory": self.enable_memory if self.enable_memory is not None else True,
            "context_level": self.context_level or "full",
            "excluded_tools": self.excluded_tools or [],
            "voice_enabled": bool(self.voice_enabled) if self.voice_enabled is not None else False,
            "voip_enabled": bool(self.voip_enabled) if getattr(self, "voip_enabled", None) is not None else False,
            "whatsapp_enabled": bool(self.whatsapp_enabled) if self.whatsapp_enabled is not None else False,
            "triagem_invite_enabled": bool(self.triagem_invite_enabled) if getattr(self, "triagem_invite_enabled", None) is not None else False,
            "total_executions": self.total_executions,
            "avg_confidence": self.avg_confidence,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "is_marketplace_published": self.is_marketplace_published,
            "category": self.category,
            "runtime_metrics": self.runtime_metrics or {},
            "search_strategy": self.search_strategy,
            "preferences": self.preferences,
            "outreach_config": self.outreach_config,
            "legacy_sourcing_agent_id": str(self.legacy_sourcing_agent_id) if self.legacy_sourcing_agent_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentMarketplaceListing(Base):
    __tablename__ = "agent_marketplace_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    publisher_company_id = Column(String(64), nullable=False, index=True)

    title = Column(String(256), nullable=False)
    short_description = Column(String(512), nullable=True)
    long_description = Column(Text, nullable=True)
    category = Column(String(64), nullable=False, default="general")
    tags = Column(ARRAY(String), nullable=False, default=list)
    icon_url = Column(String(512), nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default=MarketplaceListingStatus.PENDING_REVIEW.value,
    )
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    credits_per_execution = Column(Integer, nullable=False, default=1)
    is_free = Column(Boolean, default=False)

    install_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)

    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("CustomAgent", back_populates="marketplace_listing")

    __table_args__ = (
        Index("idx_marketplace_status", "status"),
        Index("idx_marketplace_category", "category"),
        Index("idx_marketplace_publisher", "publisher_company_id"),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<MarketplaceListing id={self.id} title='{self.title}' status={self.status}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "publisher_company_id": self.publisher_company_id,
            "title": self.title,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "category": self.category,
            "tags": self.tags or [],
            "icon_url": self.icon_url,
            "status": self.status,
            "review_notes": self.review_notes,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "credits_per_execution": self.credits_per_execution,
            "is_free": self.is_free,
            "install_count": self.install_count,
            "avg_rating": self.avg_rating,
            "total_ratings": self.total_ratings,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentInstallation(Base):
    __tablename__ = "agent_installations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_marketplace_listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    installer_company_id = Column(String(64), nullable=False, index=True)
    installed_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("custom_agents.id", ondelete="SET NULL"),
        nullable=True,
    )

    installed_by = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    version_at_install = Column(Integer, nullable=False, default=1)

    total_executions = Column(Integer, default=0)
    total_credits_consumed = Column(Integer, default=0)

    installed_at = Column(DateTime, default=datetime.utcnow)
    uninstalled_at = Column(DateTime, nullable=True)

    source_agent = relationship(
        "CustomAgent",
        back_populates="installations",
        foreign_keys=[source_agent_id],
    )

    __table_args__ = (
        Index("idx_installation_company", "installer_company_id"),
        Index("idx_installation_source", "source_agent_id"),
        Index("idx_installation_status", "status"),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<AgentInstallation id={self.id} company={self.installer_company_id} agent={self.source_agent_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "source_agent_id": str(self.source_agent_id),
            "listing_id": str(self.listing_id) if self.listing_id else None,
            "installer_company_id": self.installer_company_id,
            "installed_agent_id": str(self.installed_agent_id) if self.installed_agent_id else None,
            "installed_by": self.installed_by,
            "status": self.status,
            "version_at_install": self.version_at_install,
            "total_executions": self.total_executions,
            "total_credits_consumed": self.total_credits_consumed,
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "uninstalled_at": self.uninstalled_at.isoformat() if self.uninstalled_at else None,
        }
