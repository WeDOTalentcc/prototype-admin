"""
TenantLLMConfig — Per-tenant LLM provider configuration.

Allows each client to:
- Choose their primary LLM provider (Gemini, Claude, OpenAI)
- Add their own API keys
- Configure routing (different LLM per operation type)
- Set fallback order
- Add multiple providers
"""
import uuid
from datetime import datetime

from lia_config.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID


class TenantLLMConfig(Base):
    """Per-tenant LLM configuration."""

    __tablename__ = "tenant_llm_configs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, unique=True, index=True)

    # Primary provider
    primary_provider = Column(String(50), default="gemini")  # gemini, claude, openai
    fallback_order = Column(JSON, default=["gemini", "claude", "openai"])

    # Provider configs (API keys encrypted, models, etc.)
    # Structure: {"gemini": {"api_key": "enc:...", "model": "gemini-2.5-flash"}, ...}
    providers = Column(JSON, default={})

    # Routing by operation type
    # Structure: {"chat": "gemini", "embedding": "openai", "screening": "claude", "voice": "gemini"}
    routing = Column(JSON, default={})

    # Full config blob (for advanced settings)
    config = Column(JSON, default={})

    # W2-012 (2026-05-22): LGPD Art 33 per-tenant region pinning.
    # NULL = usa default global do provider (us-central1 Gemini, sem header constraint OpenAI/Claude).
    # Override per-tenant: "us-east-1", "sa-east-1", "southamerica-east1", etc.
    region = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True)

    # Sprint D (2026-06-13): override de tier por dominio
    # {"screening": {"tier": "heavy", "threshold": 0.70}}
    # NULL = usa DOMAIN_TIER_DEFAULTS da plataforma
    tier_policies = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
